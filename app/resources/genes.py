
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort
from flask_restful_swagger import swagger
from flask.ext.restful import reqparse
from app.common import boilerplate
from app.common.auth import is_authenticated
from app.common.boilerplate import Paginable
from app.common.response_templates import CTTVResponse



class GeneInfo(restful.Resource):

    @swagger.operation()
    @is_authenticated
    def get(self, target_id ):
        '''
        Get gene information
        Get a gene generic information from an ensembl gene id'''
        es = current_app.extensions['esquery']
        res = es.get_gene_info([target_id])
        if res:
            data = res.toDict()['data']
            if data:
                return data[0]

        abort(404, message="Gene id %s cannot be found"%target_id)

