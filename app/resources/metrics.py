
from app.common.response_templates import CTTVResponse
from flask import current_app

from flask_restful import Resource
import time

__author__ = 'andreap'




class Metrics(Resource):
    def get(self):
        '''
        get counts and statistics fro the availabkle data
        '''
        start_time = time.time()
        es = current_app.extensions['esquery']
        res = es.get_metrics()
        return CTTVResponse.OK(res,
                               took=time.time() - start_time)

