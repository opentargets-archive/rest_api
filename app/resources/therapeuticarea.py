from app.common.response_templates import CTTVResponse
from flask import current_app

from flask_restful import reqparse, Resource, abort
import time

__author__ = 'cinzia'

# This endpoint returns all the therapeutic area.
# https://github.com/opentargets/platform/issues/603


class TherapeuticAreas(Resource):

    def get(self):
        '''
        get counts and statistics fro the availabkle data
        '''
        start_time = time.time()
        es = current_app.extensions['esquery']
        res = es.get_therapeutic_areas()

        if not res:
            abort(404, message='Cannot find the therapeutic ares')

        return CTTVResponse.OK(res,
                               took=time.time() - start_time)

