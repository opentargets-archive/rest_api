from flask import current_app
from flask.ext import restful

def get_uniprotid_from_ensg(ensg, es,):
    res = es.search(index=current_app.config['ELASTICSEARCH_MAPPING_INDEX_NAME'],
                doc_type='mapping',
                body={'query': {
                        'match': {
                            'ensembl_gene_id': ensg}
                        },
                      }
            )
    for hit in res['hits']['hits']:
        return  hit['_source']['uniprot_accession']




class Genes(restful.Resource):

    def get(self, ensemblid = None):
        es = current_app.extensions['elasticsearch']
        index_name = current_app.config['ELASTICSEARCH_DATA_INDEX_NAME']
        if ensemblid is None:
            res = es.search(index=index_name,
                doc_type='evidence',
                body={'query': {
                        'wildcard': {
                            'biological_subject.about': 'ensembl:*'}
                        },
                      'size':100
                      }
               )
            print("Got %d Hits in %ims"%(res['hits']['total'],res['took']))
            return [hit['_source'] for hit in res['hits']['hits']]
        else:
            res = es.search(index=index_name,
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