from flask_restful import Resource
from flask import jsonify
import header, subprocess
from tasks import concat_ff

class Concat(Resource):
    def get(self,name=None):
        concat = concat_ff.delay(name)
        while not concat.ready():
            time.sleep(1)
        return concat.get()
