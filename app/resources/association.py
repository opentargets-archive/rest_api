from flask.ext.restful.inputs import boolean
from flask.ext.restful.reqparse import Argument
from app.common import boilerplate


from flask import current_app, request
from flask.ext import restful
from flask.ext.restful import abort, fields, marshal,marshal_with
from flask_restful_swagger import swagger
from flask.ext.restful import reqparse
from app.common.auth import is_authenticated
from app.common.response_templates import CTTVResponse, PaginatedResponse
from app.common.utils import get_ordered_filter_list


__author__ = 'andreap'

@swagger.model
class EvidenceQuery:
  "An object to specify an association query"
  resource_fields = {
      'gene': fields.List(fields.String(attribute='gene file name', )),
      'efo': fields.List(fields.String(attribute='efo code', )),


  }

  swagger_metadata = {
      'gene': {
          'list': ['one', 'two', 'three']
      }
  }






class Association(restful.Resource):

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
              "dataType": "string",
              "paramType": "query"
            },
            {
              "name": "filterbyscorevalue_min",
              "description": "the minimum value of association score you want to filter by",
              "required": False,
              "allowMultiple": False,
              "dataType": "string",
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


          ]

    # _swagger_parameters.extend(Paginable._swagger_parameters)
    @swagger.operation(
        nickname='association',
        produces = ["application/json", "text/xml", "text/csv"],

        # responseClass=PaginatedResponse.__name__,
        parameters=_swagger_parameters,
        )
    @is_authenticated
    def get(self):
        """
        Get association scores
        Get association scores for a gene, an efo or a combination of them
        Test with ENSG00000136997
        """
        parser = reqparse.RequestParser()
        parser.add_argument('gene', type=str, action='append', required=False, help="gene in biological_subject")
        # parser.add_argument('gene-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('efo', type=str, action='append', required=False, help="List of efo code in biological_object")
        # parser.add_argument('efo-bool', type=str, action='store', required=False, help="Boolean operator to combine genes")
        parser.add_argument('filterbyscorevalue_min', type=float, required=False, help="filter by minimum score value")
        parser.add_argument('filterbyscorevalue_max', type=float, required=False, help="filter by maximum score value")
        parser.add_argument('filterbydatasource', type=str, action='append', required=False,help="datasources to consider to calculate the association score")
        parser.add_argument('filterbydatatype', type=str, action='append', required=False,  help="datatype to consider to calculate the association score")
        parser.add_argument('filterbypathway', type=str, action='append', required=False, help="consider only genes linked to this pathway")
        # parser.add_argument('filter', type=str, required=False, help="pass a string uncluding the list of filters you want to apply in the right order. Only use if you cannot preserve the order of the arguments in the get request")
        parser.add_argument('datastructure', type=str, required=False, help="Return the output in a list with 'flat' or in a hierarchy with 'tree' (only works when searching for gene)", choices=['flat','tree'])
        parser.add_argument('expandefo', type=boolean, required=False, help="return the full efo tree if True or just direct links to an EFO code if False", default=False)


        args = parser.parse_args()
        # filters = args.pop('filter',[]) or []
        # if filters:
        #     filters = get_ordered_filter_list(filters)
        # else:
        #     filters = get_ordered_filter_list(request.query_string)
        # if filters:
        #     args['filter']=filters
        genes = args.pop('gene',[]) or []
        # gene_operator = args.pop('gene-bool','OR') or 'OR'
        objects = args.pop('efo',[]) or []
        # object_operator = args.pop('efo-bool','OR') or 'OR'


        if not (genes or objects ):
            abort(404, message='Please provide at least one gene or efo')
        return self.get_association(genes, objects,params=args)


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
        # if not res:
        #     abort(404, message='Cannot find associations for  %s'%str([genes,
        #                                                             objects,
        #                                                             # gene_operator,
        #                                                             # object_operator,
        #                                                             ]))
        return CTTVResponse.OK(res)

