from flask_restful import Resource
from tasks import convert_ff
import time

globpath = "/deploy/app/media/"
apipath = "/deploy/app/"


class Convert(Resource):
    def get(self, name=None, typec=None):
        convert = convert_ff.delay(name, typec)
        while not convert.ready():
            time.sleep(1)
        return convert.get()
