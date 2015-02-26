
from flask.ext.restful import reqparse

__author__ = 'andreap'


def get_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('size', type=int, required=False, help="maximum amount of results to retrieve", default=10, )
    parser.add_argument('from', type=int, required=False, help="pagination start from", default = 0)
    parser.add_argument('format', type=str, required=False, help="return format, can be: 'json','xml','table'", choices=['json','xml','table'])
    parser.add_argument('datastructure', type=str, required=False, help="Type of data structure to return. Can be: 'full','simple','ids', 'count' ",choices=['full','simple','ids', 'count'])
    parser.add_argument('fields', type=str, action='append', required=False, help="fields you want to retrieve")
    # parser.add_argument('groupby', type=str, action='append', required=False, help="group returned elements by the indicated value")

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
          "description": "Format to get data back. Can be 'json', 'xml' or 'table' ",
          "required": False,
          "allowMultiple": False,
          "dataType": "string",
          "paramType": "query"
        },
    ]
    return _swagger_params


class Paginable():
    '''
    Subclass this if you want to use just the default parameter specified here.
    If you want to add more parameters use the methods above directly
    '''
    parser = get_parser() #TODO: in theory parser inheritance should work but is not working, check used version of flask-restful: https://flask-restful.readthedocs.org/en/0.3.0/reqparse.html#parser-inheritance
    _swagger_parameters = get_swagger_parameters()






