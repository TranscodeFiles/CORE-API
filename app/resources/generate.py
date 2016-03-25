from flask_restful import Resource
from tasks import generate_ff

globpath = "/deploy/app/media/"
apipath = "/deploy/app/"


class Generate(Resource):
    def get(self, name=None):
        generate = generate_ff.delay(name)
        while not generate.ready():
            time.sleep(1)
        return generate.get()
