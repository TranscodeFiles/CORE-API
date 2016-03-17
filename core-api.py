""" core-api.py """

from flask import Flask, request, render_template, jsonify
import subprocess
from os.path import basename
import glob
app = Flask(__name__)
  
globpath = "/media/sf_shared/" 
apipath =  "/media/sf_shared/API-CORE/"
  
@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/extract/name=<name>&output=<output>')
def extract(name=None,output=None):
     subprocess.call(['ffmpeg -i '+globpath+name +' -vn -ab 128 '+ output+'.mp3'], shell=True)
     return jsonify(file=apipath+output+'.mp3'+'.'+typec,success = true)

@app.route('/convert/name=<name>&typec=<typec>')
def convert(name=None,typec=None):
	subprocess.call(['ffmpeg -i '+globpath+name+' '+('.').join(name.split('.')[:-1])+'.'+typec], shell=True)
	return jsonify(file=apipath+('.').join(name.split('.')[:-1])+'.'+typec,success = true)
	
@app.route('/separate/name=<name>')
def separate(name=None):
	subprocess.call(['ffmpeg -i '+globpath+name+' -acodec copy -f segment -segment_time 30 -vcodec copy -reset_timestamps 1 -map 0 -an '+('.').join(name.split('.')[:-1])+'_%d.'+name.split(".")[-1]], shell=True)
	tab = glob.glob(('.').join(name.split('.')[:-1])+'_*')	
	return 	jsonify(files = tab)
	
@app.route('/concat/name=<name>')
def concat(name=None):
	subprocess.call(["ffmpeg -f concat -i "+name+" -c copy "+('.').join(name.split('.')[:-1])], shell=True)
	return jsonify(filename=('.').join(name.split('.')[:-1]),success = 'true')

@app.route('/generate/name=<name>')
def generate(name=None):
	tab = glob.glob(('.').join(name.split('.')[:-1])+'_*.'+name.split(".")[-1])	
	with open(name+".txt", "a") as myfile:
		for item in tab:
			myfile.write('file \''+apipath+item+'\'\n')
	myfile.close()
	jsonify(file=apipath+name+".txt",success = 'true')
	
			
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')