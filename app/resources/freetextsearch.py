import flask
import time
from flask import current_app
from flask import request
from flask.ext import restful
from flask.ext.restful import abort,reqparse
from app.common import boilerplate
from app.common.auth import is_authenticated
from app.common.boilerplate import Paginable
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse


__author__ = 'andreap'




class FreeTextSearch(restful.Resource, Paginable):
    parser =boilerplate.get_parser()
    parser.add_argument('q', type=str, required=True, help="Query cannot be blank!")
    parser.add_argument('filter', type=str, required=False,  action='append', help="filter by gene or efo")
    
    
    @is_authenticated
    @rate_limit
    def get(self ):
        """
        Search for gene and disease
        Search with a parameter q = 'your query'
        """
        start_time = time.time()
        print "FreeTextSearch:start_time=" + str(start_time)
        kwargs = self.parser.parse_args()
        searchphrase = kwargs.pop('q')
        filter = kwargs.pop('filter') or ['all']
        if len(searchphrase)>1:
            res = current_app.extensions['esquery'].free_text_search(searchphrase, doc_filter= filter, **kwargs)

            return CTTVResponse.OK(res,
                                   took=time.time() - start_time)
        else:
            abort(400, message = "Query is too short")

    @is_authenticated
    @rate_limit
    def post(self ):
        """
        Search for gene and disease
        Parameters are passed with data 
        Search with a parameter q = 'your query'
        """
        start_time = time.time()
        print "FreeTextSearch:start_time=" + str(start_time)
        kwargs = request.get_json(force=True)
        for k,v in kwargs.items():
            if isinstance(v, list):
                if len(v)>0:
                    drop = True
                    for i in v:
                        if i != '':
                            drop =False
                    if drop:
                        del kwargs[k]
        print("free_text_search:post:args=" +str(kwargs))                
        searchphrase = kwargs.pop('q')
        filter = ['all']
        if ('filter' in kwargs):
            filter = kwargs['filter']
        
        if len(searchphrase)>1:
            res = current_app.extensions['esquery'].free_text_search(searchphrase, doc_filter= filter, **kwargs)

            return CTTVResponse.OK(res,
                                   took=time.time() - start_time)
        else:
            abort(400, message = "Query is too short")



class QuickSearch(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('q', type=str, required=True, help="Query cannot be blank!")
    parser.add_argument('size', type=int, required=False, help="number of genes or efo to be returned.")

    @is_authenticated
    @rate_limit
    def get(self ):
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
        if len(searchphrase)>1:
            res = current_app.extensions['esquery'].quick_search(searchphrase, size = size,**kwargs)
            took = time.time() - start_time
            return CTTVResponse.OK(res, took=took)
        else:
            abort(400, message = "Query is too short")



class AutoComplete(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('q', type=str, required=True, help="Query cannot be blank!")
    parser.add_argument('size', type=int, required=False, help="number ofobjects be returned.")

    @is_authenticated
    @rate_limit
    def get(self ):
        """
        Suggest best terms for gene and disease
        Search with a parameter q = 'your query'
        """
        kwargs = self.parser.parse_args()
        searchphrase = kwargs.pop('q')
        size = kwargs.pop('size') or 5
        if len(searchphrase)>1:
            res = current_app.extensions['esquery'].autocomplete(searchphrase, size = size,**kwargs)
            return CTTVResponse.OK(res)
        else:
            abort(400, message = "Query is too short")

