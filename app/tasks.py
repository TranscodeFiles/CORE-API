import glob
import subprocess
import requests
import time
from utils import convert

from flask import g
from celery import group
from celery.signals import task_prerun
from factory import create_celery_app

celery, app = create_celery_app()

glob_path = "/deploy/app/media/"
api_path = "/deploy/app/"

data = {'Success': True, 'Data': '', 'Code': 201}


@task_prerun.connect
def celery_prerun(*args, **kwargs):
    with celery.app.app_context():
        print g


def transcode(name=None, type_file=None, call_back=None):
    """
    Method call tasks:
        - Step 1 : Separate file
        - Step 2 : Convert part of files
        - Step 3 : Merges all part of converted files
        - Step 4 : Run url callback and set data like Success, Code, Error and Data
    :param      str  name:       File to convert
    :param      str  type_file:  Type of file to convert
    :param      str  call_back:  Url to run after all task has finished
    """
    #: Step 1 : Separate file
    print "Step 1 : SEPARATE FILE"
    task_separate = separate_ff.delay(name, type_file)
    while not task_separate.ready():
        time.sleep(1)
    files, txt_file = task_separate.get()
    #: Step 2 : Convert separated files
    print "Step 2 : Convert separated files"
    tasks_convert = group(convert_ff.s(item_file, type_file) for item_file in files)
    result_task_convert = tasks_convert.apply_async()
    while not result_task_convert.ready():
        time.sleep(1)
    #: Step 3 : Concat all converted files
    print "Step 3 : Concat all converted files"
    task_concat = concat_ff.delay(txt_file)
    while not task_concat.ready():
        time.sleep(1)
    #: Step 4 : Run call_back url with data
    print "Step 4 : Run call_back url with data"
    requests.post("http://" + call_back, data)
    return True


@celery.task
def concat_ff(name=None):
    """
    Task concat file
    :param      str  name: File name contains all parts of converted files
    :return:    boolean status and name of concatenated file
    """
    with app.test_request_context():
        if name is None or name is False:
            return False
        subprocess.call(["ffmpeg -f concat -safe 0 -i " + glob_path + name + " -c copy " + glob_path + '.'.join(
            name.split('.')[:-1])], shell=True)
        concat_file = '.'.join(name.split('.')[:-1])
        data.update({'Data': {'File': concat_file}})
        print "Concat files"
        print data
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
def separate_ff(file_name=None, type_file=None):
    """
    Task separate file in multi parts of files
    :param      str     type_file:  Extension file
    :param      str     file_name:  File to separate
    :return:    boolean status, list of files and name of text file contains all parts of files
    """
    with app.test_request_context():
        if file_name is False or file_name is None:
            return False
        subprocess.call(['ffmpeg -i ' + glob_path + file_name + ' -acodec copy -f segment -segment_time 30 -vcodec copy -reset_timestamps 1 -ab 32k -map 0 -an ' + glob_path + '.'.join(file_name.split('.')[:-1]) + '_%d.' + file_name.split(".")[-1]], shell=True)
        files = glob.glob(glob_path + '.'.join(file_name.split('.')[:-1]) + '_*')
        file_txt = '.'.join(file_name.split('.')[:-1]) + '.' + type_file + ".txt"
        files.sort(key=convert)
        with open(glob_path + file_txt, "a") as my_file:
            for item in files:
                my_file.write('file \'' + '.'.join(item.split('.')[:-1]) + '.' + type_file + '\'\n')
        my_file.close()
        return files, file_txt
