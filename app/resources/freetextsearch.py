import time

from flask import current_app
from flask import request
from flask.ext import restful
from flask.ext.restful import abort, reqparse

from app.common import boilerplate
from app.common.auth import is_authenticated
from app.common.boilerplate import Paginable
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse
from flask.ext.restful.inputs import boolean


__author__ = 'andreap'


class FreeTextSearch(restful.Resource, Paginable):
    parser = boilerplate.get_parser()
    parser.add_argument('q', type=str, required=True, help="Query cannot be blank")
    parser.add_argument('filter', type=str, required=False, action='append', help="filter by target or disease")
    parser.add_argument('highlight', type=boolean, required=False,
                        help="return where the query was matched, defaults to true")
    parser.add_argument('fields', type=str, action='append', required=False,
                        help="specify the fields to return for each object")
    parser.add_argument('search_entities', type=str, required=False, action="append",
                        help="specify the entity type to look for. Only {drug|all} at the momment")

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Search for gene and disease
        Search with a parameter q = 'your query'
        """
        start_time = time.time()

        kwargs = self.parser.parse_args()
        searchphrase = kwargs.pop('q')
        filter = kwargs.pop('filter') or ['all']

        if len(searchphrase) > 1:
            res = current_app.extensions['esquery'].free_text_search(searchphrase, doc_filter=filter, **kwargs)

            return CTTVResponse.OK(res,
                                   took=time.time() - start_time)
        else:
            abort(400, message="Query is too short")


class BestHitSearch(restful.Resource, Paginable):
    '''This is similar to freeTextSearch but different because it allows for a list of search queries instead of one
    query'''
    parser = boilerplate.get_parser()

    parser.add_argument('q', type=str, action='append', required=True, help="Query cannot be blank")
    parser.add_argument('filter', type=str, required=False, action='append', help="filter by target or disease")
    parser.add_argument('highlight', type=boolean, required=False,
                        help="return where the query was matched, defaults to true")
    parser.add_argument('search_entities', type=str, required=False, action="append",
                        help="specify the entity type to look for. Only {drug|all} at the momment")

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Search for gene and disease
        Search with a parameter q = 'your query'
        'fields':['id', 'approved_symbol']
        """
        start_time = time.time()
        kwargs = self.parser.parse_args()
        filter_ = kwargs.pop('filter') or ['all']
        searchphrases = kwargs.pop('q')
        if len(searchphrases) > 500:
            raise AttributeError('request size too big')
        res = current_app.extensions['esquery'].best_hit_search(searchphrases, doc_filter=filter_, **kwargs)
        return CTTVResponse.OK(res,
                               took=time.time() - start_time)

    @is_authenticated
    @rate_limit
    def post(self):
        """
        Search for gene and disease
        Search with a parameter q = 'your query'
        """
        start_time = time.time()
        kwargs = request.get_json(force=True)
        if 'filter' in kwargs:
            filter_ = [kwargs.pop('filter')]
        else:
            filter_ = ['all']
        searchphrases = kwargs.pop('q')
        if len(searchphrases) > 500:
            raise AttributeError('request size too big')

        res = current_app.extensions['esquery'].best_hit_search(searchphrases, doc_filter=filter_, **kwargs)
        return CTTVResponse.OK(res,
                               took=time.time() - start_time)


class QuickSearch(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('q', type=str, required=True, help="Query cannot be blank")
    parser.add_argument('size', type=int, required=False, help="number of objects to be returned per type")
    parser.add_argument('highlight', type=boolean, required=False,
                        help="return where the query was matched, defaults to true")

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Suggest best terms for gene and disease
        Search with a parameter q = 'your query'
        """
        start_time = time.time()
        kwargs = self.parser.parse_args()
        searchphrase = kwargs.pop('q')
        size = kwargs.pop('size') or 5
        if size > 10:
            size = 10
        if len(searchphrase) > 1:
            res = current_app.extensions['esquery'].quick_search(searchphrase, size=size, **kwargs)
            took = time.time() - start_time
            return CTTVResponse.OK(res, took=took)
        else:
            abort(400, message="Query is too short")


class AutoComplete(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('q', type=str, required=True, help="Query cannot be blank!")
    parser.add_argument('size', type=int, required=False, help="number ofobjects be returned.")

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Suggest best terms for gene and disease
        Search with a parameter q = 'your query'
        """
        kwargs = self.parser.parse_args()
        searchphrase = kwargs.pop('q')
        size = kwargs.pop('size') or 5
        if len(searchphrase) > 1:
            res = current_app.extensions['esquery'].autocomplete(searchphrase, size=size, **kwargs)
            return CTTVResponse.OK(res)
        else:
            abort(400, message="Query is too short")
