import time
from flask import current_app, request
from flask.ext import restful
from flask.ext.restful import abort,reqparse
from flask_restful_swagger import swagger
from app.common import boilerplate
from app.common.boilerplate import Paginable
from app.common.auth import TokenAuthentication, is_authenticated
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse
from app.common.results import RawResult

__author__ = 'andreap'



class RequestToken(restful.Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('app_name', type=str, required=True, help="app name [appname] is required")
    parser.add_argument('secret', type=str, required=True, help="app secret [secret] is required")
    parser.add_argument('uid', type=str, required=False, help="user id [uid] ")
    parser.add_argument('password', type=str, required=False, help="password [password] ")
    parser.add_argument('expiry', type=int, required=False, help="seconds before the token expires")

    _swagger_parameters = [
                {
                  "name": "app_name",
                  "description": "the name of the app you are using to request a token. You need to register the app before you will be able to request a token",
                  "required": True,
                  "dataType": "string",
                  "paramType": "query"
                },
                {
                  "name": "secret",
                  "description": "the secret you were given when registering your app",
                  "required": True,
                  "dataType": "string",
                  "paramType": "query"

                },
                {
                  "name": "uid",
                  "description": "the id of the user that is using your app",
                  "required": False,
                  "dataType": "string",
                  "paramType": "query"

                },
                {
                  "name": "password",
                  "description": "the password of the user that is using your app",
                  "required": False,
                  "dataType": "string",
                  "paramType": "query"

                },
 {
                  "name": "expiry",
                  "description": "seconds before the token expires",
                  "required": False,
                  "dataType": "integer",
                  "paramType": "query"

                },

              ]

    @swagger.operation(
        nickname='association',
        produces = ["application/json"],
        parameters=_swagger_parameters,
        )
    @rate_limit
    def get(self, ):
        start_time = time.time()
        args = self.parser.parse_args()
        if args['expiry'] is None:
            args['expiry']=600
        token_data = TokenAuthentication.get_auth_token('cttv_api', auth_data=args, expiry=args['expiry'])
        return CTTVResponse.OK(RawResult(token_data), took=time.time() - start_time)


class ValidateToken(restful.Resource):
    @rate_limit
    def get(self, ):
        return TokenAuthentication.is_valid(request.headers.get('Auth-Token'))
