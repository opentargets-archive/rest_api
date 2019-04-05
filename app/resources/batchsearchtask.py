from flask import current_app, Response, json, request
from flask_restful import reqparse, Resource
from socket import error as SocketError
import errno

author__ = 'cinzia'


class BatchSearchTask(Resource):
    def post(self):
        try:
            args= request.get_json(force=True)
        except Exception:
            args = None

        # blueprints did not work. Rules issue.
        url_prefix = 'v' + str(current_app.config['API_VERSION']) + '/platform'
        uri = str(request.url_root)+url_prefix+'/private/enrichment/targets'

        celery_obj = current_app.extensions['celery']
        try:
            #self.remove_empty_params(args)
            async_result=celery_obj.send_task('request_worker.run',(uri,args))
            result = {'uuid': str(async_result.id)}
        except SocketError as e:
                socket_error = json.dumps({'error': e.message})
                return Response(response=socket_error,
                         status=503,
                         mimetype="application/json")

        except Exception as ex:
            result = json.dumps({'error': str(ex.message)+' not found'})
            return Response(response=result,
                        status=500,
                        mimetype="application/json")
        return current_app.response_class(json.dumps(result), mimetype="application/json")
