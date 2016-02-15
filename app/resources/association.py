from flask.ext.restful.inputs import boolean
from flask.ext.restful.reqparse import Argument
from app.common import boilerplate


from flask import current_app, request
from flask.ext import restful
from flask.ext.restful import abort, fields, marshal,marshal_with
from flask_restful_swagger import swagger
from flask.ext.restful import reqparse
from app.common.auth import is_authenticated
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse, PaginatedResponse
from app.common.utils import get_ordered_filter_list
import time


__author__ = 'andreap'

@swagger.model
class AssociationQuery:
  "An object to specify an association query"
  resource_fields = {
      'target': fields.List(fields.String(attribute='target id', )),
      'disease': fields.List(fields.String(attribute='disease efo code', )),
      'filterbyscorevalue_min': fields.Float(attribute='filterbyscorevalue_min',),
      'filterbyscorevalue_max': fields.Float(attribute='filterbyscorevalue_max',),
      'filterbydatasource': fields.List(fields.String(attribute='filterbydatasource', )),
      'filterbydatatype': fields.List(fields.String(attribute='filterbydatatype', )),
      'filterbypathway': fields.List(fields.String(attribute='filterbypathway', )),
      'filterbyuniprotkw': fields.List(fields.String(attribute='filterbyuniprotkw', )),
      'stringency': fields.Float(attribute='filterbydatasource', ),
      'datastructure': fields.String(attribute='filterbydatasource', ),
      'expandefo': fields.Boolean(attribute='expandefo', ),
      'facets': fields.Boolean(attribute='facets', ),

  }

  swagger_metadata = {
      'gene': {
          'list': ['one', 'two', 'three']
      }
  }






class Association(restful.Resource):
    pass

