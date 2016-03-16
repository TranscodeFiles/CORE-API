from flask import Flask
from flask import render_template
import subprocess
from os.path import basename
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

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
