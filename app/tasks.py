import glob
import shutil
import subprocess
import errno
import requests
import time
import magic
import os

from utils import convert
from flask import g
from celery import group
from celery.signals import task_prerun
from factory import create_celery_app

celery, app, conn = create_celery_app()

tmp_path = "/deploy/app/media/"
api_path = "/deploy/app/"

data = {'Success': True, 'Data': '', 'Code': 201, 'UserId': 0}

mime = magic.Magic(mime=True)


@task_prerun.connect
def celery_prerun(*args, **kwargs):
    with celery.app.app_context():
        print g


def transcode(name=None, type_file=None, call_back=None, user_id=None):
    """
    Method call tasks:
        - Step 1 : Download file
        - Step 2 : Separate file
        - Step 3 : Convert part of files
        - Step 4 : Merges all part of converted files
        - Step 5 : Run url callback and set data like Success, Code, Error and Data
    :param      str  name:       File to convert
    :param      str  type_file:  Type of file to convert
    :param      str  call_back:  Url to run after all task has finished
    :param      int  user_id:
    """
    data.update({'UserId': user_id})
    path = tmp_path + str(user_id) + "/"
    #: Step 1 : Download file
    print "Step 1 : DOWNLOAD FILE"
    task_download_file = download_file_ff.delay(path, name, user_id, conn)
    while not task_download_file.ready():
        time.sleep(1)
    #: Step 2 : Separate file
    print "Step 2 : SEPARATE FILE"
    task_separate = separate_ff.delay(path, name, type_file)
    while not task_separate.ready():
        time.sleep(1)
    files, txt_file = task_separate.get()
    #: Step 3 : Convert separated files
    print "Step 3 : CONVERT SEPARATED FILES"
    tasks_convert = group(convert_ff.s(item_file, type_file) for item_file in files)
    result_task_convert = tasks_convert.apply_async()
    while not result_task_convert.ready():
        time.sleep(1)
    #: Step 4 : Concat all converted files
    print "Step 4 : CONCAT ALL CONVERTED FILES"
    task_concat = concat_ff.delay(path, txt_file)
    while not task_concat.ready():
        time.sleep(1)
    task_upload = upload_file_ff.delay(path, task_concat.get(), user_id, conn)
    while not task_upload.ready():
        time.sleep(1)
    clean_ff.delay(path)
    #: Step 5 : Run call_back url with data
    print "Step 5 : RUN CALL_BACK URL WITH DATA"
    requests.post("http://" + call_back, data)
    return True


@celery.task
def concat_ff(path=None, name=None):
    """
    Task concat file
    :param      str     path:
    :param      str     name: File name contains all parts of converted files
    :return:    boolean status and name of concatenated file
    """
    with app.test_request_context():
        if name is None or name is False:
            return False
        subprocess.call(["ffmpeg -f concat -safe 0 -i " + path + name + " -c copy " + path + '.'.join(
            name.split('.')[:-1])], shell=True)
        concat_file = '.'.join(name.split('.')[:-1])
        data.update({'Data': {'File': concat_file}})
        print "Concat files"
        print data
        print concat_file
        return concat_file


@celery.task
def convert_ff(name=None, type_file=None):
    """
    Task convert file in new type
    :param      str  name:       File name to convert
    :param      str  type_file:  New type of file
    :return:    boolean status and name of converted file
    """
    with app.test_request_context():
        if (name is None or name is False) or (type_file is None or False):
            return False
        subprocess.call(['ffmpeg -i ' + name + ' ' + '.'.join(name.split('.')[:-1]) + '.' + type_file], shell=True)
        return name


@celery.task
def separate_ff(path=None, file_name=None, type_file=None):
    """
    Task separate file in multi parts of files
    :param      str     path:
    :param      str     type_file:  Extension file
    :param      str     file_name:  File to separate
    :return:    boolean status, list of files and name of text file contains all parts of files
    """
    with app.test_request_context():
        if file_name is False or file_name is None:
            return False

        subprocess.call([
                            'ffmpeg -i ' + path + file_name + ' -acodec copy -f segment -segment_time 30 -vcodec copy -reset_timestamps 1 -ab 32k -map 0 -an ' + path + '.'.join(
                                file_name.split('.')[:-1]) + '_%d.' + file_name.split(".")[-1]], shell=True)

        files = glob.glob(path + '.'.join(file_name.split('.')[:-1]) + '_*')

        file_txt = '.'.join(file_name.split('.')[:-1]) + '.' + type_file + ".txt"

        files.sort(key=convert)

        with open(path + file_txt, "a") as my_file:
            for item in files:
                my_file.write('file \'' + '.'.join(item.split('.')[:-1]) + '.' + type_file + '\'\n')
        my_file.close()

        return files, file_txt


@celery.task
def download_file_ff(path=None, file_name=None, user_id=None, connection=None):
    """
    Task download file
    :param      str                           path:
    :param      swiftclient.client.Connection connection:
    :param      str                           file_name:
    :param      str                           user_id:
    :return:    str                           tmp_file_path:
    """
    obj_tuple = connection.get_object(str(user_id), file_name)
    file_path = path + file_name
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(file_path, 'w') as my_file:
        my_file.write(obj_tuple[1])
    return file_path


@celery.task
def upload_file_ff(path=None, file_name=None, user_id=None, connection=None):
    """
    Task upload converted file
    :param      str                           path:
    :param      swiftclient.client.Connection connection:
    :param      str                           file_name:
    :param      int                           user_id:
    :return:    boolean
    """
    file_path = path + file_name
    print("File path upload")
    print file_path
    with open(file_path, 'r') as my_file:
        connection.put_object(str(user_id), file_name,
                              contents=my_file.read(),
                              content_type=mime.from_file(file_path))
    return True


@celery.task
def clean_ff(path=None):
    shutil.rmtree(path)
    return True
