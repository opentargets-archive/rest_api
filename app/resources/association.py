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
from types import *
import time
from astropy.io.fits.card import UNDEFINED


__author__ = 'andreap'

class Association(restful.Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, action='append', required=True, help="List of IDs to retrieve")

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get an associations from its id
        Can be used to request in batch if multiple ids are passed
        """
        start_time = time.time()
        args = self.parser.parse_args()
        evidenceids = args['id'][:1000]
        es = current_app.extensions['esquery']

        res = es.get_associations_by_id(evidenceids)
        if not res:
            abort(404, message='Cannot find evidences for id %s'%str(evidenceids))
        return CTTVResponse.OK(res,
                               took=time.time() - start_time)

class FilterBy(restful.Resource):


    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get association objects
        Get association objects for a gene, an efo or a combination of them
        Test with ENSG00000136997
        """
        start_time = time.time()
        parser = boilerplate.get_parser()
        parser.add_argument('target', type=str, action='append', required=False, help="target in target.id")
        # parser.add_argument('gene-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('disease', type=str, action='append', required=False, help="efo code in disease.id")
        # parser.add_argument('efo-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('therapeutic_area', type=str, action='append', required=False, help="efo code of the therapeutic area")
        parser.add_argument('scorevalue_min', type=float, required=False, help="filter by minimum score value")
        parser.add_argument('scorevalue_max', type=float, required=False, help="filter by maximum score value")
        parser.add_argument('scorevalue_types', type=str, required=False, action='append', help="score types to apply min and max score filter")
        parser.add_argument('datasource', type=str, action='append', required=False,help="datasources to consider to calculate the association score")
        parser.add_argument('datatype', type=str, action='append', required=False,  help="datatype to consider to calculate the association score")
        parser.add_argument('pathway', type=str, action='append', required=False, help="consider only genes linked to this pathway")
        parser.add_argument('uniprotkw', type=str, action='append', required=False, help="consider only genes linked to this uniprot keyword")
        parser.add_argument('go', type=str, action='append', required=False,
                            help="consider only genes linked to this GO term")
        # parser.add_argument('filter', type=str, required=False, help="pass a string uncluding the list of filters you want to apply in the right order. Only use if you cannot preserve the order of the arguments in the get request")
        # parser.add_argument('outputstructure', type=str, required=False, help="Return the output in a list with 'flat' or in a hierarchy with 'tree' (only works when searching for gene)", choices=['flat','tree'])
        parser.add_argument('direct', type=boolean, required=False, help="return the full efo tree if True or just direct links to an EFO code if False")
        parser.add_argument('facets', type=boolean, required=False, help="return the facets for the call. Defaults to True", default=False)
        parser.add_argument('sort', type=str,  required=False, action='append', help="sort the results by this score type")
        parser.add_argument('search', type=str,  required=False, help="filter the results by fulltext matching")
        parser.add_argument('cap_scores', type=boolean, required=False, help="cap scores to 1 if bigger than that")

        args = parser.parse_args()
        data = self.get_association(params=args)
        return CTTVResponse.OK(data,
                               took=time.time() - start_time)


    @is_authenticated
    @rate_limit
    def post(self ):
        """
        Get association objects
        Get association objects for a gene, an efo or a combination of them
        Test with ENSG00000136997
        test with: {"target":["ENSG00000136997"]},
        """
        def fix_empty_strings(l):
            new_l=[]
            if l:
                for i in l:
                    if i:
                        new_l.append(i)
            return new_l

        start_time = time.time()
        args = request.get_json(force=True)
        for k,v in args.items():
            if isinstance(v, list):
                if len(v)>0:
                    drop = True
                    for i in v:
                        if i != '':
                            drop =False
                    if drop:
                        del args[k]

        #print("post:args=" +str(args))
        data = self.get_association(params=args)
        format = None
        if('format' in args):
            format = args['format']   
        #print "format = " + str(format)
        return CTTVResponse.OK(data, format,
                               took=time.time() - start_time)
  
    def get_association(self,params):        
        
        es = current_app.extensions['esquery']
        try:
            res = es.get_associations(**params)
        except AttributeError,e:
            print("AttributeError:" + message)
            abort(404, message=e.message)

        res.excluded_target_list = resultList[1]
        return res
    

    

