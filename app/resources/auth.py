import time
from flask import current_app, request

from flask_restful import reqparse, Resource
from app.common.auth import TokenAuthentication
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse
from app.common.results import RawResult

__author__ = 'andreap'



class RequestToken(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('app_name', type=str, required=True, help="app name [appname] is required")
    parser.add_argument('secret', type=str, required=True, help="app secret [secret] is required")
    parser.add_argument('uid', type=str, required=False, help="user id [uid] ")
    parser.add_argument('password', type=str, required=False, help="password [password] ")
    parser.add_argument('expiry', type=int, required=False, help="seconds before the token expires")

    @rate_limit
    def get(self, ):
        start_time = time.time()
        args = self.parser.parse_args()
        if args['expiry'] is None:
            args['expiry']=600
        token_data = TokenAuthentication.get_auth_token('cttv_api', auth_data=args, expiry=args['expiry'])
        return CTTVResponse.OK(RawResult(token_data), took=time.time() - start_time)


class ValidateToken(Resource):
    @rate_limit
    def get(self, ):
        return TokenAuthentication.is_valid(request.headers.get('Auth-Token'))
