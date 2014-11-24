from collections import defaultdict
from flask import current_app
import ujson as json
from dicttoxml import dicttoxml
import csv
from StringIO import StringIO
from elasticsearch import helpers
import operator
from app.common.responses import ResponseType
from app.common.requests import OutputDataStructureOptions


__author__ = 'andreap'


class esQuery():

    def __init__(self,
                 handler,
                 index_data = None,
                 index_mapping = None,
                 index_efo = None,
                 index_eco = None,
                 index_genename = None,
                 log_level="DEBUG"):
        '''

        :param handler: initialized ElasticSearch official python client
        :param index_data:
        :param index_mapping:
        :param index_efo:
        :param index_eco:
        :param index_genename:
        :param log_level:
        :return:
        '''

        self.handler= handler
        self._index_data = index_data
        self._index_mapping = index_mapping
        self._index_efo = index_efo
        self._index_eco = index_eco
        self._index_genename = index_genename




    def get_evidences_for_gene(self, gene, **kwargs):
        params = SearchParams(**kwargs)
        if gene.startswith('ENSG'): #retrieve from ensembl code
            res = self.handler.search(index=self._index_data,
                    doc_type='evidence',
                    body={'query': {
                            'match': {
                                'biological_subject.about': 'ensembl:'+gene}
                            },
                          'size':params.size,
                          'from':params.start_from,
                          '_source': OutputDataStructureOptions.getSource(params.datastructure)
                          }
                )
        else: #search by name
             res = self.handler.search(index=self._index_data,
                    doc_type='evidence',
                    body={'query': {
                            'match': {
                                'biological_subject.about': 'ensembl:'+gene}
                            },
                          'size':params.size,
                          'from':params.start_from,
                          '_source': OutputDataStructureOptions.getSource(params.datastructure)
                          }
                )

        current_app.logger.debug("Got %d Hits in %ims"%(res['hits']['total'],res['took']))

        return PaginatedResult(res,params)

    def free_text_search(self, searchphrase, **kwargs):
        searchphrase = searchphrase.lower()
        if "*" not in searchphrase:
            params = SearchParams(**kwargs)
            searchphrase ='* '.join(searchphrase.split())
            res = self.handler.search(index=[self._index_efo,
                                             self._index_genename],
                    doc_type=['efolabel','genename'],
                    body={'query': {
                            'fuzzy': {
                                '_all' : searchphrase}
                            },
                          'size' : params.size,
                          'from' : params.start_from,
                          '_source': OutputDataStructureOptions.getSource(params.datastructure)
                          }
                )
            current_app.logger.debug("Got %d Hits in %ims"%(res['hits']['total'],res['took']))
            data =[]
            for hit in res['hits']['hits']:
                datapoint = dict(type = hit['_type'],
                                            data = hit['_source'],
                                            id =  hit['_id'],
                                            score =  hit['_score'])
                if hit['_type'] == 'genename':
                    datapoint['title'] = hit['_source']['Associated Gene Name']
                    datapoint['description'] = hit['_source']['Description']
                elif hit['_type'] == 'efolabel':
                    datapoint['title'] = hit['_source']['label']
                    datapoint['description'] = hit['_source']['efoid']
                data.append(datapoint)
            return PaginatedResult(res, params, data)


    def _get_ensemblid_from_gene_name(self,genename, **kwargs):
        res = self.handler.search(index=self._index_genename,
                    doc_type='genename',
                    body={'query': {
                            'match': {"Associated Gene Name":genename}

                            },
                          'size':1,
                          'fields': ['Ensembl Gene ID']
                          }
                )
        current_app.logger.debug("Got %d gene id  Hits in %ims"%(res['hits']['total'],res['took']))
        return res['hits']['hits']

    def available_genes(self, **kwargs):
        params = SearchParams(**kwargs)
        res = helpers.scan(client = self.handler,
                             # query = {'filter': {
                             #                    'prefix': {
                             #                        'biological_subject.about': 'ensembl:'},
                             #                    },
                            query = {"query" : {"match_all" : {}},

                                  'size' : 1000,
                                  'fields': ['biological_subject.about'],
                                 },
                             scroll = '10m',
                             doc_type='evidence',
                             timeout="10m",
                            )

        available_genes  = defaultdict(int)
        for hit in res:
            gene_name = hit['fields']['biological_subject.about'][0]
            if gene_name.startswith('ensembl:'):
                gene_name = gene_name.split('ensembl:')[1]
            available_genes[gene_name] += 1
        #do this trough es api like this:
        # "aggs" = {
        #            "sport_count": {
        #                "value_count": {
        #                  "field": "sport"
        #                      }
        #                 }
        #           }
        available_genes = available_genes.items()
        available_genes.sort(key=operator.itemgetter(1), reverse=True)

        current_app.logger.debug("Got a total of %i genes with %i evidences"%(len(available_genes),sum((e for g,e in available_genes))))
        return available_genes


    def get_ensemblid_from_uniprotid(self, uniprotid, **kwargs):
        res = self.handler.search(index=self._index_mapping,
                    doc_type='mapping',
                    body={'query': {
                                    "match" : {'uniprot_accession': uniprotid}

                                    }

                        }
                )
        if res['hits']['hits']:
            for hit in res['hits']['hits']:
                return  hit['_source']['ensembl_gene_id']
        return

    def get_uniprotid_from_ensemblid(self, ensembleid, **kwargs):
        res = self.handler.search(index=self._index_mapping,
                    doc_type='mapping',
                    body={'query': {
                            'match': {
                                'ensembl_gene_id': ensembleid}
                            },
                          }
                )
        if res['hits']['hits']:
            for hit in res['hits']['hits']:
                return  hit['_source']['uniprot_accession']
        return

    def get_efo_label_from_code(self, code, **kwargs):
        res = self.handler.search(index=self._index_efo,
                doc_type='efolabel',
                body={'query': {
                        'match': {
                            'efoid': '*'+code}
                        },
                      'size':1

                }
            )
        if res['hits']['total']:
            for hit in res['hits']['hits']:
                return hit['_source']['label']


    def get_efo_code_from_label(self, label, **kwargs):
        res = self.handler.search(index=self._index_efo,
                doc_type='efolabel',
                body={'query': {
                        'match': {
                            'label': label}
                        },
                      'size':100
                }
            )
        if res['hits']['total']:
            return [hit['_source']['efoid'] for hit in res['hits']['hits']]

    def get_evidences_with_efo_code_as_object(self, efocode, **kwargs):
        if not efocode.startswith('efo:'):#temporary workaround
            efocode= 'efo:'+efocode

        params = SearchParams(**kwargs)

        res = self.handler.search(
                            index=self._index_data,
                            doc_type='evidence',
                            body={"query" : {"match" : {'biological_object.about': efocode}},
                                  'size' : params.size,
                                  'from' : params.start_from,
                                  '_source': OutputDataStructureOptions.getSource(params.datastructure)
                                },
                            timeout="1m",
                             )


        return  PaginatedResult(res,params)

    def get_evidences_by_id(self, evidenceid, **kwargs):

        if isinstance(evidenceid, str):
            evidenceid=[evidenceid]


        res = self.handler.search(index=self._index_data,
                doc_type='evidence',
                body={'filter': {
                                "ids" : {
                                        "type" : "evidence",
                                        "values" : evidenceid
                                        }
                                }
                }
            )
        if res['hits']['total']:
                return [ hit['_source'] for hit in res['hits']['hits']]

    def get_label_for_eco_code(self, code):
        res = self.handler.search(index=self._index_eco,
                doc_type='eco',
                body={'filter': {
                                "ids" : {
                                        "type" : "eco",
                                        "values" : [code]
                                        }
                                }
                }
            )
        for hit in res['hits']['hits']:
            return hit['_source']

    def get_evidences_for_gene_and_efo(self, geneid, efoid, **kwargs):
        params = SearchParams(**kwargs)
        res = self.handler.search(
            index=self._index_data,
            doc_type='evidence',
            body={"query" : {
                      "bool" : {
                        "must" : {
                             "match" : {'biological_subject.about': 'ensembl:'+geneid},
                             "match" : {'biological_object.about': efoid},
                            }
                        }
                    },
                  'size' : params.size,
                  'from' : params.start_from,
                  '_source': OutputDataStructureOptions.getSource(params.datastructure)
                },
            timeout="1m",
            )
        current_app.logger.debug("Got %d Hits in %ims"%(res['hits']['total'],res['took']))
        return PaginatedResult(res,params)





