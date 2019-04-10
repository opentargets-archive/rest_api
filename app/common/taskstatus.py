from flask import current_app, Response, json
from flask_restful import reqparse, Resource

__author__ = 'cinzia'


class TaskStatus(Resource):

    @classmethod
    def taskstatus(self, task_id):
        celery_obj = current_app.extensions['celery']
        try:
            task = celery_obj.AsyncResult(task_id)
            if task.state == 'SUCCESS':
                #It is already JSON format
                response= task.info
            else:
                if task.state == 'FAILURE':
                    response = json.dumps({'status': task.result})
                else:
                    response= json.dumps({'status': task.state})
        except Exception as ex:
            response = json.dumps({'status': 'exception', 'message' : str(ex.message)})

        return response
