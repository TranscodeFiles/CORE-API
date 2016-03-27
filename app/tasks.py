import glob
import subprocess
from flask import jsonify, g
from celery.signals import task_prerun
from factory import create_celery_app

celery, app = create_celery_app()

globpath = "/deploy/app/media/"
apipath = "/deploy/app/"


@task_prerun.connect
def celery_prerun(*args, **kwargs):
    with celery.app.app_context():
        print g


@celery.task()
def concat_ff(name=None):
    with app.test_request_context():
        subprocess.call(["ffmpeg -f concat -i " + name + " -c copy " + ('.').join(name.split('.')[:-1])], shell=True)
        return jsonify(filename=('.').join(name.split('.')[:-1]), success='true')


@celery.task()
def convert_ff(name=None, typec=None):
    with app.test_request_context():
        ret = subprocess.call(['ffmpeg -i ' + globpath + name + ' ' + '.'.join(name.split('.')[:-1]) + '.' + typec],
                              shell=True)
        if ret != 0:
            if ret < 0:
                print "Killed by signal", -ret
                return jsonify(file=apipath + '.'.join(name.split('.')[:-1]) + '.' + typec, success=False)
            else:
                print "Command failed with return code", ret
                return jsonify(file=apipath + '.'.join(name.split('.')[:-1]) + '.' + typec, success=False)
        else:
            return jsonify(file=apipath + '.'.join(name.split('.')[:-1]) + '.' + typec, success=True)


@celery.task()
def extract_ff(name=None, output=None):
    with app.test_request_context():
        subprocess.call(['ffmpeg -i ' + globpath + name + ' -vn -ab 128 ' + output + '.mp3'], shell=True)
        return jsonify(file=apipath + output + '.mp3', success='true')


@celery.task()
def generate_ff(name=None):
    with app.test_request_context():
        tab = glob.glob(('.').join(name.split('.')[:-1]) + '_*.' + name.split(".")[-1])
        with open(name + ".txt", "a") as myfile:
            for item in tab:
                myfile.write('file \'' + apipath + item + '\'\n')
        myfile.close()
        return jsonify(file=apipath + name + ".txt", success='true')


@celery.task()
def separate_ff(name=None):
    with app.test_request_context():
        subprocess.call(['ffmpeg -i ' + globpath + name + ' -acodec copy -f segment -segment_time 30 -vcodec copy -reset_timestamps 1 -map 0 -an ' + '.'.join(name.split('.')[:-1]) + '_%d.' + name.split(".")[-1]], shell=True)
        tab = glob.glob('.'.join(name.split('.')[:-1]) + '_*')
        with open(name + ".txt", "a") as myfile:
            for item in tab:
                myfile.write('file \'' + apipath + item + '\'\n')
        myfile.close()
        return jsonify(files=tab, file=apipath + name + ".txt")
