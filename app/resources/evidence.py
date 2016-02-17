import time
from flask.ext.restful.inputs import boolean
from app.common import boilerplate
from app.common.rate_limit import rate_limit

__author__ = 'andreap'
from flask import current_app, request
from flask.ext import restful
from flask.ext.restful import abort, fields, marshal,marshal_with
from flask_restful_swagger import swagger
from flask.ext.restful import reqparse
from app.common.boilerplate import Paginable
from app.common.response_templates import CTTVResponse, PaginatedResponse
import json
from app.common.auth import is_authenticated

@swagger.model
class GetByIdQuery:
  "An object to specify an getbyid query"
  resource_fields = {
      'id': fields.List(fields.String(attribute='gene file name', ))
  }


@swagger.model
class FilterByQuery:
  "An object to specify a filterby query"
  resource_fields = {
      'target': fields.List(fields.String(attribute='target gene id', )),
      'disease': fields.List(fields.String(attribute='diseaseefo code', )),
      'eco': fields.List(fields.String(attribute='eco code', )),
      'pathway': fields.List(fields.String(attribute='pathway', )),
      'datasource': fields.List(fields.String(attribute='datasource', )),
      'datatype': fields.List(fields.String(attribute='datatype', )),
      'uniprotkw': fields.List(fields.String(attribute='uniprotkw', )),
      'from': fields.Integer(attribute='paginate from',),
      'size': fields.Integer(attribute='size to return', ),
      'format': fields.String(attribute='format',),
      'datastructure': fields.String(attribute='datastructure', ),
      'fields': fields.List(fields.String(attribute='fields to return', )),
      'expandefo': fields.Boolean(attribute='get data for efo children',),
      # 'groupby': fields.List(fields.String(attribute='group returned evidence by', )),

  }




