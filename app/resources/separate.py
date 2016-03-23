from flask_restful import Resource
from flask import jsonify
import glob, header, subprocess
globpath = "/media/sf_shared/"
apipath =  "/media/sf_shared/API-CORE/app/"

class Separate(Resource):
    def get(self,name=None):
        subprocess.call(['ffmpeg -i '+globpath+name+' -acodec copy -f segment -segment_time 30 -vcodec copy -reset_timestamps 1 -map 0 -an '+('.').join(name.split('.')[:-1])+'_%d.'+name.split(".")[-1]], shell=True)
        tab = glob.glob(('.').join(name.split('.')[:-1])+'_*')
        with open(name+".txt", "a") as myfile:
            for item in tab:
                myfile.write('file \''+apipath+item+'\'\n')
        myfile.close()
        return 	jsonify(files = tab,file=apipath+name+".txt")