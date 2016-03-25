import time

from flask_restful import Resource
from tasks import separate_ff

globpath = "/deploy/app/media/"
apipath = "/deploy/app/"


class Separate(Resource):
    def get(self, name=None):
        separate = separate_ff.delay(name)
        while not separate.ready():
            time.sleep(1)
        return separate.get()
