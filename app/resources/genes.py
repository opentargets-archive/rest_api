
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort
from flask_restful_swagger import swagger
from flask.ext.restful import reqparse
from app.common import boilerplate
from app.common.boilerplate import Paginable
from app.common.responses import CTTVResponse





class Genes(restful.Resource, Paginable):

    @swagger.operation(
        notes='''get evidences for an ensembl ID, test with ENSG00000136997''',
        nickname='Genes',
        parameters=Paginable._swagger_parameters)
    def get(self, ensemblid ):
        kwargs = self.parser.parse_args()
        es = current_app.extensions['esquery']
        return CTTVResponse.OK(es.get_evidences_for_gene(ensemblid, **kwargs))


class AvailableGenes(restful.Resource):

    @swagger.operation(
        notes='''get a list of available genes - WARNING VERY SLOW''',)
    def get(self):
        es = current_app.extensions['esquery']
        return es.available_genes()


class GeneName(restful.Resource):

    @swagger.operation(
        notes='''get evidences for a gene name''',)
    def get(self, genename ):
        es = current_app.extensions['esquery']
        try:
            ensemblid_result = es._get_ensemblid_from_gene_name(genename)
            current_app.logger.debug("Ensembl ids: " + str(ensemblid_result))
        except:
             self.abort(genename)
        if ensemblid_result:
            ensemblid = ensemblid_result[0]['fields']['Ensembl Gene ID'][0]
            return CTTVResponse.OK(es.get_evidences_for_gene(ensemblid))
        else:
            self.abort(genename)

    def abort(self, genename):
        abort(404, message="Cannot find Symbol %s"%genename)


class GeneEvidenceByEfo(restful.Resource, Paginable):

    @swagger.operation(
        notes='''get evidences for a gene id and an efo code''',
        nickname='GeneEvidenceByEfo',
        parameters=Paginable._swagger_parameters,
    )
    def get(self, ensemblid, efocode ):
        es = current_app.extensions['esquery']
        kwargs = self.parser.parse_args()
        try:
            res = es.get_evidences_for_gene_and_efo(ensemblid, efocode, **kwargs)
        except:
             abort(404, message="Cannot find gene id %s or efo code %s"%(ensemblid, efocode))

        return CTTVResponse.OK(res)

