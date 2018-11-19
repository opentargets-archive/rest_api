from flask_restful.inputs import boolean
from flask_restful.reqparse import Argument
from app.common import boilerplate

from flask import current_app, request

from flask_restful import abort, fields, marshal,marshal_with
from flask_restful import reqparse, Resource
from app.common.auth import is_authenticated
from app.common.rate_limit import rate_limit
from app.common.request_templates import FilterTypes
from app.common.response_templates import CTTVResponse
from types import *
import time

import pprint

__author__ = 'andreap'

class Association(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, action='append', required=True, )

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get an associations from its id
        Can be used to request in batch if multiple ids are passed
        """
        args = self.parser.parse_args()
        evidenceids = args['id'][:1000]
        es = current_app.extensions['esquery']

        res = es.get_associations_by_id(evidenceids)
        if not res:
            abort(404, message='Cannot find evidences for id %s'%str(evidenceids))
        return CTTVResponse.OK(res)

class FilterBy(Resource):


    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get association objects
        Get association objects for a gene, an efo or a combination of them
        Test with ENSG00000136997
        """
        parser = boilerplate.get_parser()
        parser.add_argument('target', type=str, action='append', required=False,)
        # parser.add_argument('gene-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('disease', type=str, action='append', required=False, )
        # parser.add_argument('efo-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('therapeutic_area', type=str, action='append', required=False, )
        parser.add_argument('scorevalue_min', type=float, required=False, )
        parser.add_argument('scorevalue_max', type=float, required=False, )
        parser.add_argument('scorevalue_types', type=str, required=False, action='append',)
        parser.add_argument('datasource', type=str, action='append', required=False,)
        parser.add_argument('datatype', type=str, action='append', required=False, )
        parser.add_argument('pathway', type=str, action='append', required=False, )
        parser.add_argument(FilterTypes.TARGET_CLASS, type=int, action='append', )
        parser.add_argument('uniprotkw', type=str, action='append', required=False,)
        parser.add_argument('rna_expression_level', type=int, default=0,
                            choices=list(xrange(0, 11)), required=False)
        parser.add_argument('rna_expression_tissue', type=str, action='append',
                            required=False, default=[])
        parser.add_argument('protein_expression_level', type=int, default=0,
                            choices=list(xrange(0, 4)), required=False)
        parser.add_argument('protein_expression_tissue', type=str, action='append',
                            required=False, default=[])
        parser.add_argument(FilterTypes.ANTIBODY, type=str, action='append',
                            required=False, default=[])
        parser.add_argument(FilterTypes.SMALL_MOLECULE, type=str, action='append',
                            required=False, default=[])
        parser.add_argument('go', type=str, action='append', required=False,
                            help="consider only genes linked to this GO term")
        # parser.add_argument('filter', type=str, required=False, help="pass a string uncluding the list of filters you want to apply in the right order. Only use if you cannot preserve the order of the arguments in the get request")
        # parser.add_argument('outputstructure', type=str, required=False, help="Return the output in a list with 'flat' or in a hierarchy with 'tree' (only works when searching for gene)", choices=['flat','tree'])

        parser.add_argument('targets_enrichment', type=str, required=False, help="disease enrichment analysis for a set of targets")
        parser.add_argument('direct', type=boolean, required=False,)
        parser.add_argument('facets', type=str, required=False,  default="")
        parser.add_argument('facets_size', type=int, required=False, default=0)
        parser.add_argument('sort', type=str,  required=False, action='append',)
        parser.add_argument('search', type=str,  required=False, )
        parser.add_argument('cap_scores', type=boolean, required=False, )

        args = parser.parse_args()
        self.remove_empty_params(args)

        data = self.get_association(params=args)

        return CTTVResponse.OK(data)

    @is_authenticated
    @rate_limit
    def post(self):
        """
        Get association objects
        Get association objects for a gene, an efo or a combination of them
        Test with ENSG00000136997
        test with: {"target":["ENSG00000136997"]},
        TODO:create new tests that check for the empty params being passed
        """
        start_time = time.time()
        args = request.get_json(force=True)
        self.remove_empty_params(args)

        data = self.get_association(params=args)
        format = None
        if('format' in args):
            format = args['format']

        return CTTVResponse.OK(data, format,
                               took=time.time() - start_time)

    def get_association(self, params):
        es = current_app.extensions['esquery']
        try:
            res = es.get_associations(**params)
        except AttributeError as e:
            abort(404, message=e.message)

        return res

    def remove_empty_params(self,args):
        for k,v in args.items():
            if isinstance(v, list):
                if len(v)>0:
                    drop = True
                    for i in v:
                        if i != '':
                            drop =False
                    if drop:
                        del args[k]
