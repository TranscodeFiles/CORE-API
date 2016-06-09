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
        - Step 1 : Separate file
        - Step 2 : Convert part of files
        - Step 3 : Merges all part of converted files
        - Step 4 : Remove separates files (transcoded and not)
        - Step 5 : Run url callback and set data like Success, Code, Error and Data
    :param      int  id_file:
    :param      str  name:       File to convert
    :param      str  type_file:  Type of file to convert
    :param      str  user_id:
    """
    data = {'Success': True, 'File': 'emtpy', 'Code': 201, 'Percentage': 0, 'UserId': user_id, 'Message': 'empty'}
    path = tmp_path + user_id + "/"

    #: STEP 1 : SEPARATE FILE
    task_separate = separate_ff.delay(path, name, data, conn, user_id)
    while not task_separate.ready():
        time.sleep(1)
    files, data = task_separate.get()
    if data['Code'] is not 201:
        callback(id_file, data, 0)
        return False
    callback(id_file, data, 40, "Slice file")

    #: STEP 2 : CONVERT SEPARATED FILES
    tasks_convert = group(convert_ff.s(path, item_file, type_file, data, conn, user_id) for item_file in files)
    result_task_convert = tasks_convert.apply_async()
    transcoded_files = []
    while not result_task_convert.ready():
        time.sleep(1)
    for item in result_task_convert.get():
        if item[1]['Code'] is not 201:
            callback(id_file, item[1], 0)
            return False
        transcoded_files.append(item[0])
    callback(id_file, data, 60, "Convert files")

    #: STEP 3 : CONCAT ALL CONVERTED FILES
    task_concat = concat_ff.delay(path, name, data, conn, user_id, files, type_file)
    while not task_concat.ready():
        time.sleep(1)
    transcoded_file, data = task_concat.get()
    if data['Code'] is not 201:
        callback(id_file, data, 0)
        return False
    callback(id_file, data, 80, "Concat files")

    #: STEP 4 : REMOVE SEPARATES FILES (Transcoded and not)
    task_clean_all = clean_all_ff.delay(files, transcoded_files, user_id, conn, data)
    while not task_clean_all.ready():
        time.sleep(1)
    data = task_clean_all.get()
    if data['Code'] is not 201:
        callback(id_file, data, 0)
        return False

    #: STEP 5 : RUN CALL_BACK URL WITH DATA
    print "Step 6 : RUN CALL_BACK URL WITH DATA"
    callback(id_file, data, 100, "Transcoded")
    return True


def callback(id_file=None, data=None, percentage=None, message=None):
    """
    Callback return result to web app
    :param id_file:
    :param data:
    :param percentage:
    :param message:
    :return:
    """
    if message is not None:
        data.update({'Message': message})

    data.update({'Percentage': percentage})
    requests.post("http://lb-web/app_dev.php/converted/files/" + str(id_file) + "/updatestate", data)


@celery.task
def concat_ff(path=None, name=None, data=None, p_conn=None, user_id=None, files=None, type_file=None):
    """
    Task concat file
    :param      str     type_file:
    :param      str     files:
    :param      str     user_id:
    :param              p_conn:
    :param              data:
    :param      str     path:
    :param      str     name: File name contains all parts of converted files
    :return:    name of concatenated file
    """
    with app.test_request_context():
        if name is None or name is False:
            return False

        # Download converted files
        for item_file in files:
            data = download_file(path, item_file, user_id, p_conn, data)
            if data['Code'] is not 201:
                return name, data

        # Generate file text with all converted name file into
        file_txt = '.'.join(name.split('.')[:-1]) + '.' + type_file + ".txt"

        file_path = path + file_txt
        #: Check if path exist, if not create it
        if not os.path.exists(os.path.dirname(file_path)):
            try:
                os.makedirs(os.path.dirname(file_path))
                os.chmod(os.path.dirname(file_path), 0755)
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        try:
            with open(file_path, "a") as my_file:
                for item_file in files:
                    my_file.write('file \'' + path + '.'.join(item_file.split('.')[:-1]) + '.' + type_file + '\'\n')
            my_file.close()
        except subprocess.CalledProcessError:
            return "", data.update({'Code': 500, 'Message': 'Error concat file'})

        # Run ffmpeg for concat transcode files to one file
        concat_file = '.'.join(name.split('.')[:-1]) + "." + type_file
        try:
            subprocess.check_call([
                "ffmpeg -f concat -safe 0 -i " + path + file_txt +
                " -c copy " + path + concat_file],
                shell=True)
        except subprocess.CalledProcessError:
            data.update({'Code': 500, 'Message': 'Error concat file'})
        data.update({'File': concat_file})

        # Upload converted file to ceph
        data = upload_file(path, concat_file, user_id, p_conn, data)

        # Remove files
        clean(path)

        return concat_file, data


@celery.task
def convert_ff(path=None, name=None, type_file=None, data=None, p_conn=None, user_id=None):
    """
    Task convert file in new type
    :param      str  path:
    :param           p_conn:
    :param           user_id:
    :param           data:
    :param      str  name:       File name to convert
    :param      str  type_file:  New type of file
    :return:    bname of converted file and data
    """
    with app.test_request_context():
        if (name is None or name is False) or (type_file is None or False) or p_conn is None or user_id is None:
            return False

        # Download file in ceph
        data = download_file(path, name, user_id, p_conn, data)
        if data['Code'] is not 201:
            return name, data

        # Run ffmpeg to convert file
        transcode_name_file = '.'.join(name.split('.')[:-1]) + '.' + type_file

        try:
            subprocess.check_call(['ffmpeg -i ' + path + name + ' ' + path + transcode_name_file],
                                  shell=True)
        except subprocess.CalledProcessError:
            return data.update({'Code': 500, 'Message': 'Error convert file'})

        # Upload converted file to ceph
        data = upload_file(path, transcode_name_file, user_id, p_conn, data)

        return transcode_name_file, data


@celery.task
def separate_ff(path=None, file_name=None, data=None, p_conn=None, user_id=None):
    """
    Task separate file in multi parts of files
    :param      str                             user_id:
    :param      swiftclient.client.Connection   p_conn:
    :param                                      data:
    :param      str                             path:
    :param      str                             file_name:  File to separate
    :return:    list of files and name and data
    """
    with app.test_request_context():
        if file_name is False or file_name is None or p_conn is None or user_id is None:
            return False

        # Download file in ceph
        data = download_file(path, file_name, user_id, p_conn, data)
        if data['Code'] is not 201:
            return "empty", data

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
            return "empty", data

        #: Get files
        glob_files = glob.glob(path + '.'.join(file_name.split('.')[:-1]) + '_*')

        #: Sort list files
        glob_files.sort(key=convert)

        files = [os.path.basename(x) for x in glob_files]

        # Upload separated files to ceph
        for item_file in files:
            data = upload_file(path, item_file, user_id, p_conn, data)
            if data['Code'] is not 201:
                return "empty", data

        # Remove files
        clean(path)

        return files, data


def download_file(path=None, file_name=None, user_id=None, connection=None, data=None):
    """
    Download file to ceph
    :param str  path:
    :param str  file_name:
    :param str  user_id:
    :param      connection:
    :param      data:
    :return: data
    """
    #: Get object in ceph
    try:
        obj_tuple = connection.get_object(user_id, file_name)
    except:
        return data.update({'Code': 500, 'Message': 'Could not download file to ceph'})

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

    return data


def upload_file(path=None, file_name=None, user_id=None, connection=None, data=None):
    """
    Upload converted file to ceph
    :param path:
    :param file_name:
    :param user_id:
    :param connection:
    :param data:
    :return: data
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
def clean_all_ff(files_transcode=None, files=None, user_id=None, p_conn=None, data=None):
    """
    Remove all part file to ceph
    :param      files_transcode:
    :param      files:
    :param str  user_id:
    :param      p_conn:
    :param      data:
    :return: data
    """
    try:
        for item_file in files_transcode:
            delete_file(item_file, user_id, p_conn, data)
    except:
        return data.update({'Code': 500, 'Message': 'Could not clean'})

    try:
        for item_file in files:
            delete_file(item_file, user_id, p_conn, data)
    except:
        return data.update({'Code': 500, 'Message': 'Could not clean'})

    return data


def clean(path=None):
    """
    Rove folder or file recursively
    :param path:
    :return: boolean
    """
    shutil.rmtree(path)
    return True


def delete_file(file_name=None, user_id=None, connection=None, data=None):
    """
    Delete file to ceph
    :param str                           file_name:
    :param str                           user_id:
    :param swiftclient.client.Connection connection:
    :param                               data:
    :return: data
    """
    #: Get object in ceph
    try:
        connection.delete_object(user_id, file_name)
    except:
        data.update({'Code': 500, 'Message': 'Could not upload file to ceph'})

    return data