class Evidence(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, action='append', required=True, help="List of IDs to request")

    @swagger.operation(
        nickname='evidence',
        produces = ["application/json"],
        parameters=[
            {
              "name": "id",
              "description": "an evidence id you want to retrieve",
              "required": True,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            }
          ],
        )
    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get an evidence from its id
        Can be used to request in batch if multiple ids are passed
        """
        start_time = time.time()
        args = self.parser.parse_args()
        evidenceids = args['id']
        es = current_app.extensions['esquery']

        res = es.get_evidences_by_id(evidenceids)
        if not res:
            abort(404, message='Cannot find evidences for id %s'%str(evidenceids))
        return CTTVResponse.OK(res,
                               took=time.time() - start_time)

    @swagger.operation(
        nickname='evidence',
        resourcePath ='/evidence',
        produces = ["application/json",],
        parameters=[
            {
              "name": "body",
              "description": "an evidence id you want to retrieve",
              "required": True,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "body",
              "type": "GetByIdQuery"
            },
            ]
        )
    @is_authenticated
    @rate_limit
    def post(self):

        start_time = time.time()
        args = request.get_json()
        evidenceids = args['id']
        es = current_app.extensions['esquery']

        res = es.get_evidences_by_id(evidenceids)
        if not res:
            abort(404, message='Cannot find evidences for id %s'%str(evidenceids))
        return CTTVResponse.OK(res,
                               took=time.time() - start_time)


class FilterBy(restful.Resource, Paginable):

    _swagger_parameters = [
            {
              "name": "target",
              "description": "a target identifier listed as target.id",
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
            {
              "name": "eco",
              "description": "a eco identifier listed in the evidence",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            # {
            #   "name": "eco-bool",
            #   "description": "a boolean operator to combine the list of eco codes. Can be 'AND' or 'OR'. Default is 'OR'.",
            #   "required": False,
            #   "allowMultiple": True,
            #   "dataType": "string",
            #   "paramType": "query"
            # },
            {
              "name": "pathway",
              "description": "a pathway identifier (meaning all the genes linked to that pathway",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "uniprotkw",
              "description": "a uniprot keyword (meaning all the genes linked to that pathway)",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "datasource",
              "description": "datasource to consider",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "datatype",
              "description": "datatype to consider",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "datastructure",
              "description": "Type of data structure to return. Can be 'full', 'simple', 'ids', or 'count' ",
              "required": False,
              "allowMultiple": False,
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "fields",
              "description": "fields you want to retrieve. this will get priority over the datastructure requested",
              "required": False,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            },
            # {
            #   "name": "groupby",
            #   "description": "group returned elements by the indicated value",
            #   "required": False,
            #   "allowMultiple": True,
            #   "dataType": "string",
            #   "paramType": "query"
            # },
            {
              "name": "expandefo",
              "description": "return only evidence directly associated with the efo term if false or to all its children if true",
              "required": False,
              "allowMultiple": False,
              "dataType": "boolean",
              "defaultValue": "false",
              "paramType": "query"
            },
            #  {
            #   "name": "scorevalue_max",
            #   "description": "the maximum value of association score you want to filter by",
            #   "required": False,
            #   "allowMultiple": False,
            #   "defaultValue": 1,
            #   "dataType": "float",
            #   "paramType": "query"
            # },
            # {
            #   "name": "scorevalue_min",
            #   "description": "the minimum value of association score you want to filter by",
            #   "required": False,
            #   "allowMultiple": False,
            #   "defaultValue": 0,
            #   "dataType": "float",
            #   "paramType": "query"
            # },
          ]

    _swagger_parameters.extend(Paginable._swagger_parameters)
    @swagger.operation(
        nickname='filterby',
        produces = ["application/json", "text/xml", "text/csv"],

        responseClass=PaginatedResponse.__name__,
        parameters=_swagger_parameters,
        )
    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get a list of evidences filtered by gene, efo and/or eco codes
        test with: ENSG00000136997,
        """
        start_time = time.time()
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
        parser.add_argument('expandefo', type=boolean, required=False, help="return only evidence directly associated with the efo term if false or to all its children if true", default=False)
        parser.add_argument('pathway', type=str, action='append', required=False, help="pathway involving a set of genes")
        parser.add_argument('uniprotkw', type=str, action='append', required=False, help="uniprot keyword linked to a set of genes")
        parser.add_argument('datatype', type=str, action='append', required=False, help="List of datatype to consider")
        parser.add_argument('scorevalue_min', type=float, required=False, help="filter by minimum score value")
        parser.add_argument('scorevalue_max', type=float, required=False, help="filter by maximum score value")

        args = parser.parse_args()
        targets = args.pop('target',[]) or []
        # gene_operator = args.pop('gene-bool','OR') or 'OR'
        diseases = args.pop('disease',[]) or []
        # object_operator = args.pop('efo-bool','OR') or 'OR'
        evidence_types = args.pop('eco',[]) or []
        # evidence_type_operator = args.pop('eco-bool','OR') or 'OR'
        datasources =  args.pop('datasource',[]) or []
        datatypes =  args.pop('datatype',[]) or []

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
                               took=time.time() - start_time)


    @swagger.operation(
        nickname='filterby',
        resourcePath ='/filterby',
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
              "type": "FilterByQuery"
            },
            ]
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

        start_time = time.time()
        args = request.get_json()
        if args:
            targets = fix_empty_strings(args.pop('target',[]) or [])
            # gene_operator = args.pop('gene-bool','OR') or 'OR'
            diseases = fix_empty_strings(args.pop('disease',[]) or [])
            # object_operator = args.pop('efo-bool','OR') or 'OR'
            evidence_types = fix_empty_strings(args.pop('eco',[]) or [])
            # evidence_type_operator = args.pop('eco-bool','OR') or 'OR'
            datasources =  args.pop('datasource',[]) or []
            datatypes=  args.pop('datatype',[]) or []

            if not (targets or diseases or evidence_types or datasources or datatypes):
                abort(404, message='Please provide at least one target, disease, eco, datasource or datatype')
            data=self.get_evidence(targets, diseases, evidence_types, datasources, datatypes, params=args)
            return CTTVResponse.OK(data,
                                   took=time.time() - start_time)
        abort(404, message='Please provide at least one target, disease, eco, datasource or datatype')


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

        try:
            res = es.get_evidence(targets= targets,
                                  diseases= diseases,
                                  evidence_types = evidence_types,
                                  datasources = datasources,
                                  datatypes = datatype,
                                  # gene_operator = gene_operator,
                                   # object_operator = object_operator,
                                   # evidence_type_operator = evidence_type_operator,
                                   **params)
        except AttributeError,e:
            abort(404, message=e.message)

        return res


