
from flask.ext.restful import reqparse
from flask_restful.inputs import boolean

__author__ = 'andreap'


def get_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('size', type=int, required=False, help="maximum amount of results to retrieve", default=10, )
    parser.add_argument('from', type=int, required=False, help="pagination start from", default = 0)
    parser.add_argument('format', type=str, required=False, help="return format, can be: 'json','xml','tab','csv", choices=['json','xml','tab', 'csv'])
    parser.add_argument('datastructure', type=str, required=False, help="Type of data structure to return. Can be: 'full','simple','ids', 'count' ",choices=['full','simple','ids', 'count'])
    parser.add_argument('fields', type=str, action='append', required=False, help="fields you want to retrieve")
    parser.add_argument('sa', type=boolean, required=False, help="enable search_after", default=False,)
    parser.add_argument('search_after', action='append', required=False, help="search_after query parameters", default=[],)

    # parser.add_argument('groupby', type=str, action='append', required=False, help="group returned elements by the indicated value")
    # parser.add_argument('auth_token', type=str, required=False, help="a valid auth token")

    return parser


class Paginable():
    '''
    Subclass this if you want to use just the default parameter specified here.
    If you want to add more parameters use the methods above directly
    '''
    parser = get_parser() #TODO: in theory parser inheritance should work but is not working, check used version of flask-restful: https://flask-restful.readthedocs.org/en/0.3.0/reqparse.html#parser-inheritance






