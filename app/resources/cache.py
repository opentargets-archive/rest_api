__author__ = 'andreap'


from flask import current_app
from flask_restful import Resource




class ClearCache(Resource):
    ''' clear the aplication cache
    '''
    def get(self ):
        return current_app.cache.clear()
