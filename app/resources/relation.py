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

class Relations(restful.Resource):

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Given a list of subjects id, returns related entities
        """
        es = current_app.extensions['esquery']
        parser = boilerplate.get_parser()
        parser.add_argument('sort', type=str, required=False, action='append',
                            help="sort the results by this score type", default=['scores.overlap']
                            )
        parser.add_argument('subject', type=str, action='append', required=True, help="subjects to get relations for")
        args = parser.parse_args()
        subjects = args.pop('subject', []) or []

        res = es.get_relations(subjects, **args)
        if not res:
            abort(404, message='Cannot find relations for id %s'%str(subjects))
        return CTTVResponse.OK(res)

    @is_authenticated
    @rate_limit
    def post(self):
        """
        Given a list of subjects id, returns related entities
        """
        es = current_app.extensions['esquery']

        parser = boilerplate.get_parser()
        parser.add_argument('subject', type=str, action='append', required=False, help="subjects to get relations for")
        parser.add_argument('sort', type=str, required=False, action='append',
                            help="sort the results by this score type", default=['scores.overlap']
                            )

        args = parser.parse_args()
        subjects = args.pop('subject', []) or []
        res = es.get_relations(subjects, **args)
        if not res:
            abort(404, message='Cannot find relations for id %s'%str(subjects))
        return CTTVResponse.OK(res)



class RelationTargetSingle(restful.Resource):

    @is_authenticated
    @rate_limit
    def get(self, target_id):
        """
        Given a target id, returns related targets
        """
        es = current_app.extensions['esquery']
        res = es.get_relations([target_id])
        if not res:
            abort(404, message='Cannot find relations for id %s'%str(target_id))
        return CTTVResponse.OK(res)



class RelationDiseaseSingle(restful.Resource):
    @is_authenticated
    @rate_limit
    def get(self, disease_id):
        """
        Given a disease id, returns related targets?
        """
        es = current_app.extensions['esquery']
        parser = boilerplate.get_parser()
        parser.add_argument('sort', type=str, required=False, action='append',
                            help="sort the results by this score type", default=['scores.overlap'])
        args = parser.parse_args()

        res = es.get_relations([disease_id], **args)
        if not res:
            abort(404, message='Cannot find relations for id %s' % str(disease_id))
        return CTTVResponse.OK(res)