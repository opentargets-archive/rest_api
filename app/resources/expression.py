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




class Expression(restful.Resource):

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get expression data for a gene
        Test with ENSG00000136997
        """
        start_time = time.time()
        parser = reqparse.RequestParser()
        parser.add_argument('gene', type=str, action='append', required=False, help="gene identifier")


        args = parser.parse_args()
        genes = args.pop('gene',[]) or []
        if not (genes ):
            abort(400, message='Please provide at least one gene')
        expression_data = self.get_expression(genes,params=args)
        return CTTVResponse.OK(expression_data, took=time.time() - start_time)

    @is_authenticated
    @rate_limit
    def post(self ):
        """
        Get expression data for a gene
        test with: {"gene":["ENSG00000136997"]},
        """
        def fix_empty_strings(l):
            new_l=[]
            if l:
                for i in l:
                    if i:
                        new_l.append(i)
            return new_l

        start_time = time.time()
        args = request.get_json()
        genes = fix_empty_strings(args.pop('gene',[]) or [])

        if not genes:
            abort(400, message='Please provide at least one gene')
        expression_data = self.get_expression(genes,params=args)
        return CTTVResponse.OK(expression_data, took=time.time() - start_time)

    def get_expression(self,
                     genes,
                     params ={}):

        es = current_app.extensions['esquery']
        res = es.get_expression(genes = genes,
                                        **params)
        # if not res:
        #     abort(404, message='Cannot find tissue expression data for  %s'%', '.join(genes))
        return res

