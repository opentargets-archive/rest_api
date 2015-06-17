from app.common.auth import is_authenticated, get_token_payload

__author__ = 'andreap'
from flask import current_app, request
from flask.ext import restful
from flask.ext.restful import abort
from flask_restful_swagger import swagger




class ProxyEnsembl(restful.Resource):

    @swagger.operation()
    @is_authenticated
    def get(self, url ):
        '''
        proxy for the ensembl rest api
        '''
        proxy = current_app.extensions['proxy']
        res = proxy.proxy('ensembl',url, get_token_payload())
        if res:
            return res
        else:
            abort(404, message="cannot proxy to: %s "%url)

    @swagger.operation(
        parameters=[
            {
              "name": "body",
              "description": "json data you want to pass in the body",
              "required": True,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "body",
            },
            ]

    )
    @is_authenticated
    def post(self, url ):
        '''
        proxy for the ensembl rest api
        '''
        proxy = current_app.extensions['proxy']
        res = proxy.proxy('ensembl',url, get_token_payload(), request.data)
        if res:
            return res
        else:
            abort(404, message="cannot proxy to: %s "%url)


class ProxyGXA(restful.Resource):

    @swagger.operation()
    @is_authenticated
    def get(self, url ):
        '''
        proxy for the gxa rest api
        '''
        proxy = current_app.extensions['proxy']
        res = proxy.proxy('gxa',url, get_token_payload())
        if res:
            return res
        else:
            abort(404, message="cannot proxy to: %s "%url)

class ProxyPDB(restful.Resource):

    @swagger.operation()
    @is_authenticated
    def get(self, url ):
        '''
        proxy for the pdbe rest api
        '''
        proxy = current_app.extensions['proxy']
        res = proxy.proxy('pdbe',url, get_token_payload())
        if res:
            return res
        else:
            abort(404, message="cannot proxy to: %s "%url)

class ProxyEPMC(restful.Resource):

    @swagger.operation()
    @is_authenticated
    def get(self, url ):
        '''
        proxy for the pdbe rest api
        '''
        proxy = current_app.extensions['proxy']
        res = proxy.proxy('epmc',url, get_token_payload())
        if res:
            return res
        else:
            abort(404, message="cannot proxy to: %s "%url)