class FilterBy(restful.Resource):

    _swagger_parameters = [
            {
              "name": "target",
              "description": "a gene identifier listed as target.id",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            # {
            #   "name": "gene-bool",
            #   "description": "a boolean operator to combine the list of genes. Can be 'AND' or 'OR'. Default is 'OR'.",
            #   "required": False,
            #   "allowMultiple": True,
            #   "dataType": "string",
            #   "paramType": "query"
            # },
            {
              "name": "disease",
              "description": "a efo identifier listed as disease.id",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            #  {
            #   "name": "efo-bool",
            #   "description": "a boolean operator to combine the list of efo codes. Can be 'AND' or 'OR'. Default is 'OR'.",
            #   "required": False,
            #   "allowMultiple": True,
            #   "dataType": "string",
            #   "paramType": "query"
            # },
            # {
            #   "name": "filters",
            #   "description": "pass a string uncluding the list of filters you want to apply in the right order. Only use if you cannot preserve the order of the arguments in the get request",
            #   "required": False,
            #   "allowMultiple": False,
            #   "dataType": "string",
            #   "paramType": "query"
            # },
             {
              "name": "filterbyscorevalue_max",
              "description": "the maximum value of association score you want to filter by",
              "required": False,
              "allowMultiple": False,
              "defaultValue": 1,
              "dataType": "float",
              "paramType": "query"
            },
            {
              "name": "filterbyscorevalue_min",
              "description": "the minimum value of association score you want to filter by",
              "required": False,
              "allowMultiple": False,
              "defaultValue": 0.2,
              "dataType": "float",
              "paramType": "query"
            },
            {
              "name": "filterbydatasource",
              "description": "the datasource you want to consider when calculating the association score. Accepts a list of datasources.",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "filterbydatatype",
              "description": "the datatype you want to consider when calculating the association score. Accepts a list of datatypes.",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "filterbypathway",
              "description": "Consider just genes involved in this pathway. Accepts a list of pathway codes.",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "filterbyuniprotkw",
              "description": "Consider just genes with this uniprot keyword. Accepts a list of uniprot keywords.",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "stringency",
              "description": "Define the stringency in the association score calculation. The higher the stringency the more evidence is needed to reach a score of 1. default is 1",
              "required": False,
              "allowMultiple": True,
              "defaultValue": 1,
              "dataType": "float",
              "paramType": "query"
            },
            {
              "name": "datastructure",
              "description": "Return the output in a list with 'flat' or in a hierarchy with 'tree' (only works when searching for gene). Can be 'flat' or 'tree'",
              "required": False,
              "allowMultiple": False,
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "expandefo",
              "description": "return the full efo tree if true or just direct links to an EFO code if false",
              "required": False,
              "allowMultiple": False,
              "dataType": "boolean",
              "defaultValue": "false",
              "paramType": "query"
            },
            {
              "name": "facets",
              "description": "return the facets for the call. Default to True",
              "required": False,
              "allowMultiple": False,
              "dataType": "boolean",
              "defaultValue": "true",
              "paramType": "query"
            },


          ]

    # _swagger_parameters.extend(Paginable._swagger_parameters)
    @swagger.operation(
        nickname='association',
        produces = ["application/json", "text/xml", "text/csv"],

        # responseClass=PaginatedResponse.__name__,
        parameters=_swagger_parameters,
        )
    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get association objects
        Get association objects for a gene, an efo or a combination of them
        Test with ENSG00000136997
        """
        start_time = time.time()
        parser = reqparse.RequestParser()
        parser.add_argument('target', type=str, action='append', required=False, help="target in target.id")
        # parser.add_argument('gene-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('disease', type=str, action='append', required=False, help="efo code in disease.id")
        # parser.add_argument('efo-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('filterbyscorevalue_min', type=float, required=False, help="filter by minimum score value")
        parser.add_argument('filterbyscorevalue_max', type=float, required=False, help="filter by maximum score value")
        parser.add_argument('filterbydatasource', type=str, action='append', required=False,help="datasources to consider to calculate the association score")
        parser.add_argument('filterbydatatype', type=str, action='append', required=False,  help="datatype to consider to calculate the association score")
        parser.add_argument('filterbypathway', type=str, action='append', required=False, help="consider only genes linked to this pathway")
        parser.add_argument('filterbyuniprotkw', type=str, action='append', required=False, help="consider only genes linked to this uniprot keyword")
        parser.add_argument('stringency', type=float, required=False, help="Define the stringency in the association score calculation.")
        # parser.add_argument('filter', type=str, required=False, help="pass a string uncluding the list of filters you want to apply in the right order. Only use if you cannot preserve the order of the arguments in the get request")
        parser.add_argument('datastructure', type=str, required=False, help="Return the output in a list with 'flat' or in a hierarchy with 'tree' (only works when searching for gene)", choices=['flat','tree'])
        parser.add_argument('expandefo', type=boolean, required=False, help="return the full efo tree if True or just direct links to an EFO code if False", default=False)
        parser.add_argument('facets', type=boolean, required=False, help="return the facets for the call. Default to True", default=True)

        args = parser.parse_args()
        # filters = args.pop('filter',[]) or []
        # if filters:
        #     filters = get_ordered_filter_list(filters)
        # else:
        #     filters = get_ordered_filter_list(request.query_string)
        # if filters:
        #     args['filter']=filters
        genes = args.pop('target',[]) or []
        # gene_operator = args.pop('gene-bool','OR') or 'OR'
        objects = args.pop('disease',[]) or []
        # object_operator = args.pop('efo-bool','OR') or 'OR'


        if not (genes or objects ):
            abort(404, message='Please provide at least one target or disease')
        data = self.get_association(genes, objects,params=args)
        return CTTVResponse.OK(data,
                               took=time.time() - start_time)


    @swagger.operation(
        summary='''get a list of association objects by target and/or disease .''',
        notes='test with: {"target":["ENSG00000136997"]}',
        nickname='association',
        resourcePath ='/association',
        produces = ["application/json", "text/xml", "text/csv"],
        responseClass=PaginatedResponse.__name__,
        parameters=[
            {
              "name": "body",
              "description": "a json object with a query",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "body",
              "type": "AssociationQuery"
            },
            ]
        )
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
        args = request.get_json()
        genes = fix_empty_strings(args.pop('target',[]) or [])
        # gene_operator = args.pop('gene-bool','OR') or 'OR'
        objects = fix_empty_strings(args.pop('disease',[]) or [])
        # object_operator = args.pop('efo-bool','OR') or 'OR'
        for k,v in args.items():
            if isinstance(v, list):
                if len(v)>0:
                    drop = True
                    for i in v:
                        if i != '':
                            drop =False
                    if drop:
                        del args[k]

        if not (genes or objects ):
            abort(404, message='Please provide at least one target or disease')
        data = self.get_association(genes, objects,params=args)
        return CTTVResponse.OK(data,
                               took=time.time() - start_time)


    def get_association(self,
                     genes,
                     objects,
                     gene_operator='OR',
                     object_operator='OR',
                     params ={}):

        es = current_app.extensions['esquery']
        res = es.get_associations(genes = genes,
                                 objects = objects,
                                 # gene_operator = gene_operator,
                                 # object_operator = object_operator,
                                 # evidence_type_operator = evidence_type_operator,
                                 **params)

        return res

