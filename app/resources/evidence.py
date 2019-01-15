import time
from flask_restful.inputs import boolean
from app.common import boilerplate
from app.common.request_templates import EvidenceSortOptions

__author__ = 'andreap'
from flask import current_app, request

from flask_restful import reqparse, Resource
from app.common.boilerplate import Paginable
from app.common.response_templates import CTTVResponse
from app.common.utils import fix_empty_strings

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


class Evidence(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, action='append', required=True,
                        help="List of IDs to retrieve")


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

    def post(self):

        start_time = time.time()
        args = request.get_json(force=True)
        evidenceids = args['id']
        es = current_app.extensions['esquery']

        res = es.get_evidences_by_id(evidenceids)
        return CTTVResponse.OK(res,
                               took=time.time() - start_time)


class FilterBy(Resource, Paginable):

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
        parser.add_argument('scorevalue_min', type=float, required=False, help="filter by minimum score value")
        parser.add_argument('scorevalue_max', type=float, required=False, help="filter by maximum score value")
        parser.add_argument('sort', type=str, action='append', required=False, help="order the results by the given list of fields. default is score.association_score")

        parser.add_argument('begin', type=long, required=False, help="filter by range with this start")
        parser.add_argument('end', type=long, required=False, help="filter by range with this end")
        parser.add_argument('chromosome', type=str, required=False, help="filter by range required chromosome location")

        args = parser.parse_args()
        targets = args.pop('target',[]) or []
        # gene_operator = args.pop('gene-bool','OR') or 'OR'
        diseases = args.pop('disease',[]) or []
        # object_operator = args.pop('efo-bool','OR') or 'OR'
        evidence_types = args.pop('eco',[]) or []
        # evidence_type_operator = args.pop('eco-bool','OR') or 'OR'
        datasources =  args.pop('datasource',[]) or []
        datatypes =  args.pop('datatype',[]) or []
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
        data = self.get_evidence(targets, diseases, evidence_types, datasources,  datatypes, params=args)
        return CTTVResponse.OK(data,
                              )


    def post(self ):
        """
        Get a list of evidences filtered by gene, efo and/or eco codes
        test with: {"target":["ENSG00000136997"]},
        """
        args = request.get_json(force=True)
        targets = fix_empty_strings(args.pop('target',[]) or [])
        # gene_operator = args.pop('gene-bool','OR') or 'OR'
        diseases = fix_empty_strings(args.pop('disease',[]) or [])
        # object_operator = args.pop('efo-bool','OR') or 'OR'
        evidence_types = fix_empty_strings(args.pop('eco',[]) or [])
        # evidence_type_operator = args.pop('eco-bool','OR') or 'OR'
        datasources =  args.pop('datasource',[]) or []
        datatypes=  args.pop('datatype',[]) or []
        if args.get('sort') is None:
            args['sort'] = [EvidenceSortOptions.SCORE]


        data=self.get_evidence(targets, diseases, evidence_types, datasources, datatypes, params=args)
        return CTTVResponse.OK(data,
                               )


    def get_evidence(self,
                     targets,
                     diseases,
                     evidence_types,
                     datasources,
                     datatype,
                     gene_operator='OR',
                     object_operator='OR',
                     evidence_type_operator='OR',
                     params ={}):

        es = current_app.extensions['esquery']

        res = es.get_evidence(targets= targets,
                              diseases= diseases,
                              evidence_types = evidence_types,
                              datasources = datasources,
                              datatypes = datatype,
                              # gene_operator = gene_operator,
                               # object_operator = object_operator,
                               # evidence_type_operator = evidence_type_operator,
                               **params)


        return res


