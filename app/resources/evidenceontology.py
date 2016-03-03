import time

from app.common.auth import is_authenticated
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse

__author__ = 'andreap'
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort


class EcoLabelFromCode(restful.Resource):


    @is_authenticated
    @rate_limit
    def get(self, code ):
        '''
        get ECO information from a code
        '''
        start_time = time.time()
        es = current_app.extensions['esquery']
        res = es.get_label_for_eco_code(code)
        if not res:
            abort(404, message="ECO ID %s cannot be found"%code)
        return CTTVResponse.OK(res,
                               took=time.time() - start_time)