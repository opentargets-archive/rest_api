from collections import defaultdict
from copy import copy

import operator
import logging
import pprint

from flask import current_app
from elasticsearch import helpers
from pythonjsonlogger import jsonlogger
from app.common.request_templates import OutputDataStructureOptions
from app.common.results import PaginatedResult, SimpleResult, CountedResult
from app.common.datatypes import FilterTypes

__author__ = 'andreap'


class BooleanFilterOperator():
    AND = 'must'
    OR = 'should'
    NOT = 'must_not'


class FreeTextFilterOptions():
    ALL = 'all'
    GENE = 'gene'
    EFO = 'efo'


class esQuery():
    def __init__(self,
                 handler,
                 datatypes,
                 datatource_scoring,
                 index_data=None,
                 index_efo=None,
                 index_eco=None,
                 index_genename=None,
                 index_expression=None,
                 index_reactome=None,
                 docname_data=None,
                 docname_efo=None,
                 docname_eco=None,
                 docname_genename=None,
                 docname_expression=None,
                 docname_reactome=None,
                 log_level=logging.DEBUG):
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

        self.handler = handler
        self._index_data = index_data
        self._index_efo = index_efo
        self._index_eco = index_eco
        self._index_genename = index_genename
        self._index_expression = index_expression
        self._index_reactome = index_reactome
        self._docname_data = docname_data
        self._docname_efo = docname_efo
        self._docname_eco = docname_eco
        self._docname_genename = docname_genename
        self._docname_expression = docname_expression
        self._docname_reactome = docname_reactome
        self.datatypes = datatypes
        self.datatource_scoring = datatource_scoring


        if log_level == logging.DEBUG:
            formatter = jsonlogger.JsonFormatter()
            es_logger = logging.getLogger('elasticsearch')
            for handler in es_logger.handlers:
                handler.setFormatter(formatter)
            es_logger.setLevel(logging.WARNING)
            es_tracer = logging.getLogger('elasticsearch.trace')
            es_tracer.setLevel(logging.WARNING)
            # es_tracer.addHandler(logging.FileHandler('es_trace.log'))
            for handler in es_tracer.handlers:
                handler.setFormatter(formatter)


    def get_evidences_for_gene(self, gene, **kwargs):
        params = SearchParams(**kwargs)
        if params.datastructure == OutputDataStructureOptions.DEFAULT:
            params.datastructure = OutputDataStructureOptions.FULL
        res = self.handler.search(index=self._index_data,
                                  # doc_type=self._docname_data,
                                  body={
                                      "query": {
                                          "filtered": {
                                              "query": {
                                                  "match_all": {}
                                              },
                                              "filter": {
                                                  "terms": {
                                                      "target.id": self._get_gene_filter(gene)

                                                  }
                                              }
                                          }
                                      },
                                      'size': params.size,
                                      'from': params.start_from,
                                      '_source': OutputDataStructureOptions.getSource(params.datastructure)
                                  }
        )

        if res['hits']['total'] == 0:  # search by name
            ensemblid = self._get_ensemblid_from_gene_name(gene)
            if ensemblid:
                ensemblid = ensemblid[0]
                res = self.handler.search(index=self._index_data,
                                          # doc_type=self._docname_data,
                                          body={
                                              "query": {
                                                  "filtered": {
                                                      "query": {
                                                          "match_all": {}
                                                      },
                                                      "filter": {
                                                          "term": {
                                                              "target.id":
                                                                  "http://identifiers.org/ensembl/" + ensemblid,


                                                          }
                                                      }
                                                  }
                                              },
                                              'size': params.size,
                                              'from': params.start_from,
                                              '_source': OutputDataStructureOptions.getSource(params.datastructure)
                                          }
                )

        current_app.logger.debug("Got %d Hits in %ims" % (res['hits']['total'], res['took']))

        return PaginatedResult(res, params)

    def free_text_search(self, searchphrase,
                         filter=FreeTextFilterOptions.ALL,
                         **kwargs):
        '''
        Multiple types of fuzzy search are supported by elasticsearch and the differences can be confusing. The list
        below attempts to disambiguate these various types.

        match query + fuzziness option: Adding the fuzziness parameter to a match query turns a plain match query
        into a fuzzy one. Analyzes the query text before performing the search.
        fuzzy query: The elasticsearch fuzzy query type should generally be avoided. Acts much like a term query.
        Does not analyze the query text first.
        fuzzy_like_this/fuzzy_like_this_field: A more_like_this query, but supports fuzziness, and has a tuned
        scoring algorithm that better handles the characteristics of fuzzy matched results.*
        suggesters: Suggesters are not an actual query type, but rather a separate type of operation (internally
        built on top of fuzzy queries) that can be run either alongside a query, or independently. Suggesters are
        great for 'did you mean' style functionality.

        :param searchphrase:
        :param filter:
        :param kwargs:
        :return:
        '''
        searchphrase = searchphrase.lower()
        params = SearchParams(**kwargs)
        if filter.lower() == FreeTextFilterOptions.ALL:
            doc_types = [self._docname_efo, self._docname_genename]
        elif filter.lower() == FreeTextFilterOptions.GENE:
            doc_types = [self._docname_genename]
        elif filter.lower() == FreeTextFilterOptions.EFO:
            doc_types = [self._docname_efo]
        res = self.handler.search(index=[self._index_efo,
                                         self._index_genename],
                                  doc_type=doc_types,
                                  body={'query':{
                                           'filtered': {
                                               'query': self._get_free_text_query(searchphrase),
                                               'filter': {
                                                   # "not":{ "term": { "biotype": 'processed_pseudogene' }},
                                                   # "not":{ "term": { "biotype": 'antisense' }},
                                                   # "not":{ "term": { "biotype": 'unprocessed_pseudogene' }},
                                                   # "not":{ "term": { "biotype": 'lincRNA' }},
                                                   # "not":{ "term": { "biotype": 'transcribed_unprocessed_pseudogene' }},
                                                   # "not":{ "term": { "biotype": 'transcribed_processed_pseudogene' }},
                                                   # "not":{ "term": { "biotype": 'sense_intronic' }},
                                                   # "not":{ "term": { "biotype": 'processed_transcript' }},
                                                   # "not":{ "term": { "biotype": 'IG_V_pseudogene' }},
                                                   # "not":{ "term": { "biotype": 'miRNA' }},
                                                  }
                                               }
                                           },
                                        'size': params.size,
                                        'from': params.start_from,
                                        '_source': OutputDataStructureOptions.getSource(
                                            OutputDataStructureOptions.GENE_AND_DISEASE),
                                        # "min_score": 0.,
                                        "highlight": {
                                            "fields": {
                                                "label": {},
                                                "symbol_synonyms": {},
                                                "efo_synonyms": {},
                                                "biotype": {},
                                                "id": {},
                                                "approved_symbol": {},
                                                "approved_name": {},
                                                "name_synonyms": {},
                                                "gene_family_description": {},
                                                "uniprot_accessions": {},
                                                "hgnc_id": {},
                                                "ensembl_gene_id": {},
                                                }
#                                              },
#                                         "script_fields" : {
#                                             "gene_synonyms" : {
#                                                 "script" : """
# if (len(doc['ensembl_gene_id']) > 0){
#     return doc['synonyms'].value
#     }
# return ""
# """
#                                                 }
                                            },
                                        },

                                )
        current_app.logger.debug("Got %d Hits in %ims" % (res['hits']['total'], res['took']))
        data = []
        for hit in res['hits']['hits']:
            highlight=''
            if 'highlight' in hit:
                highlight = hit['highlight']
            datapoint = dict(type=hit['_type'],
                             data=hit['_source'],
                             id=hit['_id'],
                             score=hit['_score'],
                             highlight=highlight)
            if hit['_type'] == self._docname_genename:
                datapoint['title'] = hit['_source']['approved_symbol']
                datapoint['description'] = hit['_source']['approved_name'].split('[')[0]
            elif hit['_type'] == self._docname_efo:
                datapoint['title'] = hit['_source']['label']
                datapoint['description'] = hit['_source']['definition']
            data.append(datapoint)
        return PaginatedResult(res, params, data)


    def quick_search(self, searchphrase,
                            filter=FreeTextFilterOptions.ALL,
                            **kwargs):
        '''
        Multiple types of fuzzy search are supported by elasticsearch and the differences can be confusing. The list
        below attempts to disambiguate these various types.

        match query + fuzziness option: Adding the fuzziness parameter to a match query turns a plain match query
        into a fuzzy one. Analyzes the query text before performing the search.
        fuzzy query: The elasticsearch fuzzy query type should generally be avoided. Acts much like a term query.
        Does not analyze the query text first.
        fuzzy_like_this/fuzzy_like_this_field: A more_like_this query, but supports fuzziness, and has a tuned
        scoring algorithm that better handles the characteristics of fuzzy matched results.*
        suggesters: Suggesters are not an actual query type, but rather a separate type of operation (internally
        built on top of fuzzy queries) that can be run either alongside a query, or independently. Suggesters are
        great for 'did you mean' style functionality.

        :param searchphrase:
        :param filter:
        :param kwargs:
        :return:
        '''

        def format_datapoint(hit):
            highlight = ''
            if 'highlight' in hit:
                highlight=hit['highlight']
            datapoint = dict(type=hit['_type'],
                             id=hit['_id'],
                             score=hit['_score'],
                             highlight = highlight)
            datapoint.update(hit['_source'])
            if hit['_type'] == self._docname_genename:
                returned_ids['genes'].append(hit['_id'])
            elif hit['_type'] == self._docname_efo:
                returned_ids['efo'].append(hit['_id'])

            return datapoint


        searchphrase = searchphrase.lower()
        params = SearchParams(**kwargs)

        data = dict(besthit=None,
                    genes=[],
                    efo=[])
        returned_ids = dict(genes=[],
                            efo=[])

        res = self.handler.search(index=[self._index_efo,
                                         self._index_genename],
                                  doc_type=[self._docname_efo, self._docname_genename],
                                  body={'query':{
                                           'filtered': {
                                               'query': self._get_free_text_query(searchphrase),
                                               'filter': {
                                                   # "bool": {
                                                   #      # "must": { "range": { "created": { "gte": "now - 1d / d" }}},
                                                   #      # "should": [
                                                   #      #   { "term": { "featured": true }},
                                                   #      #   { "term": { "starred":  true }}
                                                   #      # ],
                                                   #      "must_not": [
                                                   #          { "term": { "biotype": 'processed_pseudogene' }},
                                                   #          { "term": { "biotype": 'antisense' }},
                                                   #          { "term": { "biotype": 'unprocessed_pseudogene' }},
                                                   #          { "term": { "biotype": 'lincRNA' }},
                                                   #          { "term": { "biotype": 'transcribed_unprocessed_pseudogene' }},
                                                   #          { "term": { "biotype": 'transcribed_processed_pseudogene' }},
                                                   #          { "term": { "biotype": 'sense_intronic' }},
                                                   #          { "term": { "biotype": 'processed_transcript' }},
                                                   #          { "term": { "biotype": 'IG_V_pseudogene' }},
                                                   #          { "term": { "biotype": 'miRNA' }},
                                                   #      ],
                                                   #    },
                                                   }
                                               }
                                           },
                                        'size': 30,
                                        '_source': OutputDataStructureOptions.getSource(
                                            OutputDataStructureOptions.GENE_AND_DISEASE),
                                        # "min_score": 0.,
                                         "highlight": {
                                            "fields": {
                                                "label": {},
                                                "symbol_synonyms": {},
                                                "efo_synonyms": {},
                                                "biotype": {},
                                                "id": {},
                                                "approved_symbol": {},
                                                "approved_name": {},
                                                "name_synonyms": {},
                                                "gene_family_description": {},
                                                "uniprot_accessions": {},
                                                "hgnc_id": {},
                                                "ensembl_gene_id": {},

                                            }
                                         }
                                  }
        )

        if ('hits' in res) and res['hits']['total']:
            '''handle best hit'''
            best_hit = res['hits']['hits'][0]
            data['besthit'] = format_datapoint(best_hit)

            ''' store the other results in the corresponding object'''
            for hit in res['hits']['hits'][1:]:
                if hit['_type'] == self._docname_genename:
                    if len(data['genes']) < params.size:
                        data['genes'].append(format_datapoint(hit))
                elif hit['_type'] == self._docname_efo:
                    if len(data['efo']) < params.size:
                        data['efo'].append(format_datapoint(hit))
            '''if there are not enough fill the results for both the categories'''

            if len(data['genes']) < params.size:
                res_genes = self.handler.search(index=self._index_genename,
                                                doc_type=self._docname_genename,
                                                body={'query':{
                                                         'filtered': {
                                                             'query': self._get_free_text_gene_query(searchphrase),
                                                             # 'filter': {
                                                             #
                                                             #            "not":{ "term": { "biotype": 'processed_pseudogene' }},
                                                             #                { "term": { "biotype": 'antisense' }},
                                                             #                { "term": { "biotype": 'unprocessed_pseudogene' }},
                                                             #                { "term": { "biotype": 'lincRNA' }},
                                                             #                { "term": { "biotype": 'transcribed_unprocessed_pseudogene' }},
                                                             #                { "term": { "biotype": 'transcribed_processed_pseudogene' }},
                                                             #                { "term": { "biotype": 'sense_intronic' }},
                                                             #                { "term": { "biotype": 'processed_transcript' }},
                                                             #                { "term": { "biotype": 'IG_V_pseudogene' }},
                                                             #                { "term": { "biotype": 'miRNA' }},
                                                             #                                                                                        ],
                                                             #
                                                             #       }
                                                             }
                                                         },
                                                      'size': params.size + 1,
                                                      '_source': OutputDataStructureOptions.getSource(
                                                          OutputDataStructureOptions.GENE),
                                                      # "min_score": 0.,
                                                      "highlight": {
                                                        "fields": {
                                                            "symbol_synonyms": {},
                                                            "biotype": {},
                                                            "id": {},
                                                            "approved_symbol": {},
                                                            "approved_name": {},
                                                            "name_synonyms": {},
                                                            "gene_family_description": {},
                                                            "uniprot_accessions": {},
                                                            "hgnc_id": {},
                                                            "enselbl_gene_id": {},
                                                        }
                                                     }
                                                }
                )
                current_app.logger.debug(
                    "Got %d additional Gene Hits in %ims" % (res_genes['hits']['total'], res['took']))
                for hit in res_genes['hits']['hits']:
                    if len(data['genes']) < params.size:
                        if hit['_id'] not in returned_ids['genes']:
                            data['genes'].append(format_datapoint(hit))

            if len(data['efo']) < params.size:
                res_efo = self.handler.search(index=self._index_efo,
                                              doc_type=self._docname_efo,
                                              body={'query': self._get_free_text_efo_query(searchphrase),
                                                    'size': params.size + 1,
                                                    '_source': OutputDataStructureOptions.getSource(
                                                        OutputDataStructureOptions.DISEASE),
                                                    # "min_score": 0.,
                                                    "highlight": {
                                                        "fields": {
                                                            "label": {},
                                                            "efo_synonyms": {},
                                                            "biotype": {},
                                                            "id": {},
                                                            "approved_symbol": {},
                                                            "approved_name": {},
                                                            "gene_family_description": {},
                                                            "uniprot_accessions": {},
                                                            "hgnc_id": {},
                                                            "enselbl_gene_id": {},
                                                        }
                                                     }
                                              }
                )
                current_app.logger.debug("Got %d additional EFO Hits in %ims" % (res_efo['hits']['total'], res['took']))
                for hit in res_efo['hits']['hits']:
                    if len(data['efo']) < params.size:
                        if hit['_id'] not in returned_ids['efo']:
                            data['efo'].append(format_datapoint(hit))

        return SimpleResult(None, params, data)

    def autocomplete(self,
                     searchphrase,
                     **kwargs):

        searchphrase = searchphrase.lower()
        params = SearchParams(**kwargs)


        res_gene = self.handler.suggest(index=[self._index_genename],
                                  body={"suggest":{
                                            "text" : searchphrase,
                                              "completion" : {
                                                "field" : "_private.suggestions"
                                              }
                                            }
                                        }
        )

        res_efo = self.handler.suggest(index=[self._index_efo],
                                  body={"suggest":{
                                            "text" : searchphrase,
                                              "completion" : {
                                                "field" : "_private.suggestions"
                                              }

                                            }
                                        }
        )
        # current_app.logger.debug("Got %d Hits in %ims" % (res['hits']['total'], res['took']))
        data = dict(gene =[], efo=[])
        if 'suggest' in res_gene:
            data['gene'] = res_gene['suggest'][0]['options']
        if 'suggest' in res_efo:
            data['efo'] = res_efo['suggest'][0]['options']

        return SimpleResult(None, params, data)

    def _get_ensemblid_from_gene_name(self, genename, **kwargs):
        res = self.handler.search(index=self._index_genename,
                                  doc_type=self._docname_genename,
                                  body={'query': {
                                      'match': {"Associated Gene Name": genename}

                                  },
                                        'size': 1,
                                        'fields': ['Ensembl Gene ID']
                                  }
        )
        current_app.logger.debug("Got %d gene id  Hits in %ims" % (res['hits']['total'], res['took']))
        return [hit['fields']['Ensembl Gene ID'][0] for hit in res['hits']['hits']]

    def available_genes(self, **kwargs):
        params = SearchParams(**kwargs)
        res = helpers.scan(client=self.handler,
                           # query = {'filter': {
                           # 'prefix': {
                           #                        'target.id': 'ensembl:'},
                           #                    },
                           query={"query": {"match_all": {}},

                                  'size': 1000,
                                  'fields': ['target.id'],
                           },
                           scroll='10m',
                           # doc_type=self._docname_data,
                           index=self._index_data,
                           timeout="10m",
        )

        available_genes = defaultdict(int)
        for hit in res:
            gene_name = hit['fields']['target.id'][0]
            if gene_name.startswith('ensembl:'):
                gene_name = gene_name.split('ensembl:')[1]
            available_genes[gene_name] += 1
        # do this trough es api like this:
        # "aggs" = {
        #            "sport_count": {
        #                "value_count": {
        #                  "field": "sport"
        #                      }
        #                 }
        #           }
        available_genes = available_genes.items()
        available_genes.sort(key=operator.itemgetter(1), reverse=True)

        current_app.logger.debug(
            "Got a total of %i genes with %i evidences" % (len(available_genes), sum((e for g, e in available_genes))))
        return available_genes


    def get_gene_info(self,gene_ids, facets = False, **kwargs):
        params = SearchParams(**kwargs)
        if params.datastructure == OutputDataStructureOptions.DEFAULT:
            params.datastructure = OutputDataStructureOptions.FULL
        source_filter = OutputDataStructureOptions.getSource(params.datastructure)
        if params.fields:
            source_filter["include"]= params.fields
        aggs = {}
        if facets:
            aggs = self._get_gene_info_agg()

        if gene_ids:
            res = self.handler.search(index=self._index_genename,
                                      doc_type=self._docname_genename,
                                      body={"query": {
                                              "filtered": {
                                                  # "query": {
                                                  #     "match_all": {}
                                                  # },
                                                  "filter": {
                                                      "ids": {
                                                          "values": gene_ids

                                                         }
                                                    }
                                                }
                                            },

                                           '_source': source_filter,
                                           'size': params.size,
                                           'from': params.start_from,
                                           'aggs':  aggs,

                                           }
                                      )
            return PaginatedResult(res, params)




    def get_efo_info_from_code(self, efo_codes, **kwargs):
        params = SearchParams(**kwargs)
        if efo_codes:
            res = self.handler.search(index=self._index_efo,
                                      doc_type=self._docname_efo,
                                      body={'filter': {
                                          "ids": {
                                              "values": [efo_codes]
                                                },
                                            },
                                            'size' : 100000
                                      }
            )
            if res['hits']['total']:
                if res['hits']['total']==1:
                    return [res['hits']['hits'][0]['_source']]
                else:
                    return [hit['_source'] for hit in res['hits']['hits']]


    def get_evidences_with_efo_code_as_object(self, efocode, **kwargs):
        if not efocode.startswith('efo:'):  # temporary workaround
            efocode = 'efo:' + efocode

        params = SearchParams(**kwargs)
        if params.datastructure == OutputDataStructureOptions.DEFAULT:
            params.datastructure = OutputDataStructureOptions.FULL

        res = self.handler.search(index=self._index_data,
                                  # doc_type=self._docname_data,
                                  body={
                                      "query": {
                                          "filtered": {
                                              "query": {
                                                  "match_all": {}
                                              },
                                              "filter": {
                                                  "term": {
                                                      "disease.id": efocode

                                                  }
                                              }
                                          }
                                      },
                                      'size': params.size,
                                      'from': params.start_from,
                                      '_source': OutputDataStructureOptions.getSource(params.datastructure)
                                  },
                                  timeout="1m",
        )

        return PaginatedResult(res, params)

    def get_evidences_by_id(self, evidenceid, **kwargs):

        if isinstance(evidenceid, str):
            evidenceid = [evidenceid]

        params = params = SearchParams(**kwargs)
        if params.datastructure == OutputDataStructureOptions.DEFAULT:
            params.datastructure = OutputDataStructureOptions.FULL

        res = self.handler.search(index=self._index_data,
                                  # doc_type=self._docname_data,
                                  body={'filter': {
                                      "ids": {
                                          # "type": self._docname_data,
                                          "values": evidenceid
                                      }
                                  }
                                  }
        )
        if res['hits']['total']:
            return [hit['_source'] for hit in res['hits']['hits']]

    def get_label_for_eco_code(self, code):
        res = self.handler.search(index=self._index_eco,
                                  doc_type=self._docname_eco,
                                  body={'filter': {
                                      "ids": {
                                          "type": "eco",
                                          "values": [code]
                                      }
                                  }
                                  }
        )
        for hit in res['hits']['hits']:
            return hit['_source']

    def get_evidences(self,
                      genes=[],
                      objects=[],
                      evidence_types=[],
                      datasources = [],
                      gene_operator='OR',
                      object_operator='OR',
                      evidence_type_operator='OR',
                      **kwargs):
        params = SearchParams(**kwargs)
        if params.datastructure == OutputDataStructureOptions.DEFAULT:
            params.datastructure = OutputDataStructureOptions.FULL
        '''convert boolean to elasticsearch syntax'''
        gene_operator = getattr(BooleanFilterOperator, gene_operator.upper())
        object_operator = getattr(BooleanFilterOperator, object_operator.upper())
        evidence_type_operator = getattr(BooleanFilterOperator, evidence_type_operator.upper())
        '''create multiple condition boolean query'''
        conditions = []
        if genes:
            conditions.append(self._get_complex_gene_filter(genes, gene_operator))
        if objects:
            conditions.append(self._get_complex_object_filter(objects, object_operator, expand_efo=params.expand_efo))
        if evidence_types:
            conditions.append(self._get_complex_evidence_type_filter(evidence_types, evidence_type_operator))
        if datasources:
            conditions.append(self._get_complex_datasource_filter(datasources, BooleanFilterOperator.OR))
        if params.pathway:
            conditions.append(self._get_complex_pathway_filter(params.pathway, BooleanFilterOperator.OR))
        '''boolean query joining multiple conditions with an AND'''
        source_filter = OutputDataStructureOptions.getSource(params.datastructure)
        if params.fields:
            source_filter["include"]= params.fields
        if params.groupby:
            res = self.handler.search(index=self._index_data,
                                  # doc_type=self._docname_data,
                                  body={
                                      "query": {
                                          "filtered": {
                                              "filter": {
                                                  "bool": {
                                                      "must": conditions
                                                  }
                                              }

                                          }
                                      },
                                      'size': params.size,
                                      'from': params.start_from,
                                      '_source': OutputDataStructureOptions.getSource(OutputDataStructureOptions.COUNT),
                                      "aggs":{
                                          params.groupby[0]: {
                                             "terms": {
                                                 "field" : "disease.id",
                                                 'size': params.size,

                                             },
                                             "aggs": {
                                                "evidencestring": { "top_hits": { "_source": source_filter, "size": params.size }}
                                             }

                                          }
                                       }
                                  }
            )
        else:
            query_body = {
                          "query": {
                              "filtered": {
                                  "filter": {
                                      "bool": {
                                          "must": conditions
                                      }
                                  }

                              }
                          },
                          'size': params.size,
                          'from': params.start_from,
                          '_source': source_filter,
                      }
            res = self.handler.search(index=self._index_data,
                                      # doc_type=self._docname_data,
                                      body=query_body,

            )
        return PaginatedResult(res, params, )

        #     res = helpers.scan(client= self.handler,
        #                                     index=self._index_data,
        #                                     query={
        #                                       "query": {
        #                                           "filtered": {
        #                                               "filter": {
        #                                                   "bool": {
        #                                                       "must": conditions
        #                                                   }
        #                                               }
        #
        #                                           }
        #                                       },
        #                                       'size': params.size,
        #                                       'from': params.start_from,
        #                                       '_source': source_filter,
        #                                     },
        #                                     scroll= "1m",
        #                                     timeout="10m",
        #                        )
        #
        #
        #
        #
        # return PaginatedResult(None, params, data = [i for i in res])

    def get_associations(self,
                      genes=[],
                      objects=[],
                      gene_operator='OR',
                      object_operator='OR',
                      **kwargs):
        params = SearchParams(**kwargs)
        if params.datastructure == OutputDataStructureOptions.DEFAULT:
            params.datastructure = OutputDataStructureOptions.FLAT
        '''convert boolean to elasticsearch syntax'''
        gene_operator = getattr(BooleanFilterOperator, gene_operator.upper())
        object_operator = getattr(BooleanFilterOperator, object_operator.upper())
        '''create multiple condition boolean query'''
        aggs = None
        efo_with_data = []
        conditions = []
        filter_data_conditions = dict()

        if params.filters[FilterTypes.DATASOURCE] or \
                 params.filters[FilterTypes.DATATYPE]:
            requested_datasources = []
            if params.filters[FilterTypes.DATASOURCE]:
                requested_datasources.extend(params.filters[FilterTypes.DATASOURCE])
            if params.filters[FilterTypes.DATATYPE]:
                for datatype in params.filters[FilterTypes.DATATYPE]:
                    requested_datasources.extend(self.datatypes.get_datasources(datatype))
            requested_datasources = list(set(requested_datasources))
            filter_data_conditions[FilterTypes.DATASOURCE]=self._get_complex_datasource_filter(requested_datasources, BooleanFilterOperator.OR)
            # #datasources = '|'.join([".*%s.*"%x for x in requested_datasources])#this will match substrings
            # datasources = '|'.join(["%s"%x for x in requested_datasources])
        if params.filters[FilterTypes.PATHWAY]:
            filter_data_conditions[FilterTypes.PATHWAY]=self._get_complex_pathway_filter(params.filters[FilterTypes.PATHWAY], BooleanFilterOperator.OR)

        if objects:
            conditions.append(self._get_complex_object_filter(objects, object_operator, expand_efo = params.expand_efo))
            params.datastructure = OutputDataStructureOptions.FLAT#override datastructure as only flat is available
            aggs = self._get_efo_associations_agg(filters = filter_data_conditions, facets=params.facets)
        if genes:
            conditions.append(self._get_complex_gene_filter(genes, gene_operator))
            if not aggs:
                aggs = self._get_gene_associations_agg(filters = filter_data_conditions, facets=params.facets)
            if not params.expand_efo:
                full_conditions = copy(conditions)
                full_conditions.extend(filter_data_conditions.values())
                efo_with_data = self._get_efo_with_data(conditions = full_conditions)


        '''boolean query joining multiple conditions with an AND'''
        source_filter = OutputDataStructureOptions.getSource(params.datastructure)
        if params.fields:
            source_filter["include"]= params.fields

        res = self.handler.search(index=self._index_data,
                                  search_type="count",
                                  body={
                                      #restrict the set of datapoints using the target and disease ids
                                      "query": {
                                          "filtered": {
                                              "filter": {
                                                  "bool": {
                                                      "must": conditions
                                                  }
                                              }
                                          }
                                      },
                                      'size': 0,
                                      '_source': OutputDataStructureOptions.getSource(OutputDataStructureOptions.COUNT),
                                      # filter out the results as requested, this will not be applied to the aggregation
                                      "post_filter": {
                                          "bool": {
                                              "must": filter_data_conditions.values()
                                          }
                                       },
                                      # calculate aggregation using proper ad hoc filters
                                      "aggs": aggs,

                                      }
                                  )
        if (not res['hits']['total']) and \
                genes and objects:
            data = [{"evidence_count": 0,
                     "datatypes": [],
                     "association_score": 0,
                     "gene_id": genes[0],
                    }]
            return CountedResult(res,
                                 params,
                                 data,
                                 total = 0,
                                 facets = {},
                                 available_datatypes = self.datatypes.available_datatypes,
                                 )
        '''build data structure to return'''
        if objects:
            if params.datastructure == OutputDataStructureOptions.FLAT:
                data = self._return_association_data_structures_for_efos(res, "genes", filters = params.filters)
        elif genes:
            if params.datastructure == OutputDataStructureOptions.FLAT:
                data = self._return_association_data_structures_for_genes(res, "efo_codes", efo_with_data=efo_with_data, filters = params.filters)
            elif params.datastructure == OutputDataStructureOptions.TREE:
                data= self._return_association_data_structures_for_genes_as_tree(res, "efo_codes",  efo_with_data=efo_with_data, filters = params.filters)


        return CountedResult(res,
                             params, data['data'],
                             total = res['hits']['total'],
                             facets=data['facets'],
                             available_datatypes = self.datatypes.available_datatypes,
                             )



    def  _get_complex_gene_filter(self,
                                  genes,
                                  bol=BooleanFilterOperator.OR,
                                  ):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param genes: list of genes
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if genes:
            return {
                "bool": {
                    bol: [{
                              "terms": {
                                  "target.id": [gene]}
                          }
                          for gene in genes]
                }
            }
        return dict()


    def _get_complex_object_filter(self,
                                   objects,
                                   bol=BooleanFilterOperator.OR,
                                   expand_efo = False):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param objects: list of objects
        :param bol: boolean operator to use for combining filters
        :param expand_efo: search in the full efo parent list (True) or just direct links (False)
        :return: boolean filter
        '''
        if objects:
            if expand_efo:
                return {
                    "bool": {
                        bol : [{
                              "terms": {
                                "_private.efo_codes":[object]}
                          }
                          for object in objects]
                    }

                }
            else:
                return {
                    "bool": {
                        bol : [{
                              "terms": {
                                 "disease.id": [object]}
                          }
                          for object in objects]
                    }

                }


    def _get_complex_evidence_type_filter(self,
                                          evidence_types,
                                          bol=BooleanFilterOperator.OR):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param evidence_types: list of evidence types
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if evidence_types:
            return {
                "bool": {
                    bol: [{
                              "terms": {
                                  "evidence.evidence_codes": [evidence_type]}
                          }
                          for evidence_type in evidence_types]
                }
            }
        return dict()


    def _get_complex_datasource_filter(self, datasources, bol):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param evidence_types: list of dataasource strings
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if datasources:
            filters = []
            for datasource in datasources:
                # filters.append({ "terms": {"_private.datasource": [datasource]}})
                filters.append({ "terms": {"sourceID": [datasource]}})


            return {
                "bool": {
                    bol:filters
                }
            }
        return dict()


    def _get_complex_pathway_filter(self, pathway_codes, bol):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param pathway_codes: list of pathway_codes strings
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if pathway_codes:
            genes = self._get_genes_for_pathway_code(pathway_codes)
            if genes:
                return self._get_complex_gene_filter(genes, bol)
        return dict()

    def _get_free_text_query(self, searchphrase):
        return {"bool": {
                    "should": [
                        {"multi_match" : {
                            "query":    searchphrase,
                            "fields": [ "label^5",
                                        "efo_synonyms",
                                        "symbol_synonyms",
                                        "approved_symbol",
                                        "approved_name",
                                        "name_synonyms",
                                        "gene_family_description",
                                        ],
                            "analyzer" : 'standard',
                            # "fuzziness": "AUTO",
                            "tie_breaker": 0.1,
                            "type": "phrase_prefix",
                          }
                        },
                        {"multi_match" : {
                            "query":    searchphrase,
                            "fields": [ "label",
                                        "id",
                                        "approved_symbol^2",
                                        "symbol_synonyms^2",
                                        "name_synonyms",
                                        "uniprot_id",
                                        "uniprot_accessions",
                                        "hgnc_id",
                                        "ensembl_gene_id",
                                        ],
                            "analyzer" : 'keyword',
                            # "fuzziness": "AUTO",
                            # "tie_breaker": 0.1,
                            "type": "best_fields",
                          }
                        },
                        {"multi_match" : {
                            "query":    searchphrase,
                            "fields": [ "id",
                                        "approved_symbol",
                                        ],
                            "analyzer" : 'keyword',
                            "fuzziness": "AUTO",
                            # "tie_breaker": 0.1,
                            "type": "best_fields",
                          }
                        },
                    ]
                }
            }




    def _get_free_text_gene_query(self, searchphrase):
        return {"bool": {
                    "should": [
                        {"multi_match" : {
                            "query":    searchphrase,
                            "fields": [ "symbol_synonyms",
                                        "approved_name",
                                        "name_synonyms",
                                        "gene_family_description",
                                        ],
                            "analyzer" : 'standard',
                            # "fuzziness": "AUTO",
                            "tie_breaker": 0.1,
                            "type": "phrase_prefix",
                          }
                        },
                        {"multi_match" : {
                            "query":    searchphrase,
                            "fields": [ "id",
                                        "approved_symbol^2",
                                        "name_synonyms",
                                        "uniprot_id",
                                        "uniprot_accessions",
                                        "hgnc_id",
                                        "ensembl_gene_id",
                                        ],
                            "analyzer" : 'keyword',
                            # "fuzziness": "AUTO",
                            # "tie_breaker": 0.1,
                            "type": "best_fields",
                          }
                        }
                    ]
                }
            }


    def _get_free_text_efo_query(self, searchphrase):
         return {"bool": {
                    "should": [
                        {"multi_match" : {
                            "query":    searchphrase,
                            "fields": [ "label^5",
                                        "efo_synonyms",
                                        ],
                            "analyzer" : 'standard',
                            # "fuzziness": "AUTO",
                            "tie_breaker": 0.1,
                            "type": "phrase_prefix",
                          }
                        },
                        {"multi_match" : {
                            "query":    searchphrase,
                            "fields": [ "label",
                                        "id",
                                      ],
                            "analyzer" : 'keyword',
                            # "fuzziness": "AUTO",
                            # "tie_breaker": 0.1,
                            "type": "best_fields",
                          }
                        }
                    ]
                }
            }



    def _get_gene_associations_agg(self, expand_efo = True, filters = {}, facets = True):
        field = "disease.id"
        if expand_efo:
            field = "_private.efo_codes"

        aggs = {"data": {
                   "filter" :{
                       "bool": {
                           "must": filters.values(),
                        },
                   },
                   "aggs":{
                        "efo_codes": {
                           "terms": {
                               "field" : field,
                               'size': 100000,
                               "order": {
                                   "association_score.count": "desc"
                               }
                           },
                            "aggs":{
                                  "datatypes": {
                                     "terms": {
                                         # "field" : "_private.datatype",
                                         "field" : "sourceID",
                                         'size': 100000,
                                       },
                                     "aggs":{
                                          "association_score": {
                                             "stats": {
                                                 "script" : self._get_script_association_score_weighted()['script'],
                                             },

                                       }
                                    }
                                  },
                                  "association_score": {
                                             "stats": {
                                                 "script" : self._get_script_association_score_weighted()['script'],
                                             },

                                       }

                              }
                           # "aggs":{
                           #    "datasource": {
                           #       "terms": {
                           #           "field" : "sourceID",
                           #           'size': 100000,
                           #       },
                           #    }
                           # }
                         },
                    },
                },
         }
        if facets:
            aggs["datatypes"] = self._get_datatype_facet_aggregation(filters)
        return aggs

    def _get_efo_associations_agg(self, filters = {}, facets = True):
        # return {"genes": {
        #            "terms": {
        #                "field" : "target.id",
        #                'size': 100,
        #            },
        #            "aggs":{
        #               "datasource": {
        #                  "terms": {
        #                      "field" : "sourceID",
        #                      'size': 10000,
        #                  },
        #            }
        #          }
        #       }
        gene_related_aggs = self._get_gene_related_aggs(filters)


        aggs = {
            "data": {
               "filter" :{
                   "bool": {
                       "must": filters.values(),
                    }
,                           },
               "aggs":{
                   "genes": {
                       "terms": {
                           "field" : "target.id",
                           'size': 100000,
                           # "order": {
                           #     "association_score.count": "desc"
                           # }
                       },
                       "aggs":{

                          "datatypes": {
                             "terms": {
                                 # "field" : "_private.datatype",
                                 "field" : "sourceID",
                                 'size': 100000,
                             },
                             "aggs":{
                                  "association_score": {
                                     "stats": {
                                         "script" : self._get_script_association_score_weighted()['script'],
                                     },

                               }
                            }
                          },
                          "association_score": {
                                     "stats": {
                                         "script" : self._get_script_association_score_weighted()['script'],
                                     }
                          },
                          # "association_score": {#TODO: could use the scripted metric, change code below
                          #           "scripted_metric": {
                          #               "init_script" : "_agg['transactions'] = []",
                          #               "map_script" : "if (doc['type'].value == \"sale\") { _agg.transactions.add(doc['amount'].value) } else { _agg.transactions.add(-1 * doc['amount'].value) }",
                          #               "combine_script" : "profit = 0; for (t in _agg.transactions) { profit += t }; return profit",
                          #               "reduce_script" : "profit = 0; for (a in _aggs) { profit += a }; return profit"
                          #           }
                          #       }
                          #     },
                          },

                        },
                    },
                },
            }
        if facets:
            aggs['datatypes'] = self._get_datatype_facet_aggregation(filters)
            aggs['pathway_type'] = gene_related_aggs["pathway_type"]
            aggs['uniprot_keywords'] = gene_related_aggs["uniprot_keywords"]
            # aggs['go'] = gene_related_aggs["go"]


        return aggs

    def _get_complimentary_facet_filters(self, key, filters):
        conditions = []
        for filter_type, filter_value in filters.items():
            if filter_type != key:
                conditions.append(filter_value)
        return conditions

    def _get_script_association_score_weighted(self):
        return {"script_id":"calculate_association_score_weighted",
                "lang" : "groovy",
                "script" : """ev_type =doc['type'].value;
if (ev_type == 'rna_expression') {
  return doc['scores.association_score'].value * 0.5;
} else if (ev_type == 'genetic_association'){
  return doc['scores.association_score'].value;
} else if (ev_type == 'affected_pathway'){
  return doc['scores.association_score'].value;
} else if (ev_type == 'animal_model'){
  return  doc['scores.association_score'].value;
} else if (ev_type == 'somatic_mutation'){
  return doc['scores.association_score'].value * 0.5;
} else if (ev_type == 'literature'){
  return doc['scores.association_score'].value;
}  else if (ev_type == 'known_drug'){
  return doc['scores.association_score'].value;
} else {
  return 0.1;
}
"""}

    def _return_association_data_structures_for_genes(self,
                                                      res,
                                                      agg_key,
                                                      efo_labels = None,
                                                      efo_tas = None,
                                                      efo_with_data=[],
                                                      filters = {}):
        def transform_datasource_point(datatype_point):
            score = datatype_point['association_score'][self.datatource_scoring.scoring_method[datatype_point['key']]]
            if score >1:
                score =1
            elif score <-1:
                score = -1
            return dict(evidence_count = datatype_point['doc_count'],
                        datatype = datatype_point['key'],
                        association_score = round(score,2),
                        )

        def transform_data_point(data_point, efo_with_data=[]):
            datasources = map( transform_datasource_point, data_point["datatypes"]["buckets"])
            datatypes = self._get_datatype_aggregation_from_datasource(datasources)
            try:
                scores = [i['association_score'] for i in datatypes]
                score = round(max(min(scores), max(scores), key=abs), 2)
            except:
                score = 0.
            terapeutic_area_data = list(set([(ta,efo_labels[ta]) for ta in efo_tas[data_point['key']]]))
            terapeutic_area =[]
            for ta,ta_label in terapeutic_area_data:
                terapeutic_area.append(dict(efo_code = ta,
                                            label = ta_label))
            return dict(evidence_count = data_point['doc_count'],
                        efo_code = data_point['key'],
                        # association_score = data_point['association_score']['value'],
                        association_score = score,
                        datatypes = datatypes,
                        label = efo_labels[data_point['key'] or data_point['key']],
                        therapeutic_area = terapeutic_area,
                        )

        data = res['aggregations']['data'][agg_key]["buckets"]
        facets = {}
        #need to add handle there the internal 'data' object coming from the facet filter for every facet
        if 'datatypes' in res['aggregations']:
            facets['datatypes'] = res['aggregations']['datatypes']['data']
        facets = self._extend_facets(facets)
        if data:
            if efo_labels is None:
                efo_parents, efo_labels, efo_tas = self._get_efo_data_for_associations([i["key"] for i in data])
            data = map(transform_data_point, data)
            if efo_with_data:
                data = filter(lambda data_point: data_point['efo_code'] in efo_with_data , data)


        return dict(data = data,
                    facets = facets)

    def _return_association_data_structures_for_genes_as_tree(self,
                                                              res,
                                                              agg_key,
                                                              efo_with_data =[],
                                                              filters = {}):


        def transform_data_to_tree(data, efo_parents, efo_with_data=[]):
            data = dict([(i["efo_code"],i) for i in data])
            expanded_relations = []
            for code, paths in efo_parents.items():
                for path in paths:
                    expanded_relations.append([code,path])
            efo_tree_relations = sorted(expanded_relations,key=lambda items: len(items[1]))
            root=AssociationTreeNode()
            # 'always add available therapeutic areas'
            # for code, parents in efo_tree_relations:
            #     if len(parents)==2:
            #         root.add_child(AssociationTreeNode(code, **data[code]))
            if not efo_with_data:
                efo_with_data= [code for code, parents in efo_tree_relations]
            else:
                for code, parents in efo_tree_relations:
                    if len(parents)==1:
                        if code not in efo_with_data:
                            efo_with_data.append(code)
            for code, parents in efo_tree_relations:
                if code in efo_with_data:
                    if not parents:
                        root.add_child(AssociationTreeNode(code, **data[code]))
                    else:
                        node = root.get_node_at_path(parents)
                        node.add_child(AssociationTreeNode(code,**data[code]))
            return root.to_dict_tree_with_children_as_array()


        data = res['aggregations']['data'][agg_key]["buckets"]
        facets = {}
        if 'datatypes' in res['aggregations']:
            facets['datatypes'] = res['aggregations']['datatypes']['data']
        facets = self._extend_facets(facets)
        data = dict([(i["key"],i) for i in data])
        if data:
            efo_parents, efo_labels,  efo_tas = self._get_efo_data_for_associations(data.keys())
            new_data = self._return_association_data_structures_for_genes(res,agg_key, efo_labels = efo_labels, efo_tas = efo_tas)['data']
            tree_data = transform_data_to_tree(new_data,efo_parents, efo_with_data) or new_data
        else:
            tree_data = data

        return dict(data = tree_data,
                    facets = facets)

    def  _get_efo_data_for_associations(self,efo_keys):
        # def get_missing_ta_labels(efo_labels, efo_therapeutic_area):
        #     all_tas = []
        #     for tas in efo_therapeutic_area.values():
        #         for ta in tas:
        #             all_tas.append(ta)
        #     all_tas=set(all_tas)
        #     all_efo_label_keys = set(efo_labels.keys())
        #     missing_tas_labels = list(all_tas - all_efo_label_keys)
        #     if missing_tas_labels:
        #         for efo in self.get_efo_info_from_code(missing_tas_labels):
        #             efo_labels[efo['path_codes'][0][-1]]=efo['label']
        #     return efo_labels

        efo_parents = {}
        efo_labels = defaultdict(str)
        efo_therapeutic_area = defaultdict(str)
        data = self.get_efo_info_from_code(efo_keys)
        for efo in data:
            code = efo['code'].split('/')[-1]
            parents = []
            for path in efo['path_codes']:
                parents.append(path[:-1])
            efo_parents[code]=parents
            efo_labels[code]=efo['label']
            ta = []
            for path in parents:
                if len(path)>1:
                    if path[1] not in ta:
                        ta.append(path[1])
            efo_therapeutic_area[code]= ta
            # if len(efo['path_codes'])>2:
        # efo_labels = get_missing_ta_labels(efo_labels,efo_therapeutic_area)


        return efo_parents, efo_labels, efo_therapeutic_area

    def _return_association_data_structures_for_efos(self, res, agg_key,  filters = {}):



        def transform_datasource_point(datatype_point):
            score = datatype_point['association_score'][self.datatource_scoring.scoring_method[datatype_point['key']]]
            if score >1:
                score =1
            elif score <-1:
                score = -1
            return dict(evidence_count = datatype_point['doc_count'],
                        datatype = datatype_point['key'],
                        association_score = round(score,2),
                        )

        def transform_data_point(data_point):
            datasources =map( transform_datasource_point, data_point["datatypes"]["buckets"])
            datatypes = self._get_datatype_aggregation_from_datasource(datasources)
            scores = [i['association_score'] for i in datatypes]
            try:
                score = round(max(min(scores), max(scores), key=abs), 2)
            except:
                score = 0.
            return dict(evidence_count = data_point['doc_count'],
                        gene_id = data_point['key'],
                        label = gene_names[data_point['key']],
                        # association_score = data_point['association_score']['value'],
                        association_score = score,
                        datatypes = datatypes,
                            )
        data = res['aggregations']['data'][agg_key]["buckets"]
        gene_ids = [d['key'] for d in data]
        if gene_ids:
            gene_info = self.get_gene_info(gene_ids,
                                           size = len(gene_ids),
                                           fields =['ensembl_gene_id',
                                                   'approved_symbol',
                                                   'ensembl_external_name',
                                                   'reactome.*',
                                                   ],
                                           ).toDict()
            gene_names = defaultdict(str)
            for gene in gene_info['data']:
                gene_names[gene['ensembl_gene_id']] = gene['approved_symbol'] or gene['ensembl_external_name']
        else:
            gene_info = []
        facets =  {}
        if 'datatypes' in res['aggregations']:
            facets['datatypes'] = res['aggregations']['datatypes']['data']
        if 'pathway_type' in res['aggregations']:
            facets['pathway_type'] = res['aggregations']['pathway_type']['data']
        if 'uniprot_keywords' in res['aggregations']:
            facets['uniprot_keywords'] = res['aggregations']['uniprot_keywords']['data']
        facets = self._extend_facets(facets)

        new_data = map(transform_data_point, data)

        return dict(data = new_data,
                    facets = facets)

    def _get_datatype_aggregation_from_datasource(self, datasources):
        datatype_aggs = {}
        for ds in datasources:
            dts = self.datatypes.get_datatypes(ds['datatype'])
            for dt in dts:
                if dt not in datatype_aggs:
                    datatype_aggs[dt]= dict(evidence_count = 0,
                                            datatype = dt,
                                            association_score = 0,
                                            )
                datatype_aggs[dt]['evidence_count'] += ds['evidence_count']
                if abs(ds['association_score']) > abs(datatype_aggs[dt]['association_score']):
                    datatype_aggs[dt]['association_score'] = ds['association_score']
        return datatype_aggs.values()

    def get_expression(self,
                              genes,
                              **kwargs):
        '''
        returns the expression data for a list of genes
        :param genes: list of genes
        :param params: query parameters
        :return: tissue expression data object
        '''
        params = SearchParams(**kwargs)
        if genes:


            source_filter = OutputDataStructureOptions.getSource(params.datastructure)
            if params.fields:
                source_filter["include"]= params.fields

            res = self.handler.search(index=self._index_expression,
                                      body={
                                          'filter': {
                                              "ids": {
                                                  "values": genes
                                              }
                                          },
                                          # 'size': params.size,
                                          # '_source': OutputDataStructureOptions.getSource(OutputDataStructureOptions.COUNT),

                                          }
                                      )
            if res['hits']['total']:
                data = dict([(hit['_id'],hit['_source']) for hit in res['hits']['hits']])
                return SimpleResult(res, params, data)

    def _get_efo_with_data(self, conditions):
        efo_with_data =[]
        res = self.handler.search(index=self._index_data,
                                  body={
                                      "query": {
                                          "filtered": {
                                              "filter": {
                                                  "bool": {
                                                      "must": conditions

                                                  }
                                              }
                                          }
                                      },
                                      'size': 100000,
                                      '_source': [ "disease.id"],
                                       "aggs": {"efo_codes": {
                                           "terms": {
                                               "field" : "disease.id",
                                               'size': 100000,

                                           },
                                         }
                                      }
                                  })
        if res['hits']['total']:
            data = res['aggregations']["efo_codes"]["buckets"]
            efo_with_data=list(set([i['key'] for i in data]))
        return efo_with_data

    def _get_gene_info_agg(self, filters = {}):

        return {
            "pathway_type": {
                "filter": {
                    "bool": {
                        "must": self._get_complimentary_facet_filters(FilterTypes.PATHWAY, filters),
                        }
                    },
                    "aggs":{
                        "data": {
                            "terms": {
                                 "field" : "_private.facets.reactome.pathway_type_code",
                                 'size': 10,
                                },

                            "aggs": {
                                "pathway": {
                                    "terms": {
                                         "field" : "_private.facets.reactome.pathway_code",
                                         'size': 10,
                                    },
                            }
                        },
                    }
                }
             }
        }

    def _get_genes_for_pathway_code(self, pathway_codes):
        data =[]
        res = self.handler.search(index=self._index_genename,
                                  body={
                                      "query": {
                                          "filtered": {
                                              "filter": {
                                                   "bool": {
                                                       "should": [
                                                           {"terms": {"_private.facets.reactome.pathway_code":pathway_codes}},
                                                           {"terms": {"_private.facets.reactome.pathway_type_code":pathway_codes}},
                                                       ]
                                                   }
                                              }
                                          }
                                      },
                                      'size': 100000,
                                      '_source': ["id"],


                                  })
        if res['hits']['total']:
            data = [hit['_id'] for hit in res['hits']['hits']]
        return data

    def _extend_facets(self, facets):

        reactome_ids = []

        '''get data'''
        for facet in facets:
            if 'buckets' in facets[facet]:
                facet_buckets = facets[facet]['buckets']
                for bucket in facet_buckets:
                    if facet=='pathway_type':
                        reactome_ids.append(bucket['key'])
                    if 'pathway' in bucket:
                        if 'buckets' in bucket['pathway']:
                            sub_facet_buckets = bucket['pathway']['buckets']
                            for sub_bucket in sub_facet_buckets:
                                reactome_ids.append(sub_bucket['key'])
        reactome_ids= [i.upper() for i in list(set(reactome_ids))]
        reactome_labels = self._get_labels_for_reactome_ids(reactome_ids)

        '''alter data'''
        for facet in facets:
            if 'buckets' in facets[facet]:
                facet_buckets = facets[facet]['buckets']
                for bucket in facet_buckets:
                    if facet=='pathway_type':
                        bucket['label']=reactome_labels[bucket['key'].upper()]#TODO: fix the data so there is no need for upper
                    if 'pathway' in bucket:
                        if 'buckets' in bucket['pathway']:
                            sub_facet_buckets = bucket['pathway']['buckets']
                            for sub_bucket in sub_facet_buckets:
                                sub_bucket['label'] = reactome_labels[sub_bucket['key'].upper()]
        return facets

    def _get_labels_for_reactome_ids(self, reactome_ids):
        labels = defaultdict(str)
        if reactome_ids:
            reactome_ids = [i.upper() for i in reactome_ids]
            res = self.handler.search(index=self._index_reactome,
                                      doc_type=self._docname_reactome,
                                      body={"query": {
                                              "filtered": {
                                                  # "query": {
                                                  #     "match_all": {}
                                                  # },
                                                  "filter": {
                                                      "ids": {
                                                          "values": reactome_ids

                                                         }
                                                    }
                                                }
                                            },

                                           '_source': ['label'],
                                           'size': 100000,
                                           'from': 0,

                                           }
                                      )
            if res['hits']['total']:
                for hit in res['hits']['hits']:
                    labels[hit['_id']]= hit['_source']['label']
        return labels

    def _get_datatype_facet_aggregation(self, filters):

        return  {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.DATASOURCE, filters),
                    }
                },
                "aggs":{
                    "data": {
                        "terms": {
                             "field" : "_private.datatype",
                             'size': 10,
                           },
                        "aggs":{
                            "datasources": {
                                "terms": {
                                    "field" :  "sourceID",
                                },
                            "aggs":{
                                "unique_target_count": {
                                    "cardinality" : {
                                      "field" : "target.id",
                                      "precision_threshold": 1000},
                                },
                                "unique_disease_count": {
                                    "cardinality" : {
                                      "field" : "disease.id",
                                      "precision_threshold": 1000},
                                    }
                                },
                            },
                            "unique_target_count": {
                               "cardinality" : {
                                  "field" : "target.id",
                                  "precision_threshold": 1000},
                              },
                            "unique_disease_count": {
                               "cardinality" : {
                                  "field" : "disease.id",
                                  "precision_threshold": 1000},
                            },

                        }
                    }
                }
        }


    def _get_pathway_facet_aggregation(self, filters = {}):

        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.PATHWAY, filters),
                    }
                },
                "aggs":{
                    "data": {
                        "terms": {
                             "field" : "_private.facets.reactome.pathway_type_code",
                             'size': 100,
                            },

                        "aggs": {
                            "pathway": {
                                "terms": {
                                     "field" : "_private.facets.reactome.pathway_code",
                                     'size': 10,
                                },
                                "aggs":{
                                    "unique_target_count": {
                                        "cardinality" : {
                                          "field" : "target.id",
                                          "precision_threshold": 1000},
                                    },
                                    "unique_disease_count": {
                                        "cardinality" : {
                                          "field" : "disease.id",
                                          "precision_threshold": 1000},
                                        }
                                    },
                            },
                            "unique_target_count": {
                               "cardinality" : {
                                  "field" : "target.id",
                                  "precision_threshold": 1000
                               },
                            },
                            "unique_disease_count": {
                               "cardinality" : {
                                  "field" : "disease.id",
                                  "precision_threshold": 1000
                               },
                            },
                        }
                    },
                }
            }


    def _get_gene_related_aggs(self, filters):
        return dict(
            pathway_type = self._get_pathway_facet_aggregation(filters),
            go = self._get_go_facet_aggregation(filters),
            uniprot_keywords = self._get_uniprot_keywords_facet_aggregation(filters),

        )

    def _get_go_facet_aggregation(self, filters):
        pass

    def _get_uniprot_keywords_facet_aggregation(self, filters):
        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.UNIPROT_KW, filters),
                    }
                },
                "aggs":{
                    "data": {
                        "significant_terms": {
                             "field" : "_private.facets.uniprot_keywords",
                             'size': 10,
                        },
                        "aggs": {
                            "unique_target_count": {
                               "cardinality" : {
                                  "field" : "target.id",
                                  "precision_threshold": 1000
                               },
                            },
                            "unique_disease_count": {
                               "cardinality" : {
                                  "field" : "disease.id",
                                  "precision_threshold": 1000
                               },
                            },
                        },
                    },
                }
            }


class SearchParams():
    _max_search_result_limit = 100000
    _default_return_size = 10
    _allowed_groupby = ['gene', 'evidence-type', 'efo']


    def __init__(self, **kwargs):

        self.size = kwargs.get('size', self._default_return_size) or self._default_return_size
        if (self.size > self._max_search_result_limit):
            self.size = self._max_search_result_limit

        self.start_from = kwargs.get('from', 0) or 0

        self.groupby = []
        groupby = kwargs.get('groupby')
        if groupby:
            for g in groupby:
                if g in self._allowed_groupby:
                    self.groupby.append(g)

        self.orderby = kwargs.get('orderby')

        self.gte = kwargs.get('gte')

        self.lt = kwargs.get('lt')

        self.format = kwargs.get('format', 'json') or 'json'

        self.datastructure = kwargs.get('datastructure', OutputDataStructureOptions.DEFAULT) or OutputDataStructureOptions.DEFAULT

        self.fields = kwargs.get('fields')

        if self.fields:
            self.datastructure = OutputDataStructureOptions.CUSTOM

        self.filters = dict()
        self.filters[FilterTypes.ASSOCIATION_SCORE_MIN] = kwargs.get(FilterTypes.ASSOCIATION_SCORE_MIN,0.25)
        self.filters[FilterTypes.ASSOCIATION_SCORE_MAX] = kwargs.get(FilterTypes.ASSOCIATION_SCORE_MAX,1)
        self.filters[FilterTypes.DATASOURCE] = kwargs.get(FilterTypes.DATASOURCE)
        self.filters[FilterTypes.DATATYPE] = kwargs.get(FilterTypes.DATATYPE)
        self.filters[FilterTypes.PATHWAY] = kwargs.get(FilterTypes.PATHWAY)
        if self.filters[FilterTypes.PATHWAY]:
            self.filters[FilterTypes.PATHWAY] = map(str.upper, self.filters[FilterTypes.PATHWAY])


        self.pathway= kwargs.get('pathway', [])
        self.target_class= kwargs.get('target_class')

        self.expand_efo = kwargs.get('expandefo', False)
        self.facets = kwargs.get('facets', True)



class AssociationTreeNode(object):
    ROOT = 'cttv_disease'

    def __init__(self, name = None, **kwargs):
        self.name = name or self.ROOT
        self.children = {}
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _is_root(self):
        return self.name == self.ROOT

    def add_child(self, child):
        if isinstance(child, AssociationTreeNode):
            if child._is_root():
                raise AttributeError("child cannot be root ")
            if child == self:
                raise AttributeError(" cannot add a node to itself as a child")
            if not self.has_child(child):
                self.children[child.name]=child
        else:
            raise AttributeError("child needs to be an AssociationTreeNode ")

    def get_child(self, child_name):
        return self.children[child_name]

    def has_child(self, child):
        if isinstance(child, AssociationTreeNode):
            return child.name in self.children
        return child in self.children

    def get_children(self):
        return self.children.values()

    def get_node_at_path(self, path):
        node = self
        for p in path:
            if node.has_child(p):
                node = node.get_child(p)
                continue
        # if node._is_root():
        #     print 'got root for path: ', path, node.children_as_array()
        return node

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)

    def children_as_array(self):
        return self.children.values()

    def single_node_to_dict(self):
        out = self.__dict__
        if self.children:
            out['children']= self.children_as_array()
        else:
            del out['children']
        return out


    def recursive_node_to_dict(self, node):
        if isinstance(node, AssociationTreeNode):
            out = node.single_node_to_dict()
            if 'children' in out:
                for i,child in enumerate(out['children']):
                    if isinstance(child, AssociationTreeNode):
                        child = child.recursive_node_to_dict(child)
                    out['children'][i] = child
            return out


    def to_dict_tree_with_children_as_array(self):
        out = self.recursive_node_to_dict(self)
        return out



