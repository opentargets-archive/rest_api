import flask
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort,reqparse
from flask_restful_swagger import swagger
from app.common import boilerplate
from app.common.auth import is_authenticated
from app.common.boilerplate import Paginable
from app.common.response_templates import CTTVResponse, PaginatedResponse


__author__ = 'andreap'




class FreeTextSearch(restful.Resource, Paginable):
    parser =boilerplate.get_parser()
    parser.add_argument('q', type=str, required=True, help="Query cannot be blank!")
    parser.add_argument('filter', type=str, required=False,  action='append', help="filter by gene or efo")
    _swagger_params = [
            {
              "name": "q",
              "description": "a full text query",
              "required": True,
              "allowMultiple": False,
              "dataType": "string",
              "paramType": "query"
            },
            {"name": "filter",
              "description": "restrict the search to return just genes or efo. Available options are 'gene' and 'efo'",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            }]
    _swagger_params.extend(Paginable._swagger_parameters)



    @swagger.operation(
        nickname='search',
        responseClass=PaginatedResponse.__name__,

        parameters=_swagger_params,
        )
    @is_authenticated
    def get(self ):
        """
        Search for gene and disease
        Search with a parameter q = 'your query'
        """
        kwargs = self.parser.parse_args()
        searchphrase = kwargs.pop('q')
        filter = kwargs.pop('filter') or ['all']
        if len(searchphrase)>1:
            res = current_app.extensions['esquery'].free_text_search(searchphrase, doc_filter= filter, **kwargs)
            return CTTVResponse.OK(res)
        else:
            abort(404, message = "Query is too short")




class QuickSearch(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('q', type=str, required=True, help="Query cannot be blank!")
    parser.add_argument('size', type=int, required=False, help="number of genes or efo to be returned.")
    _swagger_params = [
            {
              "name": "q",
              "description": "a full text query",
              "required": True,
              "allowMultiple": False,
              "dataType": "string",
              "paramType": "query"
            },
            {"name": "size",
              "description": "number of genes or efo to be returned",
              "required": False,
              "allowMultiple": False,
              "dataType": "integer",
              "paramType": "query"
            }]



    @swagger.operation(
        nickname='quick search',
        # responseClass=PaginatedResponse.__name__,
        parameters=_swagger_params,
        )
    @is_authenticated
    def get(self ):
        """
        Suggest best terms for gene and disease
        Search with a parameter q = 'your query'
        """
        kwargs = self.parser.parse_args()
        searchphrase = kwargs.pop('q')
        size = kwargs.pop('size') or 5
        if size > 10:
            size = 10
        if len(searchphrase)>1:
            res = current_app.extensions['esquery'].quick_search(searchphrase, size = size,**kwargs)
            return CTTVResponse.OK(res)
        else:
            abort(404, message = "Query is too short")



class AutoComplete(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('q', type=str, required=True, help="Query cannot be blank!")
    parser.add_argument('size', type=int, required=False, help="number of genes or efo to be returned.")
    _swagger_params = [
            {
              "name": "q",
              "description": "a full text query",
              "required": True,
              "allowMultiple": False,
              "dataType": "string",
              "paramType": "query"
            },
            {"name": "size",
              "description": "number of genes or efo to be returned",
              "required": False,
              "allowMultiple": False,
              "dataType": "integer",
              "paramType": "query"
            },
            ]



    @swagger.operation(
        nickname='autocomplete',
        # responseClass=PaginatedResponse.__name__,
        parameters=_swagger_params,
        )
    @is_authenticated
    def get(self ):
        """
        Suggest best terms for gene and disease
        Search with a parameter q = 'your query'
        """
        kwargs = self.parser.parse_args()
        searchphrase = kwargs.pop('q')
        size = kwargs.pop('size') or 5
        if len(searchphrase)>1:
            res = current_app.extensions['esquery'].autocomplete(searchphrase, size = size,**kwargs)
            return CTTVResponse.OK(res)
        else:
            abort(404, message = "Query is too short")

