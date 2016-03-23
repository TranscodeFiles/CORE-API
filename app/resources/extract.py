from flask_restful import Resource
from flask import jsonify
import header, subprocess
globpath = "/media/sf_shared/"
apipath =  "/media/sf_shared/API-CORE/app/"

class Extract(Resource):
    def get(self,name=None,output=None):
        subprocess.call(['ffmpeg -i '+globpath+name +' -vn -ab 128 '+ output+'.mp3'], shell=True)
        return jsonify(file=apipath+output+'.mp3',success =  'true')