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
mime = magic.Magic(mime=True)


@task_prerun.connect
def celery_prerun(*args, **kwargs):
    with celery.app.app_context():
        print g


def transcode(name=None, type_file=None, id_file=None, user_id=None):
    """
    Method call tasks:
        - Step 1 : Download file
        - Step 2 : Separate file
        - Step 3 : Convert part of files
        - Step 4 : Merges all part of converted files
        - Step 5 : Upload converted file to ceph
        - Step 6 : Run url callback and set data like Success, Code, Error and Data
    :param      int  id_file:
    :param      str  name:       File to convert
    :param      str  type_file:  Type of file to convert
    :param      str  user_id:
    """
    data = {'Success': True, 'File': '', 'Code': 201, 'UserId': user_id}
    path = tmp_path + user_id + "/"

    #: STEP 1 : DOWNLOAD FILE
    task_download_file = download_file_ff.delay(path, name, user_id, conn)
    while not task_download_file.ready():
        time.sleep(1)
    #: STEP 2 : SEPARATE FILE
    task_separate = separate_ff.delay(path, name, type_file, data)
    while not task_separate.ready():
        time.sleep(1)
    files, txt_file, data = task_separate.get()
    if data['Code'] is not 201:
        callback(id_file, data, path)
        return False
    #: STEP 3 : CONVERT SEPARATED FILES
    tasks_convert = group(convert_ff.s(item_file, type_file, data) for item_file in files)
    result_task_convert = tasks_convert.apply_async()
    while not result_task_convert.ready():
        time.sleep(1)
    for item in result_task_convert.get():
        if item[1]['Code'] is not 201:
            callback(id_file, item[1], path)
            return False
    #: STEP 4 : CONCAT ALL CONVERTED FILES
    task_concat = concat_ff.delay(path, txt_file, data)
    while not task_concat.ready():
        time.sleep(1)
    transcoded_file, data = task_concat.get()
    if data['Code'] is not 201:
        callback(id_file, data, path)
        return False
    #: STEP 5 : UPLOAD CONVERTED FILE TO CEPH
    task_upload = upload_file_ff.delay(path, transcoded_file, user_id, conn, data)
    while not task_upload.ready():
        time.sleep(1)
    data = task_upload.get()
    if data['Code'] is not 201:
        callback(id_file, data, path)
        return False
    #: STEP 6 : RUN CALL_BACK URL WITH DATA
    print "Step 5 : RUN CALL_BACK URL WITH DATA"
    callback(id_file, data, path)
    return True


def callback(id_file=None, data=None, path=None):
    clean_ff.delay(path)
    requests.post("http://lb-web/converted/files/" + str(id_file) + "/updatestate", data)


@celery.task
def concat_ff(path=None, name=None, data=None):
    """
    Task concat file
    :param              data:
    :param      str     path:
    :param      str     name: File name contains all parts of converted files
    :return:    boolean status and name of concatenated file
    """
    with app.test_request_context():
        if name is None or name is False:
            return False

        try:
            subprocess.call([
                "ffmpeg -f concat -safe 0 -i " + path + name +
                " -c copy " + path + '.'.join(name.split('.')[:-1])],
                shell=True)
        except subprocess.CalledProcessError:
            data.update({'Code': 500, 'Message': 'Error concat file'})

        concat_file = '.'.join(name.split('.')[:-1])
        data.update({'File': concat_file})

        return concat_file, data


@celery.task
def convert_ff(name=None, type_file=None, data=None):
    """
    Task convert file in new type
    :param           data:
    :param      str  name:       File name to convert
    :param      str  type_file:  New type of file
    :return:    boolean status and name of converted file
    """
    with app.test_request_context():
        if (name is None or name is False) or (type_file is None or False):
            return False
        try:
            subprocess.call(['ffmpeg -i ' + name + ' ' + '.'.join(name.split('.')[:-1]) + '.' + type_file], shell=True)
        except subprocess.CalledProcessError:
            data.update({'Code': 500, 'Message': 'Error convert file'})

        return name, data


@celery.task
def separate_ff(path=None, file_name=None, type_file=None, data=None):
    """
    Task separate file in multi parts of files
    :param              data:
    :param      str     path:
    :param      str     type_file:  Extension file
    :param      str     file_name:  File to separate
    :return:    boolean status, list of files and name of text file contains all parts of files
    """
    with app.test_request_context():
        if file_name is False or file_name is None:
            return False

        #: Seperate file with ffmpeg
        try:
            subprocess.check_call([
                'ffmpeg -i ' + path + file_name +
                ' -acodec copy -f segment -segment_time 30 -vcodec copy -reset_timestamps 1 -ab 32k -map 0 -n ' +
                path +
                '.'.join(file_name.split('.')[:-1]) + '_%d.' + file_name.split(".")[-1]],
                shell=True)
        except subprocess.CalledProcessError:
            data.update({'Code': 500, 'Message': 'Error separate file'})

        #: Get files
        files = glob.glob(path + '.'.join(file_name.split('.')[:-1]) + '_*')

        #: Create files list all separated files
        file_txt = '.'.join(file_name.split('.')[:-1]) + '.' + type_file + ".txt"

        #: Sort list files
        files.sort(key=convert)

        #: Write list files in files list separated files
        with open(path + file_txt, "a") as my_file:
            for item in files:
                my_file.write('file \'' + '.'.join(item.split('.')[:-1]) + '.' + type_file + '\'\n')
        my_file.close()

        return files, file_txt, data


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
    #: Get object in ceph
    obj_tuple = connection.get_object(user_id, file_name)

    #: Get file path for save downloaded file
    file_path = path + file_name

    #: Check if path exist, if not create it
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
            os.chmod(os.path.dirname(file_path), 0755)
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    #: Write content cepg object in new file
    with open(file_path, 'w') as my_file:
        my_file.write(obj_tuple[1])

    #: Return new file path
    return file_path


@celery.task
def upload_file_ff(path=None, file_name=None, user_id=None, connection=None, data=None):
    """
    Task upload converted file
    :param                                    data:
    :param      str                           path:
    :param      swiftclient.client.Connection connection:
    :param      str                           file_name:
    :param      str                           user_id:
    :return:    boolean
    """
    #: Get file path for upload it to ceph
    file_path = path + file_name

    #: Open content file and upload it to container
    try:
        with open(file_path, 'r') as my_file:
            connection.put_object(user_id, file_name,
                                  contents=my_file.read(),
                                  content_type=mime.from_file(file_path))
    except:
        data.update({'Code': 500, 'Message': 'Could not upload file to ceph'})

    return data


@celery.task
def clean_ff(path=None):
    shutil.rmtree(path)
    return True
