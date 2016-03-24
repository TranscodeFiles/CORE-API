from flask_restful import Resource
from flask import jsonify
import header, glob, subprocess
from tasks import generate_ff
globpath = "/media/sf_shared/"
apipath =  "/media/sf_shared/API-CORE/app/"

class Generate(Resource):
    def get(self,name=None):
        generate = generate_ff.delay(name)
        while not generate.ready():
            time.sleep(1)
        return generate.get()
