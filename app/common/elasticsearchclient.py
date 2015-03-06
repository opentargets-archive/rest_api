from collections import defaultdict
import collections
import pprint
import itertools
import csv
from StringIO import StringIO
import operator
import logging

from flask import current_app
import ujson as json
from dicttoxml import dicttoxml
from elasticsearch import helpers

from app.common.responses import ResponseType
from app.common.requests import OutputDataStructureOptions


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
                 index_data=None,
                 index_efo=None,
                 index_eco=None,
                 index_genename=None,
                 docname_data=None,
                 docname_efo=None,
                 docname_eco=None,
                 docname_genename=None,
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
        self._docname_data = docname_data
        self._docname_efo = docname_efo
        self._docname_eco = docname_eco
        self._docname_genename = docname_genename

        if log_level == logging.DEBUG:
            es_logger = logging.getLogger('elasticsearch')
            es_logger.setLevel(logging.DEBUG)
            es_tracer = logging.getLogger('elasticsearch.trace')
            es_tracer.setLevel(logging.DEBUG)
            es_tracer.addHandler(logging.FileHandler('es_trace.log'))


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
                                                      "biological_subject.about": self._get_gene_filter(gene)

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
                                                              "biological_subject.about":
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


    def autocomplete_search(self, searchphrase,
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
        current_app.logger.debug("Got %d Hits in %ims" % (res['hits']['total'], res['took']))

        if res['hits']['total']:
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
                           #                        'biological_subject.about': 'ensembl:'},
                           #                    },
                           query={"query": {"match_all": {}},

                                  'size': 1000,
                                  'fields': ['biological_subject.about'],
                           },
                           scroll='10m',
                           # doc_type=self._docname_data,
                           index=self._index_data,
                           timeout="10m",
        )

        available_genes = defaultdict(int)
        for hit in res:
            gene_name = hit['fields']['biological_subject.about'][0]
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


    def get_gene_info(self,gene_ids, **kwargs):
        params = SearchParams(**kwargs)
        if params.datastructure == OutputDataStructureOptions.DEFAULT:
            params.datastructure = OutputDataStructureOptions.FULL
        source_filter = OutputDataStructureOptions.getSource(params.datastructure)
        if params.fields:
            source_filter["include"]= params.fields


        if gene_ids:
            res = self.handler.search(index=self._index_genename,
                                      doc_type=self._docname_genename,
                                      body={'filter': {
                                              "ids": {
                                                  "values": gene_ids
                                                  },
                                              },
                                           '_source': source_filter,
                                           'size': params.size,
                                           'from': params.start_from,
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
                                            'size' : 10000
                                      }
            )
            if res['hits']['total']:
                if res['hits']['total']==1:
                    return res['hits']['hits'][0]['_source']
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
                                                      "biological_object.about": efocode

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
            conditions.append(self._get_complex_object_filter(objects, object_operator))
        if evidence_types:
            conditions.append(self._get_complex_evidence_type_filter(evidence_types, evidence_type_operator))
        if datasources:
            conditions.append(self._get__complex_datasource_filter(datasources, BooleanFilterOperator.OR))
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
                                                 "field" : "biological_object.about",
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
                                          '_source': source_filter,
                                      }
            )



        return PaginatedResult(res, params)

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
        conditions = []
        aggs = None
        if objects:
            conditions.append(self._get_complex_object_filter(objects, object_operator))
            params.datastructure = OutputDataStructureOptions.FLAT#override datastructure as only flat is available
            aggs = self._get_efo_associations_agg()
        if genes:
            conditions.append(self._get_complex_gene_filter(genes, gene_operator))
            if not aggs:
                aggs = self._get_gene_associations_agg()


        '''boolean query joining multiple conditions with an AND'''
        source_filter = OutputDataStructureOptions.getSource(params.datastructure)
        if params.fields:
            source_filter["include"]= params.fields

        res = self.handler.search(index=self._index_data,
                                  # doc_type='evidencestring-phenodigm',
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
                                      '_source': OutputDataStructureOptions.getSource(OutputDataStructureOptions.COUNT),
                                       "aggs": aggs

                                      }
                                  )
        # print res
        if res['hits']['total']:
            '''build data structure to return'''
            if objects:
                if params.datastructure == OutputDataStructureOptions.FLAT:
                    data = self._return_association_data_structures_for_efos(res, "genes", filter_value=params.filter)
            elif genes:
                if params.datastructure == OutputDataStructureOptions.FLAT:
                    data = self._return_association_data_structures_for_genes(res, "efo_codes", filter_value=params.filter)
                elif params.datastructure == OutputDataStructureOptions.TREE:
                    data= self._return_association_data_structures_for_genes_as_tree(res, "efo_codes", filter_value=params.filter)



            return CountedResult(res, params, data, total = res['hits']['total'])#res['aggregations'], res['hits']['hits']

    def _get_gene_filter(self, gene):
        return [
            gene,
            # "http://identifiers.org/uniprot/"+gene,
            # "http://identifiers.org/ensembl/" + gene,
        ]

    def _get_complex_gene_filter(self, genes, bol):
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
                                  "biological_subject.about": self._get_gene_filter(gene)}
                          }
                          for gene in genes]
                }
            }
        return dict()


    def _get_object_filter(self, object):
        return [object,
               # "http://identifiers.org/efo/" + object,
        ]

    def _get_complex_object_filter(self, objects, bol):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param objects: list of objects
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if objects:
             return {
                    "bool": {
                        bol : [{
                              "terms": {
                                 # "biological_object.about": self._get_object_filter(object)}
                                "_private.efo_codes": self._get_object_filter(object)}
                          }
                          for object in objects]
                    }

            }

    def _get_evidence_type_filter(self, evidence_type):
        return [evidence_type,
                "http://identifiers.org/eco/" + evidence_type,
        ]

    def _get_complex_evidence_type_filter(self, evidence_types, bol):
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
                                  "evidence.evidence_codes": self._get_evidence_type_filter(evidence_type)}
                          }
                          for evidence_type in evidence_types]
                }
            }
        return dict()


    def _get__complex_datasource_filter(self, datasources, bol):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param evidence_types: list of dataasource strings
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if datasources:
            filters = []
            for datasource in datasources:
                filters.append({ "terms": {"_private.datasource": [datasource]}})
                filters.append({ "terms": {"evidence.provenance_type.database.id": [datasource]}})


            return {
                "bool": {
                    bol:filters
                }
            }
        return dict()



    def _get_free_text_query(self, searchphrase):
        return {"bool": {
                    "should": [
                        {"multi_match" : {
                            "query":    searchphrase,
                            "fields": [ "label^5",
                                        "symbol_synonyms",
                                        "efo_synonyms",
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



        #
        # return {"bool": {
        #     "should": [
        #         {'match': {
        #             "label": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #                  "analyzer" : "keyword",
        #                 # "prefix_length": 1,
        #                 # "max_expansions": 100,
        #                 # "fuzziness": "AUTO"
        #
        #             },
        #         }},
        #         # {'prefix': {
        #         #     "label": {
        #         #         "value": searchphrase,
        #         #         "boost": 1.0,
        #         #         # "prefix_length": 1,
        #         #         # "max_expansions": 100,
        #         #         # "fuzziness": "AUTO"
        #         #
        #         #     },
        #         # }},
        #         #  {'prefix': {
        #         #     "_id": {
        #         #         "value": "EFO_",
        #         #         "boost": .0001,
        #         #         # "prefix_length": 1,
        #         #         # "max_expansions": 100,
        #         #         # "fuzziness": "AUTO"
        #         #
        #         #     },
        #         # }},
        #         # {'match_phrase': {
        #         #     "efo_synonyms": {
        #         #         "query": searchphrase,
        #         #         "boost": .1,
        #         #         # "prefix_length": 1,
        #         #         # "max_expansions": 100,
        #         #         # "fuzziness": "AUTO"
        #         #     },
        #         # }},
        #         {'match': {
        #             "efo_synonyms": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #                  "analyzer" : "keyword",
        #                 }
        #
        #         }},
        #          {'term': {
        #             "efo_synonyms": {
        #                 "value": searchphrase,
        #                 "boost": 1.0,
        #                 }
        #
        #         }},
        #         {'match': {
        #             "symbol_synonyms": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #                  "analyzer" : "keyword",
        #                 }
        #
        #         }},
        #         # {'prefix': {
        #         #     "symbol_synonyms": {
        #         #         "value": searchphrase,
        #         #         "boost": 1.0,
        #         #         }
        #         #
        #         # }},
        #         {'match': {
        #             "id": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #             },
        #         }},
        #         {'match': {
        #             "approved_symbol": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #                 "analyzer" : "keyword",
        #             },
        #         }},
        #         # {'prefix': {
        #         #     "approved_symbol": {
        #         #         "value": searchphrase,
        #         #         "boost": 1.0,
        #         #         }
        #         #
        #         # }},
        #         {'match': {
        #             "approved_name": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #                 # "operator" : "and",
        #                  "analyzer" : "keyword",
        #                 # "prefix_length": 3,
        #                 # "max_expansions": 1,
        #                 #  "fuzziness": "AUTO"
        #             },
        #         }},
        #         {'match_phrase': {
        #             "name_synonyms": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #                 "operator" : "and",
        #                  "analyzer" : "keyword",
        #                 # "prefix_length": 3,
        #                 # "max_expansions": 1,
        #                 # "fuzziness": "AUTO"
        #             },
        #         }},
        #
        #
        #         {'match': {
        #             "gene_family_description": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #                 # "prefix_length": 3,
        #                 # "max_expansions": 3,
        #                 # "fuzziness": "AUTO",
        #                  "analyzer" : "keyword"
        #             },
        #         }},
        #         {'match': {
        #             "uniprot_id": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #                  "analyzer" : "keyword",
        #             },
        #         }},
        #         {'match': {
        #             "uniprot_accessions": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #                  "analyzer" : "keyword",
        #             },
        #         }},
        #         {'match': {
        #             "hgnc_id": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #                  "analyzer" : "keyword",
        #             },
        #         }},
        #         {'match': {
        #             "ensembl_gene_id": {
        #                 "query": searchphrase,
        #                 "boost": 1.0,
        #             },
        #         }}
        #     ]
        # }
        # }


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

        # return {"bool": {
        #     "should": [
        #        {'match': {
        #             "symbol_synonyms": {
        #                 "query": searchphrase,
        #                 "boost": 20.0,
        #                 }
        #
        #         }},
        #         {'prefix': {
        #             "symbol_synonyms": {
        #                 "value": searchphrase,
        #                 "boost": 30.0,
        #                 }
        #
        #         }},
        #         {'match': {
        #             "id": {
        #                 "query": searchphrase,
        #                 "boost": 30.0,
        #             },
        #         }},
        #         {'match': {
        #             "approved_symbol": {
        #                 "query": searchphrase,
        #                 "boost": 50.0,
        #             },
        #         }},
        #         {'prefix': {
        #             "approved_symbol": {
        #                 "value": searchphrase,
        #                 "boost": 50.0,
        #                 }
        #
        #         }},
        #         {'match': {
        #             "approved_name": {
        #                 "query": searchphrase,
        #                 "boost": 10.0,
        #                 "operator" : "and",
        #                 # "prefix_length": 3,
        #                 # "max_expansions": 1,
        #                 # "fuzziness": "AUTO"
        #             },
        #         }},
        #         {'match': {
        #             "name_synonyms": {
        #                 "query": searchphrase,
        #                 "boost": 10.0,
        #                 "operator" : "and",
        #                 # "prefix_length": 3,
        #                 # "max_expansions": 1,
        #                 # "fuzziness": "AUTO"
        #             },
        #         }},
        #
        #
        #         {'match': {
        #             "gene_family_description": {
        #                 "query": searchphrase,
        #                 "boost": 10.0,
        #                 "prefix_length": 3,
        #                 "max_expansions": 3,
        #                 "fuzziness": "AUTO"
        #             },
        #         }},
        #         {'match': {
        #             "uniprot_accessions": {
        #                 "query": searchphrase,
        #                 "boost": 50.0,
        #             },
        #         }},
        #         {'match': {
        #             "hgnc_id": {
        #                 "query": searchphrase,
        #                 "boost": 10.0,
        #             },
        #         }},
        #         {'match': {
        #             "ensembl_gene_id": {
        #                 "query": searchphrase,
        #                 "boost": 50.0,
        #             },
        #         }}
        #     ]
        # }
        #
        # }

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
                                      ]
                            "analyzer" : 'keyword',
                            # "fuzziness": "AUTO",
                            # "tie_breaker": 0.1,
                            "type": "best_fields",
                          }
                        }
                    ]
                }
            }


        # return {"bool": {
        #     "should": [
        #           {'match_phrase': {
        #             "label": {
        #                 "query": searchphrase,
        #                 "boost": 30.0,
        #                 # "prefix_length": 1,
        #                 # "max_expansions": 100,
        #                 # "fuzziness": "AUTO"
        #
        #             },
        #         }},
        #         {'prefix': {
        #             "label": {
        #                 "value": searchphrase,
        #                 "boost": 100.0,
        #                 # "prefix_length": 1,
        #                 # "max_expansions": 100,
        #                 # "fuzziness": "AUTO"
        #
        #             },
        #         }},
        #         {'match_phrase': {
        #             "efo_synonyms": {
        #                 "query": searchphrase,
        #                 "boost": 10.0,
        #                 # "prefix_length": 1,
        #                 # "max_expansions": 100,
        #                 # "fuzziness": "AUTO"
        #             },
        #         }},
        #         {'prefix': {
        #             "efo_synonyms": {
        #                 "value": searchphrase,
        #                 "boost": 10.0,
        #                 }
        #
        #         }},
        #         {'match': {
        #             "id": {
        #                 "query": searchphrase,
        #                 "boost": 50.0,
        #             },
        #         }},
        #     ]
        # }
        #
        # }

    def _get_gene_associations_agg(self):
        return {"efo_codes": {
                   "terms": {
                       "field" : "_private.efo_codes",
                       'size': 100,
                       "order": {
                           "association_score": "desc"
                       }
                   },
                    "aggs":{
                          "datatypes": {
                             "terms": {
                                 "field" : "_private.datatype",
                                 'size': 10000,
                               },
                             "aggs":{
                                  "association_score": {
                                     "sum": {
                                         "script" : self._get_script_association_score_weighted()['script'],
                                     },

                               }
                            }
                          },
                          "association_score": {
                                     "sum": {
                                         "script" : self._get_script_association_score_weighted()['script'],
                                     },

                               }

                      }
                   # "aggs":{
                   #    "datasource": {
                   #       "terms": {
                   #           "field" : "evidence.provenance_type.database.id",
                   #           'size': 10000,
                   #       },
                   #    }
                   # }
                 }
              }

    def _get_efo_associations_agg(self):
        # return {"genes": {
        #            "terms": {
        #                "field" : "biological_subject.about",
        #                'size': 100,
        #            },
        #            "aggs":{
        #               "datasource": {
        #                  "terms": {
        #                      "field" : "evidence.provenance_type.database.id",
        #                      'size': 10000,
        #                  },
        #            }
        #          }
        #       }

        return {"genes": {
                   "terms": {
                       "field" : "biological_subject.about",
                       'size': 100,
                       "order": {
                           "association_score": "desc"
                       }
                   },
                   "aggs":{
                          "datatypes": {
                             "terms": {
                                 "field" : "_private.datatype",
                                 'size': 10000,
                               },
                             "aggs":{
                                  "association_score": {
                                     "sum": {
                                         "script" : self._get_script_association_score_weighted()['script'],
                                     },

                               }
                            }
                          },
                          "association_score": {
                                     "sum": {
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

                   }
               }

    def _get_script_association_score_weighted(self):
        return {"script_id":"calculate_association_score_weighted",
                "lang" : "groovy",
                "script" : """db =doc['evidence.provenance_type.database.id'].value;
if (db == 'expression_atlas') {
  return 0.01;
} else if (db == 'uniprot'){
  return 1.0;
} else if (db == 'reactome'){
  return 0.2;
} else if (db == 'eva'){
  return 0.5;
} else if (db == 'phenodigm'){
  return 0.0333;
} else if (db == 'gwas'){
  return 0.5;
} else if (db == 'cancer_gene_census'){
  return 0.5;
}  else if (db == 'chembl'){
  return 1;
} else {
  return 0.1;
}
"""}

    def _return_association_data_structures_for_genes(self, res, agg_key, filter_value = None, efo_labels = None, efo_tas = None):
        def transform_datasource_point(datatype_point):
            if datatype_point['association_score']['value'] >1:
                datatype_point['association_score']['value'] =1
            return dict(evidence_count = datatype_point['doc_count'],
                        datatype = datatype_point['key'],
                        association_score = round(datatype_point['association_score']['value'],2),
                        )

        def transform_data_point(data_point):
            datatypes =map( transform_datasource_point, data_point["datatypes"]["buckets"])

            return dict(evidence_count = data_point['doc_count'],
                        efo_code = data_point['key'],
                        # association_score = data_point['association_score']['value'],
                        association_score = round(sum([i['association_score'] for i in datatypes]), 2),
                        datatypes = datatypes,
                        label = efo_labels[data_point['key'] or data_point['key']],
                        therapeutic_area = efo_labels[efo_tas[data_point['key']]],
                        )

        data = res['aggregations'][agg_key]["buckets"]
        if filter_value is not None:
            data = filter(lambda data_point: data_point['association_score']['value'] >= filter_value, data)
        if efo_labels is  None:
            efo_parents, efo_labels, efo_tas = self._get_efo_data_for_associations([i["key"] for i in data])
        new_data = map(transform_data_point, data)


        return new_data

    def _return_association_data_structures_for_genes_as_tree(self, res, agg_key, filter_value = None):


        def transform_data_to_tree(data, efo_parents):
            data = dict([(i["efo_code"],i) for i in data])
            efo_tree_relations = sorted(efo_parents.items(),key=lambda items: len(items[1]))
            root=AssociationTreeNode()
            for code, parents in efo_tree_relations:
                if not parents:
                    root.add_child(AssociationTreeNode(code, **data[code]))
                else:
                    node = root.get_node_at_path(parents)
                    node.add_child(AssociationTreeNode(code,**data[code]))

            return root.to_dict_tree_with_children_as_array()


        data = res['aggregations'][agg_key]["buckets"]
        if filter_value is not None:
            data = filter(lambda data_point: data_point['association_score']['value'] >= filter_value, data)
        data = dict([(i["key"],i) for i in data])
        efo_parents, efo_labels,  efo_tas = self._get_efo_data_for_associations(data.keys())
        new_data = self._return_association_data_structures_for_genes(res,agg_key, efo_labels = efo_labels, efo_tas = efo_tas)
        tree_data = transform_data_to_tree(new_data,efo_parents) or new_data
        return tree_data

    def  _get_efo_data_for_associations(self,efo_keys):
        efo_parents = {}
        efo_labels = defaultdict(str)
        efo_therapeutic_area = defaultdict(str)
        data = self.get_efo_info_from_code(efo_keys)
        for efo in data:
            code = efo['code'].split('/')[-1]
            parents = efo['path_codes'][:-1]
            efo_parents[code]=parents
            efo_labels[code]=efo['label']
            ta = ''
            if len(parents)>1:
                ta = parents[1]
            efo_therapeutic_area[code]= ta

        return efo_parents, efo_labels, efo_therapeutic_area

    def _return_association_data_structures_for_efos(self, res, agg_key, filter_value=None):



        def transform_datasource_point(datatype_point):
            if datatype_point['association_score']['value'] >1:
                datatype_point['association_score']['value'] =1
            return dict(evidence_count = datatype_point['doc_count'],
                        datatype = datatype_point['key'],
                        association_score = round(datatype_point['association_score']['value'],2),
                        )

        def transform_data_point(data_point):
            datatypes =map( transform_datasource_point, data_point["datatypes"]["buckets"])
            return dict(evidence_count = data_point['doc_count'],
                        gene_id = data_point['key'],
                        label = gene_names[data_point['key']],
                        # association_score = data_point['association_score']['value'],
                        association_score = round(sum([i['association_score'] for i in datatypes]),2),
                        datatypes = datatypes,
                            )
        data = res['aggregations'][agg_key]["buckets"]
        if filter_value is not None:
            data = filter(lambda data_point: data_point['association_score']['value'] >= filter_value, data)
        gene_ids = [d['key'] for d in data]
        gene_info = self.get_gene_info(gene_ids, size = gene_ids).toDict()
        gene_names = defaultdict(str)
        for gene in gene_info['data']:
            gene_names[gene['ensembl_gene_id']] = gene['approved_symbol'] or gene['ensembl_external_name']
        new_data = map(transform_data_point, data)
        return new_data




class SearchParams():
    _max_search_result_limit = 10000
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

        self.filter = kwargs.get('filter')


class Result(object):
    format = ResponseType.JSON

    def __init__(self, res, params, data=None):
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
        NOT_ALLOWED_FIELDS = ['evidence.evidence_chain']
        output = StringIO()
        if self.data is None:
            self.flatten(self.toDict())  # populate data if empty
        if isinstance(self.data[0], dict):
            key_set = set()
            flattened_data = []
            for row in self.data:
                flat = self.flatten(row,
                                    simplify=self.params.datastructure == OutputDataStructureOptions.SIMPLE)
                for field in NOT_ALLOWED_FIELDS:
                    flat.pop(field, None)
                flattened_data.append(flat)
                key_set.update(flat.keys())

            writer = csv.DictWriter(output,
                                    sorted(list(key_set)),
                                    delimiter='\t',
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL,
                                    doublequote=False,
                                    escapechar='|')
            writer.writeheader()
            for row in flattened_data:
                writer.writerow(row)
        if isinstance(self.data[0], list):
            writer = csv.writer(output,
                                delimiter='\t',
                                quotechar='"',
                                quoting=csv.QUOTE_MINIMAL,
                                doublequote=False,
                                escapechar='|')
            for row in self.data:
                writer.writerow(row)
        return output.getvalue()

    def flatten(self, d, parent_key='', sep='.', simplify=False):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return_dict = {}
        for k, v in items:
            if isinstance(v, list):
                if len(v) == 1:
                    v = v[0]
            return_dict[k] = v
        if simplify:
            for k, v in items:
                try:
                    if v.startswith("http://identifiers.org/") or \
                            k.startswith("biological_object.properties."):
                        return_dict.pop(k)
                except:
                    pass

        return return_dict


class PaginatedResult(Result):
    def toDict(self):
        if self.data is None:
            if self.params.datastructure == OutputDataStructureOptions.COUNT:
                return {'total': self.res['hits']['total'],
                        'took': self.res['took']
                }
            elif self.params.datastructure == OutputDataStructureOptions.SIMPLE:
                self.data = [self.flatten(hit['_source'], simplify=True) for hit in self.res['hits']['hits']]

            else:
                self.data = [hit['_source'] for hit in self.res['hits']['hits']]
        else:
            if self.params.datastructure == OutputDataStructureOptions.SIMPLE:
                self.data = [self.flatten(hit['_source'], simplify=True) for hit in self.res['hits']['hits']]

        return {'data': self.data,
                'total': self.res['hits']['total'],
                'took': self.res['took'],
                'size': len(self.data) or 0,
                'from': self.params.start_from
        }


class SimpleResult(Result):
    ''' just need data to be passed and it will be returned as dict
    '''

    def toDict(self):
        if not self.data:
            raise AttributeError('some data is needed to be returned in a SimpleResult')
        return {'data': self.data}

class CountedResult(Result):

    def __init__(self, *args, **kwargs):
        '''

        :param total: count to return, needs to be passed as kwarg
        '''
        total = None
        if 'total' in kwargs:
            total = kwargs.pop('total')
        super(self.__class__,self).__init__(*args, **kwargs)
        self.total = total or len(self.data)

    def toDict(self):
        if not self.data:
            raise AttributeError('some data is needed to be returned in a CountedResult')
        return {'data': self.data,
                'total': self.total,
        }

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
                raise AttributeError("child cannot add a  node to itself ")
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
        return node

    def __eq__(self, other):
        return self.name == other.name

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



