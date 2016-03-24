from flask_restful import Resource
from flask import jsonify
import glob, header, subprocess
from tasks import separate_ff
globpath = "/media/sf_shared/"
apipath =  "/media/sf_shared/API-CORE/app/"

class Separate(Resource):
    def get(self,name=None):
        separate = separate_ff.delay(name)
        while not separate.ready():
            time.sleep(1)
        return separate.get()