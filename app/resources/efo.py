from app.common.auth import is_authenticated
from app.common.rate_limit import rate_limit

__author__ = 'andreap'
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort
from flask_restful_swagger import swagger




class EfoLabelFromCode(restful.Resource):

    @swagger.operation()
    @is_authenticated
    @rate_limit
    def get(self, code ):
        '''
        get EFO information from a code
        '''
        es = current_app.extensions['esquery']
        res = es.get_efo_info_from_code(code)
        if res:
            return res[0]
        else:
            abort(404, message="EFO code %s cannot be found"%code)
