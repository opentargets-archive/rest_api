

import time
import json

from flask import current_app, request
from flask_restful import abort, Resource

from app.common.response_templates import CTTVResponse
from app.common.results import RawResult

class Drug(Resource):
    def get(self, drug_id):
        start_time = time.time()
        es = current_app.extensions['esquery']
        res = es.get_drug_info_from_id(drug_id)
        if res:
            return CTTVResponse.OK(res,
                took=time.time() - start_time)
        else:
            abort(404, message="drug code %s cannot be found"%drug_id)