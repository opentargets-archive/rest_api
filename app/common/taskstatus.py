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
                    response = json.dumps({'state': task.state, 'message': task.result})
                else:
                    response= json.dumps({'state': task.state,'message': task.result})
        except Exception as ex:
            response = json.dumps({'state': 'FAILURE', 'message' : str(ex.message)})

        return response
