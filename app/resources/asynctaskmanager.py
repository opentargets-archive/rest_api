from flask import current_app, Response, json, request
from flask_restful import reqparse, Resource
from socket import error as SocketError
import errno
from celery.task.control import inspect


__author__ = 'cinzia'


class AsyncTaskManager(Resource):

    def post(self):

        args= request.get_json(force=True)
        if 'task_type' not in args:
            result = {'message':'task_type: Missing required parameter in the JSON body or the post body or the query string'}
            return Response(response=json.dumps(result),
                status=400,
                mimetype="application/json")

        celery_obj = current_app.extensions['celery']
        try:
            self.remove_empty_params(args)
            task_name = self.get_task_name(celery_obj,args['task_type'])
            if task_name is None:
                result = json.dumps({'error':'Task not available'})
                return Response(response=result,
                         status=404,
                         mimetype="application/json")
            else:
                async_result = celery_obj.tasks[task_name].apply_async(
                               kwargs={'args': args})
                result = {'uuid': str(async_result.id)}
        except SocketError as e:
                socket_error = json.dumps({'status': e.message})
                return Response(response=socket_error,
                         status=503,
                         mimetype="application/json")

        except Exception as ex:
            result = json.dumps({'error': str(ex.message)+' not found'})
            return Response(response=result,
                        status=500,
                        mimetype="application/json")
        return current_app.response_class(json.dumps(result), mimetype="application/json")

    def get_task_name(self,celery_app, task_type):
        task_type = "app.common.taskexecutor."+task_type
        task_name = None
        try:
            tasks_list = celery_app.control.inspect().registered_tasks()
            if tasks_list is None: return set()
            celery_registered_tasks = tasks_list.values()[0]
            task_name = task_type if task_type in celery_registered_tasks else None
        except Exception as e:
            current_app.logger.error("No tasks available: " + e.message)

        return task_name

    # Copied from EnrichmentTargets, the method needs to be moved somewhere else
    def remove_empty_params(self,args):
        for k,v in args.items():
            if isinstance(v, list):
                if len(v)>0:
                    drop = True
                    for i in v:
                        if i != '':
                            drop =False
                    if drop:
                        del args[k]