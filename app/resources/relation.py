from flask.ext.restful.inputs import boolean
from flask.ext.restful.reqparse import Argument
from app.common import boilerplate


from flask import current_app, request
from flask.ext import restful
from flask.ext.restful import abort, fields, marshal,marshal_with
from flask.ext.restful import reqparse
from app.common.auth import is_authenticated
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse
import time

__author__ = 'andreap'

class RelationTarget(restful.Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, action='append', required=True, help="List of IDs to retrieve")

    @is_authenticated
    @rate_limit
    def get(self, target_id):
        """
        Given a target id, return related targets
        """
        es = current_app.extensions['esquery']

        res = es.get_targets_related_to_target(target_id)
        if not res:
            abort(404, message='Cannot find relations for id %s'%str(target_id))
        return CTTVResponse.OK(res)
