from flask import current_app, Response, json
from flask_restful import reqparse, Resource

__author__ = 'cinzia'


class TaskStatus(Resource):
    def get(self, uuid):
        response = self.taskstatus(uuid)
        return Response(response=response,
                        status=200,
                        mimetype="application/json")


    def taskstatus(self, task_id):
        celery_obj = current_app.extensions['celery']
        try:
            task = celery_obj.AsyncResult(task_id)
            if task.state == 'SUCCESS':
                #It is already JSON format
                response= task.info
            else:
                if task.state == 'FAILURE':
                    response = json.dump({'status': task.result})
                else:
                    response= json.dump({'status': task.state})
        except Exception as ex:
            response = json.dump({'status': 'exception', 'message' : str(ex.message)})

        return response
