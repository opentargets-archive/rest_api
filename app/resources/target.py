from app.common import boilerplate

import json
from flask import request
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort
from app.common.auth import is_authenticated
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse
from app.common.results import RawResult


class TargetInfo(restful.Resource):
    @is_authenticated
    @rate_limit
    def get(self):
        """
        Given a list of target ids returns target generic information
        """
        es = current_app.extensions['esquery']
        parser = boilerplate.get_parser()
        parser.add_argument('id', type=str, required=False, action='append',
                            help="target ids to get the information"
                            )
        parser.add_argument('fields', type=str, required=False, action='append',
                            help="fields to include in the output"
                            )

        kwargs = parser.parse_args()
        target_ids = kwargs.pop('id', []) or []

        res = es.get_gene_info(target_ids, **kwargs)
        if res:
            return CTTVResponse.OK(res)

        abort(404, message="Gene id %s cannot be found" % target_ids)

    @is_authenticated
    @rate_limit
    def post(self):
        """
        Given a list of target ids returns target generic information
        """

        es = current_app.extensions['esquery']

        kwargs = request.get_json(force=True)
        print "kwargs"
        print kwargs
        target_ids = kwargs.pop('id', []) or []

        res = es.get_gene_info(target_ids, **kwargs)
        if res:
            return CTTVResponse.OK(res)

        abort(404, message="Gene id %s cannot be found" % target_ids)


class TargetInfoSingle(restful.Resource):
    @is_authenticated
    @rate_limit
    def get(self, target_id):
        """
        Returns general information of a target
        """
        es = current_app.extensions['esquery']
        res = es.get_gene_info([target_id])
        if res:
            data = res.toDict()['data']
            if data:
                return CTTVResponse.OK(RawResult(json.dumps(data[0])))

        abort(404, message="Gene id %s cannot be found" % target_id)


