import flask
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort
from flask_restful_swagger import swagger
from app.common import boilerplate
from app.common.responses import CTTVResponse


__author__ = 'andreap'




class FreeTextSearch(restful.Resource):
    parser = boilerplate.get_parser()
    parser.add_argument('q', type=str, required=True, help="Query cannot be blank!")
    _swagger_params = [
            {
              "name": "q",
              "description": "a full text query",
              "required": True,
              "allowMultiple": False,
              "dataType": "string",
              "paramType": "query"
            }]
    _swagger_params.extend(boilerplate.get_swagger_parameters())



    @swagger.operation(
        notes='''search with a parameter q = your query''',
        nickname='search',
        parameters=_swagger_params,
        )
    def get(self ):
        kwargs = self.parser.parse_args()
        searchphrase = kwargs.pop('q')
        if len(searchphrase)>2:
            res = current_app.extensions['esquery'].free_text_search(searchphrase,**kwargs)
            return CTTVResponse.OK(res)
        else:
            abort(404, message = "Query is too short")




