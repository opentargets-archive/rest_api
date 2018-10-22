from app.common.rate_limit import rate_limit

__author__ = 'andreap'


from flask import current_app
from flask_restful import Resource




class ClearCache(Resource):
    ''' clear the aplication cache
    '''

    @rate_limit
    def get(self ):
        return current_app.cache.clear()
