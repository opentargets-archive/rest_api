import json
from app.common.auth import is_authenticated
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse
from app.common.results import RawResult
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort
import time

__author__ = 'andreap'



class EfoLabelFromCode(restful.Resource):

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
            return CTTVResponse.OK(RawResult(json.dumps(res[0])),
                                   took=time.time() - start_time)
        else:
            abort(404, message="EFO code %s cannot be found"%disease_id)
