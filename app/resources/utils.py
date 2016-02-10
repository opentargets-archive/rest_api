__author__ = 'andreap'

from flask.ext import restful
from flask.ext.restful import reqparse



class Ping(restful.Resource):
    parser = reqparse.RequestParser()

    def get(self ):
        return "pong"

class Version(restful.Resource):
    parser = reqparse.RequestParser()

    def get(self ):
        return "1.1"
