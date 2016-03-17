""" core-api.py """

from flask import Flask
from flask import render_template
import subprocess
from os.path import basename
import glob
from flask import jsonify
app = Flask(__name__)
  
@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/extract/name=<name>&output=<output>')
def extract(name=None,output=None):
     subprocess.call(['ffmpeg -i /media/sf_shared/'+name +' -vn -ab 128 '+ output+'.mp3'], shell=True)
     return '200'

@app.route('/convert/name=<name>&typec=<typec>')
def convert(name=None,typec=None):
	subprocess.call(['ffmpeg -i /media/sf_shared/'+name+' '+('.').join(name.split('.')[:-1])+'.'+typec], shell=True)
	return '200'
	
@app.route('/separate/name=<name>')
def separate(name=None):
	subprocess.call(['ffmpeg -i /media/sf_shared/'+name+' -acodec copy -f segment -segment_time 30 -vcodec copy -reset_timestamps 1 -map 0 -an '+('.').join(name.split('.')[:-1])+'_%d.'+name.split(".")[-1]], shell=True)
	tab = glob.glob(('.').join(name.split('.')[:-1])+'_*')	
	return 	jsonify(files = tab)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')