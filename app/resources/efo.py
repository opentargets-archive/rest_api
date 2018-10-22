import json
from app.common.auth import is_authenticated
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse
from app.common.results import RawResult

from flask_restful import abort, Resource
from flask import current_app, request
import time


__author__ = 'andreap'



class EfoLabelFromCode(Resource):

    @is_authenticated
    @rate_limit
    def get(self, disease_id ):
        '''
        get EFO information from a code
        '''
        start_time = time.time()
        es = current_app.extensions['esquery']
        res = es.get_efo_info_from_code(disease_id)
        if res:
            data = res.toDict()['data']
            if data:
                return CTTVResponse.OK(RawResult(json.dumps(data[0])),
                                   took=time.time() - start_time)
        else:
            abort(404, message="EFO code %s cannot be found"%disease_id)

    @is_authenticated
    @rate_limit
    def post(self):

        start_time = time.time()
        args = request.get_json(force=True)

        diseases = args.pop('diseases',[])

        es = current_app.extensions['esquery']

        res = es.get_efo_info_from_code(efo_codes=diseases,
                              **args)
        return CTTVResponse.OK(res, format,
                               took=time.time() - start_time)



