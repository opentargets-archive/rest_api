import urllib2
from flask import current_app
from flask.ext import restful
from elasticsearch import helpers
from datetime import datetime
import ujson as json


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

    def get(self, ensemblid ):
        es = current_app.extensions['elasticsearch']
        index_name = current_app.config['ELASTICSEARCH_DATA_INDEX_NAME']
        res = es.search(index=index_name,
                doc_type='evidence',
                body={'query': {
                        'match': {
                            'biological_subject.about': 'ensembl:'+ensemblid}
                        },
                      'size':100
                      }
            )
        print("Got %d Hits in %ims"%(res['hits']['total'],res['took']))
        return [hit['_source'] for hit in res['hits']['hits']]


class AvailableGenes(restful.Resource):

    def get(self):
        startdate = datetime.now()
        es = current_app.extensions['elasticsearch']
        index_name = current_app.config['ELASTICSEARCH_DATA_INDEX_NAME']
        # res = helpers.scan(client = es,
        #              query = {'filter': {
        #                                 'prefix': {
        #                                     'biological_subject.about': 'ensembl:'}
        #                                 },
        #                                 'size':10000
        #                      },
        #              scroll = '1m',
        #              doc_type='evidence',
        #              timeout="1m"
        #              )

        res = helpers.scan(client = es,
                     query = {'filter': {
                                        'prefix': {
                                            'biological_subject.about': 'ensembl:'}
                                        },
                              'size' : 1000,
                              'fields': ['biological_subject.about'],
                             },
                     scroll = '10m',
                     doc_type='evidence',
                     timeout="10m"
                     )

        # res = es.search(index=index_name,
        #     doc_type='evidence',
        #     body={'query': {
        #             'wildcard': {
        #                 'biological_subject.about': 'ensembl:*'}
        #             },
        #           'size':1000000
        #           }
        #    )
        # print("Got %d Hits in %ims"%(res['hits']['total'],res['took']))

        available_genes = []
        for hit in res:
            available_genes.append(hit['fields']['biological_subject.about'][0].split('ensembl:')[1])
        available_genes = sorted(list(set(available_genes)))
        print "%i gene(s) found and returned in %ims"%(len(available_genes),int(round((datetime.now()-startdate).total_seconds()*1000)))
        return available_genes



class EfficientAvailableGenes(restful.Resource):

    def get(self):
        startdate = datetime.now()
        search_url = '''http://localhost:9200/test-arrayexpress-data-schemaless/evidence/_search?{"filter":{"prefix":{"biological_subject.about":"ensembl:"}},"size":100000}'''
        res = json.load(urllib2.urlopen(search_url))
        print("Done in %ims"%(int(round((datetime.now()-startdate).total_seconds()*1000))))

        available_genes = []
        for hit in res['hits']['hits']:
            available_genes.append(hit['_source']['biological_subject']['about'].split('ensembl:')[1])
        available_genes = sorted(list(set(available_genes)))

        return available_genes


