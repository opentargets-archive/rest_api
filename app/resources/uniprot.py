
__author__ = 'andreap'
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort
from flask_restful_swagger import swagger


class Uniprot(restful.Resource):

    @swagger.operation(
        notes='''get evidences for uniprot id''',)
    @is_authenticated
    def get(self, uniprotid):

        es = current_app.extensions['esquery']
        ensemblid = es.get_ensemblid_from_uniprotid(uniprotid)

        if ensemblid:
            return  es.get_evidences_for_gene(ensemblid)
        else:
            abort(404, message="Uniprot ID %s cannot be mapped to an ensembl gene"%uniprotid)

class UniprotFromEnsembl(restful.Resource):


    @swagger.operation(
        notes='''get uniprot ID from ensembl ID, test with  ENSG00000136997 ''',)
    @is_authenticated
    def get(self, ensemblid):
        es = current_app.extensions['esquery']
        uniprotid = es.get_uniprotid_from_ensemblid(ensemblid)

        if uniprotid:
            return uniprotid
        else:
            abort(404, message="Ensembl ID %s cannot be mapped to a Uniprot ID"%ensemblid)

class EnsemblFromUniprot(restful.Resource):


    @swagger.operation(
        notes='''get ensembl ID from uniprot ID,  test with P01106''',)
    @is_authenticated
    def get(self, uniprotid):
        es = current_app.extensions['esquery']
        ensemblid = es.get_ensemblid_from_uniprotid(uniprotid)
        if ensemblid:
            return ensemblid
        else:
            abort(404, message="Uniprot ID %s cannot be mapped to a Ensembl ID"%uniprotid)