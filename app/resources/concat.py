from flask_restful import Resource
from flask import jsonify
import header, subprocess

class Concat(Resource):
    def get(self,name=None):
        subprocess.call(["ffmpeg -f concat -i "+name+" -c copy "+('.').join(name.split('.')[:-1])], shell=True)
        return jsonify(filename=('.').join(name.split('.')[:-1]),success = 'true')
