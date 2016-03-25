from flask_restful import Resource
from tasks import extract_ff

globpath = "/deploy/app/media/"
apipath = "/deploy/app/"


class Extract(Resource):
    def get(self, name=None, output=None):
        extract = extract_ff.delay(name, output)
        while not extract.ready():
            time.sleep(1)
        return extract.get()
