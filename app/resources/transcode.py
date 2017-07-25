import thread

from flask_restful import fields, marshal_with, reqparse, Resource
from tasks import transcode


class Transcode(Resource):
    """ Class manage transcoding """
    def get(self, name, type_file, id_file, user_id):
        """
        Run main task for transode file in async and return result "Task in progress"
        :param int  id_file:
        :param str  name:
        :param str  type_file:
        :param str  user_id:
        :return: response with Status 200 and its content
        """
        #: Run task transcode in async
        thread.start_new_thread(transcode, (name, type_file, id_file, user_id))

        return {'Status': 'Tasks in progress'}, 200