class SearchParams():

    _max_search_result_limit = 1000
    _default_return_size = 10
    _allowed_groupby = ['gene','evidence-type']


    def __init__(self, **kwargs):

        self.size = kwargs.get('size', self._default_return_size) or self._default_return_size
        if (self.size> self._max_search_result_limit) :
            self.size = self._max_search_result_limit

        self.start_from = kwargs.get('from', 0) or 0

        groupby = kwargs.get('groupby')
        if groupby:
            if groupby not in self._allowed_groupby:
                groupby = None
        self.groupby = groupby

        self.orderby = kwargs.get('orderby')

        self.gte = kwargs.get('gte')

        self.lt = kwargs.get('lt')

        self.format = kwargs.get('format', 'json') or 'json'

        self.datastructure = kwargs.get('datastructure', 'full') or 'full'




class Result():

    format = ResponseType.JSON

    def toDict(self):
        raise NotImplementedError

    def __str__(self):
        if self.format == ResponseType.JSON:
            return self.toJSON()
        elif self.format == ResponseType.XML:
            return self.toXML()
        elif self.format == ResponseType.CSV:
            return self.toCSV()

    def toJSON(self):
        return json.dumps(self.toDict())
    def toXML(self):
        return dicttoxml(self.toDict(), custom_root='cttv-api-result')
    def toCSV(self):
        output = StringIO()
        if self.data is None:
            self.toDict()#populate data if empty
        if isinstance(self.data[0], dict):
            keys = self.data[0].keys()
            writer = csv.DictWriter(output, keys)
            writer.writeheader()
            for row in self.data:
                d = {}
                for k,v in row.items():
                    if k in keys:
                        if isinstance(k,str):
                            d[k] = v
                        else:
                            d[k]=json.dumps(v)
                writer.writerow(d)
        if isinstance(self.data[0], list):
            writer = csv.writer(output)
            for row in self.data:
                l = []
                for i in row:
                    if isinstance(i, str):
                        l.append(i)
                    else:
                        l.append(json.dumps(i))
                writer.writerow(l)
        return output.getvalue()

class PaginatedResult(Result):

    def __init__(self, res, params, data = None):
        '''

        :param res: elasticsearch query response
        :param params: get parameters
        :param data: data to display, use only to override default representation
        :param data_structure: a type of OutputDataStructureOptions
        '''

        self.res = res
        self.params = params
        self.data = data
        self.format = params.format

    def toDict(self):

        if self.data is None:
            if self.params.datastructure == OutputDataStructureOptions.COUNT:
                 return {'total' :self.res['hits']['total'],
                         'took' : self.res['took']
                        }
            else:
                self.data = [hit['_source'] for hit in self.res['hits']['hits']]
        return {'data' : self.data,
                'total' :self.res['hits']['total'],
                'took' : self.res['took'],
                'size' : self.params.size,
                'from' : self.params.start_from
                }

