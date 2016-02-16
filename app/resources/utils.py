from flask import current_app

from app.common.response_templates import CTTVResponse
from app.common.results import SimpleResult, RawResult

__author__ = 'andreap'

from flask.ext import restful
from flask.ext.restful import reqparse
from app.common.rate_limit import rate_limit


class Ping(restful.Resource):
    parser = reqparse.RequestParser()

    @rate_limit
    def get(self ):
        return CTTVResponse.OK(RawResult('pong'))

class Version(restful.Resource):
    parser = reqparse.RequestParser()

    @rate_limit
    def get(self ):
        return CTTVResponse.OK(RawResult(current_app.config['API_VERSION']))
