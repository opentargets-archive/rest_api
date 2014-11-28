
from flask.ext.restful import reqparse

__author__ = 'andreap'


def get_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('size', type=int, required=False, help="maximum amount of results to retrieve")
    parser.add_argument('from', type=int, required=False, help="pagination start from")
    parser.add_argument('format', type=str, required=False, help="return format")
    parser.add_argument('datastructure', type=str, required=False, help="Type of data structure to return")
    return parser

def get_swagger_parameters():
    _swagger_params = [
        {
          "name": "size",
          "description": "maximum amount of results to return. Defaults to 10, max is 1000",
          "required": False,
          "allowMultiple": False,
          "dataType": "integer",
          "paramType": "query"
        },
        {
          "name": "from",
          "description": "How many initial results should be skipped. Defaults to 0",
          "required": False,
          "allowMultiple": False,
          "dataType": "integer",
          "paramType": "query"
        },
        {
          "name": "format",
          "description": "Format to get data back. Can be 'json', 'xml' or 'csv' ",
          "required": False,
          "allowMultiple": False,
          "dataType": "string",
          "paramType": "query"
        },
        {
          "name": "datastructure",
          "description": "Type of data structure to return. Can be 'full', 'simple', 'ids', or 'count' ",
          "required": False,
          "allowMultiple": False,
          "dataType": "string",
          "paramType": "query"
        }
    ]
    return _swagger_params


class Paginable():
    '''
    Subclass this if you want to use just the default parameter specified here.
    If you want to add more parameters use the methods above directly
    '''
    parser = get_parser()
    _swagger_parameters = get_swagger_parameters()






