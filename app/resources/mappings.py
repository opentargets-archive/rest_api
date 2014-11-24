__author__ = 'andreap'
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort
from flask_restful_swagger import swagger




class StartFromUniprot(restful.Resource):

    @swagger.operation(
        notes='''get mapping data for uniprot id''',)
    def get(self, uniprotid ):
        es = current_app.extensions['elasticsearch']
        mapping_index_name = current_app.config['ELASTICSEARCH_MAPPING_INDEX_NAME']
        res = es.search(index=mapping_index_name,
                doc_type='mapping',
                body={'query': {
                                "match" : {'uniprot_accession': uniprotid}

                                }

                    }
            )
        if res['hits']['total']:
            for hit in res['hits']['hits']:
                return hit['_source']
        else:
            abort(404, message="Cannot find Uniprot ID %s"%uniprotid)

class StartFromEnsemblGene(restful.Resource):

    @swagger.operation(
        notes='''get mapping data for ensembl gene id''',)
    def get(self, ensemblgeneid ):
        es = current_app.extensions['elasticsearch']
        mapping_index_name = current_app.config['ELASTICSEARCH_MAPPING_INDEX_NAME']
        res = es.search(index=mapping_index_name,
                doc_type='mapping',
                body={'query': {
                                "match" : {'ensembl_gene_id': ensemblgeneid}

                                }

                    }
            )
        if res['hits']['total']:
            for hit in res['hits']['hits']:
                return hit['_source']
        else:
            abort(404, message="Cannot find Ensembl Gene ID %s"%ensemblgeneid)

class StartFromEnsemblTranscript(restful.Resource):

    @swagger.operation(
        notes='''get mapping data for ensembl transcript id''',)
    def get(self, ensembltranscriptid ):
        es = current_app.extensions['elasticsearch']
        mapping_index_name = current_app.config['ELASTICSEARCH_MAPPING_INDEX_NAME']
        res = es.search(index=mapping_index_name,
                doc_type='mapping',
                body={'query': {
                                "match" : {'ensembl_transcript_id': ensembltranscriptid}

                                }

                    }
            )
        if res['hits']['total']:
            for hit in res['hits']['hits']:
                return hit['_source']
        else:
            abort(404, message="Cannot find Ensembl Transcript ID %s"%ensembltranscriptid)

class StartFromEnsemblProtein(restful.Resource):

    @swagger.operation(
        notes='''get mapping data for ensembl protein id''',)
    def get(self, ensemblproteinid ):
        es = current_app.extensions['elasticsearch']
        mapping_index_name = current_app.config['ELASTICSEARCH_MAPPING_INDEX_NAME']
        res = es.search(index=mapping_index_name,
                doc_type='mapping',
                body={'query': {
                                "match" : {'ensembl_protein_id': ensemblproteinid}

                                }

                    }
            )
        if res['hits']['total']:
            for hit in res['hits']['hits']:
                return hit['_source']
        else:
            abort(404, message="Cannot find Ensembl Protein ID %s"%ensemblproteinid)