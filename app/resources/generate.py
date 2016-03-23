from flask_restful import Resource
from flask import jsonify
import header, glob, subprocess
globpath = "/media/sf_shared/"
apipath =  "/media/sf_shared/API-CORE/app/"

class Generate(Resource):
    def get(self,name=None):
        tab = glob.glob(('.').join(name.split('.')[:-1])+'_*.'+name.split(".")[-1])
        with open(name+".txt", "a") as myfile:
            for item in tab:
                myfile.write('file \''+apipath+item+'\'\n')
        myfile.close()
        jsonify(file=apipath+name+".txt",success = 'true')