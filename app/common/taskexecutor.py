from flask import json, Response
from celery import current_app as current_celery
from flask import current_app, json


@current_celery.task()
def batch_search(args):
    es_dict = {}
    # Set up to 1000
    MAX_ELEMENT_SIZE = 1000
    if 'target' in args:
        if len(args['target']) > MAX_ELEMENT_SIZE:
            es_dict = {'message': 'maximum number of targets allowed is %i' % MAX_ELEMENT_SIZE}
            es_dict['status'] = 'ERROR'
        else:
            try:
                with current_app.app_context():
                    es = current_app.extensions['esquery']
                    es_result = es.get_enrichment_for_targets(targets=args['target'],
                                            pvalue_threshold=args['pvalue'],
                                            from_=args['from'],
                                            size=args['size'],
                                            async_task = True)
                    try:
                        es_dict = es_result.toDict()
                        es_dict['status'] = 'SUCCESS'
                    except TypeError as te:
                        es_dict['message'] = 'Cannot find diseases for targets %s'%str(args['target'])
                        es_dict['status'] = 'ERROR'
                    except Exception as ex:
                        es_dict['message'] = str(ex.message)
                        es_dict['status'] = 'ERROR'
            except Exception as ex:
                es_dict ['message'] = str(ex)
                es_dict['status'] = 'ERROR'

    resJSON = json.dumps(es_dict)
    return resJSON


@current_celery.task()
def ping(args):
    message = {'message': 'pong'}
    return json.dumps(message)