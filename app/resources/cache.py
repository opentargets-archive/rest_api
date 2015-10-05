__author__ = 'andreap'

from flask.ext import restful
from flask import current_app





class ClearCache(restful.Resource):
    ''' clear the aplication cache
    '''

    def get(self ):
        return current_app.cache.clear()
