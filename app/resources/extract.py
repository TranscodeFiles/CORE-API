from flask_restful import Resource
from flask import jsonify
import header, subprocess
from tasks import extract_ff
globpath = "/media/sf_shared/"
apipath =  "/media/sf_shared/API-CORE/app/"

class Extract(Resource):
    def get(self,name=None,output=None):
        extract = extract_ff.delay(name, output)
        while not extract.ready():
            time.sleep(1)
        return extract.get()
