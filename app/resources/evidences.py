from app.common import boilerplate

__author__ = 'andreap'
from flask import current_app, request
from flask.ext import restful
from flask.ext.restful import abort, fields, marshal,marshal_with
from flask_restful_swagger import swagger
from flask.ext.restful import reqparse
from app.common.boilerplate import Paginable
from app.common.responses import CTTVResponse, PaginatedResponse
from app.common.requests import json_type
import ujson as json



@swagger.model
class EvidenceQuery:
  "An object to specify an evidence query"
  resource_fields = {
      'gene': fields.List(fields.String(attribute='gene file name', )),
      'efo': fields.List(fields.String(attribute='efo code', )),
      'eco': fields.List(fields.String(attribute='efo code', )),
      'from': fields.Integer(attribute='paginate from',),
      'size': fields.Integer(attribute='size to return', ),
      'format': fields.String(attribute='format',),
      'datastructure': fields.String(attribute='datastructure', ),

  }

  swagger_metadata = {
      'gene': {
          'list': ['one', 'two', 'three']
      }
  }





class Evidence(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, action='append', required=True, help="List of IDs to request")

    @swagger.operation(
        summary='get an evidence from its id, can be used to request in batch if multiple ids are passed.',
        nickname='evidence',
        produces = ["application/json", "text/xml", "text/csv"],
        parameters=[
            {
              "name": "id",
              "description": "an evidene id you want to retrieve",
              "required": True,
              "allowMultiple": True,
              "dataType": "string",
              "paramType": "query"
            }
          ],
        )
    def get(self ):
        args = self.parser.parse_args()
        evidenceids = args['id']
        es = current_app.extensions['esquery']

        res = es.get_evidences_by_id(evidenceids)
        if not res:
            abort(404, message='Cannot find evidences for id %s'%str(evidenceids))
        return res


class Evidences(restful.Resource, Paginable):

    _swagger_parameters = [
            {
              "name": "gene",
              "description": "a gene identifier listed as biological subject",
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
              "name": "efo",
              "description": "a efo identifier listed as biological object",
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

          ]

    _swagger_parameters.extend(Paginable._swagger_parameters)
    @swagger.operation(
        summary='''get a list of evidences filtered by gene, efo and/or eco codes.''',
        notes= 'test with ENSG00000136997',
        nickname='evidences',
        produces = ["application/json", "text/xml", "text/csv"],

        responseClass=PaginatedResponse.__name__,
        parameters=_swagger_parameters,
        )
    def get(self):
        parser = boilerplate.get_parser()
        parser.add_argument('gene', type=str, action='append', required=False, help="gene in biological_subject")
        # parser.add_argument('gene-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('efo', type=str, action='append', required=False, help="List of efo code in biological_object")
        # parser.add_argument('efo-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('eco', type=str, action='append', required=False, help="List of evidence types as eco code")
        # parser.add_argument('eco-bool', type=str, action='store', required=False, help="Boolean operator to combine evidence types")
        # parser.add_argument('body', type=str, action='store', required=False, location='form', help="json object with query parameter")

        args = parser.parse_args()
        genes = args.pop('gene',[]) or []
        # gene_operator = args.pop('gene-bool','OR') or 'OR'
        objects = args.pop('efo',[]) or []
        # object_operator = args.pop('efo-bool','OR') or 'OR'
        evidence_types = args.pop('eco',[]) or []
        # evidence_type_operator = args.pop('eco-bool','OR') or 'OR'

        if not (genes or objects or evidence_types):
            abort(404, message='Please provide at least one gene, efo or eco')
        return self.get_evidence(genes, objects, evidence_types, params=args)


    @swagger.operation(
        summary='''get a list of evidences filtered by gene, efo and/or eco codes.''',
        notes='test with: {"gene":["ENSG00000136997"]}',
        nickname='evidences',
        resourcePath ='/evidences',
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
              "type": "EvidenceQuery"
            },
            ]
        )
   # @marshal_with(EvidenceQuery.resource_fields)
    def post(self ):
        # parser = reqparse.RequestParser()
        # parser.add_argument('gene', type=fields.List(fields.String),location='form', required=False, help="List of genes in biological_subject")
        #
        # args = parser.parse_args()
        # print args
        # print request
        def fix_empty_strings(l):
            new_l=[]
            if l:
                for i in l:
                    if i:
                        new_l.append(i)
            return new_l


        args = request.get_json()
        genes = fix_empty_strings(args.pop('gene',[]) or [])
        # gene_operator = args.pop('gene-bool','OR') or 'OR'
        objects = fix_empty_strings(args.pop('efo',[]) or [])
        # object_operator = args.pop('efo-bool','OR') or 'OR'
        evidence_types = fix_empty_strings(args.pop('eco',[]) or [])
        # evidence_type_operator = args.pop('eco-bool','OR') or 'OR'
        if not (genes or objects or evidence_types):
            abort(404, message='Please provide at least one gene, efo or eco')
        return self.get_evidence(genes, objects, evidence_types, params=args)


    def get_evidence(self,
                     genes,
                     objects,
                     evidence_types,
                     gene_operator='OR',
                     object_operator='OR',
                     evidence_type_operator='OR',
                     params ={}):

        es = current_app.extensions['esquery']

        res = es.get_evidences(genes = genes,
                               objects = objects,
                               evidence_types = evidence_types,
                               # gene_operator = gene_operator,
                               # object_operator = object_operator,
                               # evidence_type_operator = evidence_type_operator,
                               **params)
        if not res:
            abort(404, message='Cannot find evidences for  %s'%str([genes,
                                                                    objects,
                                                                    evidence_types,
                                                                    # gene_operator,
                                                                    # object_operator,
                                                                    # evidence_type_operator,
                                                                    ]))
        return CTTVResponse.OK(res)


class EvidenceWithEfoAsObject(restful.Resource, Paginable):
    '''http://127.0.0.1:5000/api/public/v0.2/evidences/?gene=ENSG00000103197&gene=ENSG00000181090'''

    @swagger.operation(
        notes='''get evidences for for an EFO code, test with  http://identifiers.org/atc/A, efo:EFO_0000637, efo:EFO_0000761''',
        nickname='EvidenceWithEfoAsObject',
        parameters=Paginable._swagger_parameters)


    def get(self, efocode ):
        es = current_app.extensions['esquery']
        kwargs = self.parser.parse_args()
        res = es.get_evidences_with_efo_code_as_object(efocode,**kwargs)
        return  CTTVResponse.OK(res)


