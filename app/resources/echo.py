__author__ = 'andreap'

from flask.ext import restful
from flask.ext.restful import reqparse
import random, time
from flask_restful_swagger import swagger




class Echo(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('echo', type=str, required=True, help="tell me something")
    parser.add_argument('random', type=bool, required=False, help="Random delay")

    @swagger.operation(
        notes='''debug utility''',
        nickname='echo',
        parameters=[
            {
              "name": "echo",
              "description": "I will echo this",
              "required": True,
              "allowMultiple": False,
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "random",
              "description": "insert a random delay in the response",
              "required": False,
              "allowMultiple": False,
              "dataType": "integer",
              "paramType": "query"
            },

          ],)
    def get(self, ):
        args = self.parser.parse_args()
        value = args['echo']
        if value:
            if args['random']:
                i = random.randint(0,50)
                if i == 0:
                    time.sleep(random.randint(3,9))
            return value
        return
