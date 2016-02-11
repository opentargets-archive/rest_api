from app.common.rate_limit import rate_limit

__author__ = 'andreap'

from flask.ext import restful
from flask import current_app





class ClearCache(restful.Resource):
    ''' clear the aplication cache
    '''
    @rate_limit
    def get(self ):
        return current_app.cache.clear()
