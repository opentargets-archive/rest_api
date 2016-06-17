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

    @is_authenticated
    @rate_limit
    def get(self, target_id):
        """
        Given a target id, return related targets
        """
        es = current_app.extensions['esquery']
        parser = boilerplate.get_parser()
        parser.add_argument('sort', type=str, required=False, action='append',
                            help="sort the results by this score type", default=['scores.euclidean']
                            )
        parser.add_argument('search', type=str, required=False, help="filter the results by fulltext matching")
        args = parser.parse_args()

        res = es.get_relations([target_id], **args)
        if not res:
            abort(404, message='Cannot find relations for id %s'%str(target_id))
        return CTTVResponse.OK(res)

class RelationDisease(restful.Resource):

        @is_authenticated
        @rate_limit
        def get(self, disease_id):
            """
            Given a target id, return related targets
            """
            es = current_app.extensions['esquery']
            parser = boilerplate.get_parser()
            parser.add_argument('sort', type=str, required=False, action='append',
                                help="sort the results by this score type", default=['scores.euclidean'])
            parser.add_argument('search', type=str, required=False, help="filter the results by fulltext matching")
            args = parser.parse_args()

            res = es.get_relations([disease_id], **args)
            if not res:
                abort(404, message='Cannot find relations for id %s' % str(disease_id))
            return CTTVResponse.OK(res)
