import time
from flask.ext.restful.inputs import boolean
from app.common import boilerplate
from app.common.rate_limit import rate_limit
from app.common.request_templates import EvidenceSortOptions

__author__ = 'andreap'
from flask import current_app, request
from flask.ext import restful
from flask.ext.restful import abort, fields, marshal,marshal_with
from flask.ext.restful import reqparse
from app.common.boilerplate import Paginable
from app.common.response_templates import CTTVResponse
import json
from app.common.auth import is_authenticated

# @swagger.model
# class GetByIdQuery:
#   "An object to specify an getbyid query"
#   resource_fields = {
#       'id': fields.List(fields.String(attribute='gene file name', ))
#   }


# @swagger.model
# class FilterByQuery:
#   "An object to specify a filterby query"
#   resource_fields = {
#       'target': fields.List(fields.String(attribute='target gene id', )),
#       'disease': fields.List(fields.String(attribute='diseaseefo code', )),
#       'eco': fields.List(fields.String(attribute='eco code', )),
#       'pathway': fields.List(fields.String(attribute='pathway', )),
#       'datasource': fields.List(fields.String(attribute='datasource', )),
#       'datatype': fields.List(fields.String(attribute='datatype', )),
#       'uniprotkw': fields.List(fields.String(attribute='uniprotkw', )),
#       'from': fields.Integer(attribute='paginate from',),
#       'size': fields.Integer(attribute='size to return', ),
#       'format': fields.String(attribute='format',),
#       'datastructure': fields.String(attribute='datastructure', ),
#       'fields': fields.List(fields.String(attribute='fields to return', )),
#       'expandefo': fields.Boolean(attribute='get data for efo children',),
#       # 'groupby': fields.List(fields.String(attribute='group returned evidence by', )),
#
#   }




class Evidence(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, action='append', required=True, help="List of IDs to retrieve")

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get an evidence from its id
        Can be used to request in batch if multiple ids are passed
        """
        start_time = time.time()
        args = self.parser.parse_args()
        evidenceids = args['id'][:1000]
        es = current_app.extensions['esquery']

        res = es.get_evidences_by_id(evidenceids)
        return CTTVResponse.OK(res,
                               took=time.time() - start_time)


    @is_authenticated
    @rate_limit
    def post(self):

        start_time = time.time()
        args = request.get_json(force=True)
        evidenceids = args['id']
        es = current_app.extensions['esquery']

        res = es.get_evidences_by_id(evidenceids)
        return CTTVResponse.OK(res,
                               took=time.time() - start_time)


class FilterBy(restful.Resource, Paginable):

    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get a list of evidences filtered by gene, efo and/or eco codes
        test with: ENSG00000136997,
        """
        parser = boilerplate.get_parser()
        parser.add_argument('target', type=str, action='append', required=False, help="ensembl id in target.id")
        # parser.add_argument('gene-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('disease', type=str, action='append', required=False, help="List of efo code in disease")
        # parser.add_argument('efo-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('eco', type=str, action='append', required=False, help="List of evidence types as eco code")
        # parser.add_argument('eco-bool', type=str, action='store', required=False, help="Boolean operator to combine evidence types")
        # parser.add_argument('body', type=str, action='store', required=False, location='form', help="json object with query parameter")
        parser.add_argument('datasource', type=str, action='append', required=False, help="List of datasource to consider")
        parser.add_argument('datatype', type=str, action='append', required=False, help="List of datatype to consider")
        # parser.add_argument('auth_token', type=str, required=True, help="auth_token is required")
        # parser.add_argument('direct', type=boolean, required=False, help="return only evidence directly associated with the efo term if false or to all its children if true", default=False)
        parser.add_argument('pathway', type=str, action='append', required=False, help="pathway involving a set of genes")
        parser.add_argument('uniprotkw', type=str, action='append', required=False, help="uniprot keyword linked to a set of genes")
        parser.add_argument('datatype', type=str, action='append', required=False, help="List of datatype to consider")
        parser.add_argument('scorevalue_min', type=float, required=False, help="filter by minimum score value")
        parser.add_argument('scorevalue_max', type=float, required=False, help="filter by maximum score value")
        parser.add_argument('sort', type=str, action='append', required=False, help="order the results by the given list of fields. default is score.association_score")
        parser.add_argument('facets', type=boolean, required=False, help="return the facets for the call. Default to True", default=True)
        parser.add_argument('abstract', type=str, required=False, help="Abstract term to consider")
        
        args = parser.parse_args()
        #targets = args.pop('target',[]) or []
        # gene_operator = args.pop('gene-bool','OR') or 'OR'
        #diseases = args.pop('disease',[]) or []
        # object_operator = args.pop('efo-bool','OR') or 'OR'
        #evidence_types = args.pop('eco',[]) or []
        # evidence_type_operator = args.pop('eco-bool','OR') or 'OR'
        #datasources =  args.pop('datasource',[]) or []
        #datatypes =  args.pop('datatype',[]) or []
        if args.get('sort') is None:
            args['sort'] = [EvidenceSortOptions.SCORE]
       

        # if not (genes
        #         or objects
        #         or evidence_types
        #         or datasources
        #         or datatypes
        #         or args['pathway']
        #         or args['uniprotkw']
        #         or args['datatype']):
        #     abort(404, message='Please provide at least one gene, efo, eco or datasource')
        data = self.get_evidence(params=args)
        return CTTVResponse.OK(data,
                              )



    @is_authenticated
    @rate_limit
    def post(self ):
        """
        Get a list of evidences filtered by gene, efo and/or eco codes
        test with: {"target":["ENSG00000136997"]},
        """
        def fix_empty_strings(l):
            new_l=[]
            if l:
                for i in l:
                    if i:
                        new_l.append(i)
            return new_l

        args = request.get_json(force=True)
       
        if args.get('sort') is None:
            args['sort'] = [EvidenceSortOptions.SCORE]


        data=self.get_evidence(params=args)
        return CTTVResponse.OK(data,
                               )


    def get_evidence(self,
                     params ={}):

        es = current_app.extensions['esquery']

        res = es.get_evidence(
                        **params)


        return res


