from flask_restful import Resource
from flask import jsonify
import header, subprocess
globpath = "/media/sf_shared/"
apipath =  "/media/sf_shared/API-CORE/app/"

class Convert(Resource):
    def get(self,name=None,typec=None):
        ret = subprocess.call(['ffmpeg -i '+globpath+name+' '+('.').join(name.split('.')[:-1])+'.'+typec], shell=True)
        if ret != 0:
            if ret < 0:
                print "Killed by signal", -ret
                return jsonify(file=apipath+('.').join(name.split('.')[:-1])+'.'+typec,success = false)
            else:
                print "Command failed with return code", ret
                return jsonify(file=apipath+('.').join(name.split('.')[:-1])+'.'+typec,success = false)
        else:
             return jsonify(file=apipath+('.').join(name.split('.')[:-1])+'.'+typec,success =  'true')