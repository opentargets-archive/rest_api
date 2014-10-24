from flask.ext.restful import abort

__author__ = 'andreap'
from flask import current_app
from flask.ext import restful



def get_ensembl_id_from_uniprot_id(uniprotid, es, mapping_index_name):
    res = es.search(index=mapping_index_name,
                doc_type='mapping',
                body={'query': {
                        'match': {
                            'uniprot_accession': uniprotid}
                        },
                      }
            )
    for hit in res['hits']['hits']:
        return  hit['_source']['ensembl_gene_id']

class Uniprot(restful.Resource):

    def get(self, uniprotid):
        es = current_app.extensions['elasticsearch']
        data_index_name = current_app.config['ELASTICSEARCH_DATA_INDEX_NAME']
        mapping_index_name = current_app.config['ELASTICSEARCH_MAPPING_INDEX_NAME']
        ensemblid = get_ensembl_id_from_uniprot_id(uniprotid, es, mapping_index_name)
        if ensemblid:
            res = es.search(index=data_index_name,
                    doc_type='evidence',
                    body={'query': {
                            'match': {
                                'biological_subject.about': 'ensembl:'+ensemblid}
                            },
                          'size':1
                          }
                )
            print("Got %d Hits in %ims"%(res['hits']['total'],res['took']))
            return [hit['_source'] for hit in res['hits']['hits']]
        else:
            abort(404, message="Uniprot ID %s cannot be mapped to an ensembl gene"%uniprotid)