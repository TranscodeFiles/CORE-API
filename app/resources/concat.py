from flask_restful import Resource
from tasks import concat_ff

globpath = "/deploy/app/media/"
apipath = "/deploy/app/"


class Concat(Resource):
    def get(self, name=None):
        concat = concat_ff.delay(name)
        while not concat.ready():
            time.sleep(1)
        return concat.get()
