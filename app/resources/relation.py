from flask_restful import Resource, abort
from app.common import boilerplate


from flask import current_app

from app.common.response_templates import CTTVResponse
import time

__author__ = 'andreap'

class Relations(Resource):

    def get(self):
        """
        Given a list of subjects id, returns related entities
        """
        es = current_app.extensions['esquery']
        parser = boilerplate.get_parser()
        parser.add_argument('sort', type=str, required=False, action='append',
                            help="sort the results by this score type", default=['scores.overlap']
                            )
        parser.add_argument('subject', type=str, action='append', required=False, help="subjects to get relations for")
        parser.add_argument('object', type=str, action='append', required=False, help="objeects to get relations for")

        args = parser.parse_args()
        subjects = args.pop('subject', []) or []
        objects = args.pop('object', []) or []
        res = es.get_relations(subjects, objects, **args)
        if not res:
            abort(404, message='Cannot find relations for id %s'%str(subjects))
        return CTTVResponse.OK(res)

    def post(self):
        """
        Given a list of subjects id, returns related entities
        """
        es = current_app.extensions['esquery']

        parser = boilerplate.get_parser()
        parser.add_argument('subject', type=str, action='append', required=False, help="subjects to get relations for")
        parser.add_argument('object', type=str, action='append', required=False, help="objeects to get relations for")
        parser.add_argument('sort', type=str, required=False, action='append',
                            help="sort the results by this score type", default=['scores.overlap']
                            )

        args = parser.parse_args()
        subjects = args.pop('subject', []) or []
        objects = args.pop('object', []) or []
        res = es.get_relations(subjects, objects, **args)
        if not res:
            abort(404, message='Cannot find relations for id %s'%str(subjects))
        return CTTVResponse.OK(res)



class RelationTargetSingle(Resource):

    def get(self, target_id):
        """
        Given a target id, returns related targets
        """
        es = current_app.extensions['esquery']
        parser = boilerplate.get_parser()
        parser.add_argument('sort', type=str, required=False, action='append',
                            help="sort the results by this score type", default=['scores.overlap'])
        args = parser.parse_args()
        res = es.get_relations([target_id],[], **args)
        if not res:
            abort(404, message='Cannot find relations for id %s'%str(target_id))
        return CTTVResponse.OK(res)



class RelationDiseaseSingle(Resource):
    def get(self, disease_id):
        """
        Given a disease id, returns related targets?
        """
        es = current_app.extensions['esquery']
        parser = boilerplate.get_parser()
        parser.add_argument('sort', type=str, required=False, action='append',
                            help="sort the results by this score type", default=['scores.overlap'])
        args = parser.parse_args()

        res = es.get_relations([disease_id],[], **args)
        if not res:
            abort(404, message='Cannot find relations for id %s' % str(disease_id))
        return CTTVResponse.OK(res)