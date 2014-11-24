__author__ = 'andreap'
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort
from flask_restful_swagger import swagger
from flask.ext.restful import reqparse
from app.common.boilerplate import Paginable
from app.common.responses import CTTVResponse





class Evidence(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, action='append', required=True, help="List of IDs to request")

    @swagger.operation(
        notes='''get an evidence from its id, can be used to request in batch if multiple ids are passed.''',
        nickname='evidence',
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



class EvidenceWithEfoAsObject(restful.Resource, Paginable):

    @swagger.operation(
        notes='''get evidences for for an EFO code, test with efo:EFO_0000637, efo:EFO_0000761''',
        nickname='EvidenceWithEfoAsObject',
        parameters=Paginable._swagger_parameters)


    def get(self, efocode ):
        es = current_app.extensions['esquery']
        kwargs = self.parser.parse_args()
        res = es.get_evidences_with_efo_code_as_object(efocode,**kwargs)
        return  CTTVResponse.OK(res)

