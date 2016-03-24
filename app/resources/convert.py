from flask_restful import Resource
from flask import jsonify
import header, subprocess
from tasks import convert_ff
globpath = "/media/sf_shared/"
apipath =  "/media/sf_shared/API-CORE/app/"

class Convert(Resource):
    def get(self,name=None,typec=None):
        convert = convert_ff.delay(name,typec)
        while not convert.ready():
            time.sleep(1)
        return convert.get()