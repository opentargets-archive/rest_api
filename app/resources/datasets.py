from flask.ext.restful.inputs import boolean
from flask.ext.restful.reqparse import Argument
from app.common import boilerplate


from flask import current_app, request
from flask.ext import restful
from flask.ext.restful import abort, fields, marshal,marshal_with
from flask.ext.restful import reqparse
from app.common.auth import is_authenticated
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse
import time

__author__ = 'gkos-bio'

class Datasets(restful.Resource):

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Given a dataset name and an ES query, returns all documents from this dataset
        """
        es = current_app.extensions['esquery']
        parser = boilerplate.get_parser()

        parser.add_argument('dataset', type=str, required=True, help="name of the dataset")
        parser.add_argument('query', type=str, required=True, help="query to retrieve data in ES format")

        args = parser.parse_args()

        dataset_name = args.get('dataset', '')
        print("get ", dataset_name)
        es_query = args.get('query', '')
        if not es_query:
            abort(404, message='No query specified in the request')
        res = es.get_documents_from_dataset(dataset_name, es_query)

        if not res:
            abort(404, message='Cannot find documents for dataset %s'%str(dataset_name))
        return CTTVResponse.OK(res)

    @is_authenticated
    @rate_limit
    def post(self):
        """
        Given a list of subjects id, returns related entities
        """
        es = current_app.extensions['esquery']
        parser = boilerplate.get_parser()

        parser.add_argument('dataset', type=str, required=True, help="name of the dataset")
        parser.add_argument('query', type=str, required=True, help="query to retrieve data in ES format")

        args = parser.parse_args()
        dataset_name = args.get('dataset', '')
        print("post ", dataset_name)
        es_query = args.get('query', '')
        if not es_query:
            abort(404, message='No query specified in the request')

        res = es.get_documents_from_dataset(dataset_name, es_query)

        if not res:
            abort(404, message='Cannot find relations for id %s'%str(subjects))
        return CTTVResponse.OK(res)



class DatasetList(restful.Resource):

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get a list of datasets stored in our back-end
        """
        es = current_app.extensions['esquery']
        res = es.get_dataset_list()
        if not res:
            abort(404, message='Cannot retrieve datasets')
        return CTTVResponse.OK(res)