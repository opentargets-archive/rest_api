from app.common import boilerplate


from flask import current_app, request
from flask.ext import restful
from flask.ext.restful import abort, fields, marshal,marshal_with
from flask_restful_swagger import swagger
from flask.ext.restful import reqparse
from app.common.auth import is_authenticated
from app.common.response_templates import CTTVResponse, PaginatedResponse



__author__ = 'andreap'


@swagger.model
class ExpressionQuery:
  "An object to specify an getbyid query"
  resource_fields = {
      'id': fields.List(fields.String(attribute='gene identifier', ))
  }




class Expression(restful.Resource):

    _swagger_parameters = [
            {
              "name": "gene",
              "description": "a gene identifier",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },


          ]

    @swagger.operation(
        nickname='expression',
        produces = ["application/json", "text/xml", "text/csv"],

        parameters=_swagger_parameters,
        )
    @is_authenticated
    def get(self):
        """
        Get expression data for a gene
        Test with ENSG00000136997
        """
        parser = reqparse.RequestParser()
        parser.add_argument('gene', type=str, action='append', required=False, help="gene identifier")


        args = parser.parse_args()
        genes = args.pop('gene',[]) or []
        if not (genes ):
            abort(404, message='Please provide at least one gene')
        return self.get_expression(genes,params=args)

    @swagger.operation(
        nickname='expression',
        produces = ["application/json", "text/xml", "text/csv"],
        parameters=[
            {
              "name": "body",
              "description": "gene id(s) you want expression data for",
              "required": True,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "body",
              "type": "ExpressionQuery"
            },
            ]
        )

    @is_authenticated
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


        args = request.get_json()
        genes = fix_empty_strings(args.pop('gene',[]) or [])

        if not genes:
            abort(404, message='Please provide at least one gene')
        return self.get_expression(genes,params=args)

    def get_expression(self,
                     genes,
                     params ={}):

        es = current_app.extensions['esquery']
        res = es.get_expression(genes = genes,
                                        **params)
        if not res:
            abort(404, message='Cannot find tissue expression data for  %s'%', '.join(genes))
        return CTTVResponse.OK(res)

