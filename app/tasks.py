from celery import Celery
from flask import jsonify

app = Celery('tasks', backend='amqp', broker='amqp://')

globpath = "/media/sf_shared/"
apipath =  "/media/sf_shared/API-CORE/app/"

@app.task
def concat_ff(name=None):
    subprocess.call(["ffmpeg -f concat -i "+name+" -c copy "+('.').join(name.split('.')[:-1])], shell=True)
    return jsonify(filename=('.').join(name.split('.')[:-1]),success = 'true')

@app.task
def convert_ff(name=None,typec=None):
    ret = subprocess.call(['ffmpeg -i '+globpath+name+' '+('.').join(name.split('.')[:-1])+'.'+typec], shell=True)
    if ret != 0:
        if ret < 0:
            print "Killed by signal", -ret
            return jsonify(file=apipath+('.').join(name.split('.')[:-1])+'.'+typec,success = false)
        else:
            print "Command failed with return code", ret
            return jsonify(file=apipath+('.').join(name.split('.')[:-1])+'.'+typec,success = false)
    else:
         return jsonify(file=apipath+('.').join(name.split('.')[:-1])+'.'+typec,success =  'true')

@app.task
def extract_ff(name=None,output=None):
    subprocess.call(['ffmpeg -i '+globpath+name +' -vn -ab 128 '+ output+'.mp3'], shell=True)
    return jsonify(file=apipath+output+'.mp3',success =  'true')

@app.task
def generate_ff(name=None):
    tab = glob.glob(('.').join(name.split('.')[:-1])+'_*.'+name.split(".")[-1])
    with open(name+".txt", "a") as myfile:
        for item in tab:
            myfile.write('file \''+apipath+item+'\'\n')
    myfile.close()
    return jsonify(file=apipath+name+".txt",success = 'true')

@app.task
def separate_ff(name=None):
    subprocess.call(['ffmpeg -i '+globpath+name+' -acodec copy -f segment -segment_time 30 -vcodec copy -reset_timestamps 1 -map 0 -an '+('.').join(name.split('.')[:-1])+'_%d.'+name.split(".")[-1]], shell=True)
    tab = glob.glob(('.').join(name.split('.')[:-1])+'_*')
    with open(name+".txt", "a") as myfile:
        for item in tab:
            myfile.write('file \''+apipath+item+'\'\n')
    myfile.close()
    return 	jsonify(files = tab,file=apipath+name+".txt")
