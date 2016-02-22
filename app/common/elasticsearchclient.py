from collections import defaultdict
from copy import copy

import operator
import logging
import pprint
import numpy as np
import json

from flask import current_app
from elasticsearch import helpers
from pythonjsonlogger import jsonlogger
from app.common.request_templates import SourceDataStructureOptions, OutputStructureOptions
from app.common.response_templates import Association
from app.common.results import PaginatedResult, SimpleResult, CountedResult, EmptyPaginatedResult
from app.common.datatypes import FilterTypes
from app.common.scoring import Scorer, Score
from app.common.scoring_conf import ScoringMethods

__author__ = 'andreap'


class BooleanFilterOperator():
    AND = 'must'
    OR = 'should'
    NOT = 'must_not'


class FreeTextFilterOptions():
    ALL = 'all'
    TARGET = 'target'
    DISEASE = 'disease'
    GO_TERM = 'go'
    PROTEIN_FEATURE = 'protein_feature'
    PUBLICATION = 'pub'
    SNP = 'snp'
    GENERIC = 'generic'


class ESResultStatus(object):
    def __init__(self):
        self.reset()

    def add_error(self, error_string):
        if 'ok' in self.status:
            self.status = [error_string]
        else:
            self.status.append(error_string)

    def reset(self):
        self.status = ['ok']


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
                 index_association=None,
                 index_search=None,
                 docname_data=None,
                 docname_efo=None,
                 docname_eco=None,
                 docname_genename=None,
                 docname_expression=None,
                 docname_reactome=None,
                 docname_association=None,
                 docname_search=None,
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
        self._index_association = index_association
        self._index_search = index_search

        self._docname_data = docname_data
        self._docname_efo = docname_efo
        self._docname_eco = docname_eco
        self._docname_genename = docname_genename
        self._docname_expression = docname_expression
        self._docname_reactome = docname_reactome
        self._docname_association = docname_association
        self._docname_search = docname_search
        self.datatypes = datatypes
        self.datatource_scoring = datatource_scoring
        self.scorer = Scorer(datatource_scoring)

        if log_level == logging.DEBUG:
            formatter = jsonlogger.JsonFormatter()
            # es_logger = logging.getLogger('elasticsearch')
            # for handler in es_logger.handlers:
            #     handler.setFormatter(formatter)
            # es_logger.setLevel(log_level)
            # es_tracer = logging.getLogger('elasticsearch.trace')
            # es_tracer.setLevel(log_level)
            # # es_tracer.addHandler(logging.FileHandler('es_trace.log'))
            # for handler in es_tracer.handlers:
            #     handler.setFormatter(formatter)

    def free_text_search(self, searchphrase,
                         doc_filter=[FreeTextFilterOptions.ALL],
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
        :param doc_filter:
        :param kwargs:
        :return:
        '''
        searchphrase = searchphrase.lower()
        params = SearchParams(**kwargs)
        if doc_filter is None:
            doc_filter = [FreeTextFilterOptions.ALL]
        doc_filter = self._get_search_doc_types(doc_filter)
        res = self._free_text_query(searchphrase, doc_filter, params)
        # current_app.logger.debug("Got %d Hits in %ims" % (res['hits']['total'], res['took']))
        data = []
        for hit in res['hits']['hits']:
            highlight = ''
            if 'highlight' in hit:
                highlight = hit['highlight']
            datapoint = dict(type=hit['_type'],
                             data=hit['_source'],
                             id=hit['_id'],
                             score=hit['_score'],
                             highlight=highlight)
            data.append(datapoint)
        return PaginatedResult(res, params, data)

    def quick_search(self,
                     searchphrase,
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
        :param doc_filter:
        :param kwargs:
        :return:
        '''

        def format_datapoint(hit):
            highlight = ''
            if 'highlight' in hit:
                highlight = hit['highlight']
            datapoint = dict(type=hit['_type'],
                             id=hit['_id'],
                             score=hit['_score'],
                             highlight=highlight,
                             data=hit['_source'])
            for opt in active_options:
                returned_ids[opt].append(hit['_id'])
            return datapoint

        searchphrase = searchphrase.lower()
        params = SearchParams(**kwargs)

        active_options = [FreeTextFilterOptions.TARGET,
                          FreeTextFilterOptions.DISEASE]

        data = {'besthit': None}
        returned_ids = {}
        for opt in active_options:
            data[opt] = []
            returned_ids[opt] = []

        res = self._free_text_query(searchphrase, [], params)

        if ('hits' in res) and res['hits']['total']:
            '''handle best hit'''
            best_hit = res['hits']['hits'][0]
            data['besthit'] = format_datapoint(best_hit)

            ''' store the other results in the corresponding object'''
            for hit in res['hits']['hits'][1:]:
                for opt in active_options:
                    if hit['_type'] == self._get_search_doc_name(opt):
                        if len(data[opt]) < params.size:
                            data[opt].append(format_datapoint(hit))

            '''if there are not enough fill the results for all the categories'''
            for opt in active_options:

                if len(data[opt]) < params.size:
                    res_opt = self._free_text_query(searchphrase, [opt], params)
                    for hit in res_opt['hits']['hits']:
                        if len(data[opt]) < params.size:
                            if hit['_id'] not in returned_ids[opt]:
                                data[opt].append(format_datapoint(hit))

        return SimpleResult(None, params, data)

    def autocomplete(self,
                     searchphrase,
                     **kwargs):

        searchphrase = searchphrase.lower()
        params = SearchParams(**kwargs)

        res = self.handler.suggest(index=[self._index_search],
                                   body={"suggest": {
                                       "text": searchphrase,
                                       "completion": {
                                           "field": "_private.suggestions"
                                       }
                                   }
                                   }

                                   )
        # current_app.logger.debug("Got %d Hits in %ims" % (res['hits']['total'], res['took']))
        data = []
        if 'suggest' in res:
            data = res['suggest'][0]['options']
        return SimpleResult(None, params, data)

    def get_gene_info(self, gene_ids, facets=False, **kwargs):
        params = SearchParams(**kwargs)
        if params.datastructure == SourceDataStructureOptions.DEFAULT:
            params.datastructure = SourceDataStructureOptions.FULL
        source_filter = SourceDataStructureOptions.getSource(params.datastructure)
        if params.fields:
            source_filter["include"] = params.fields
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
                                          'aggs': aggs,

                                      }
                                      )
            if res['hits']['total']:
                return SimpleResult(res, params)

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
                                          'size': 100000
                                      }
                                      )
            if res['hits']['total']:
                if res['hits']['total'] == 1:
                    return [res['hits']['hits'][0]['_source']]
                else:
                    return [hit['_source'] for hit in res['hits']['hits']]

    def get_evidences_by_id(self, evidenceid, **kwargs):

        if isinstance(evidenceid, str):
            evidenceid = [evidenceid]

        params = params = SearchParams(**kwargs)
        if params.datastructure == SourceDataStructureOptions.DEFAULT:
            params.datastructure = SourceDataStructureOptions.FULL

        res = self.handler.search(index=self._index_data,
                                  # doc_type=self._docname_data,
                                  body={"filter": {
                                            "ids": {"values": evidenceid},
                                            },
                                        "size" : len(evidenceid),
                                        }
                                  )
        if res['hits']['total']:
            return SimpleResult(res,
                                params,
                                data = [hit['_source'] for hit in res['hits']['hits']])

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

    def get_evidence(self,
                     targets=[],
                     diseases=[],
                     evidence_types=[],
                     datasources=[],
                     datatypes=[],
                     gene_operator='OR',
                     object_operator='OR',
                     evidence_type_operator='OR',
                     **kwargs):
        params = SearchParams(**kwargs)
        if params.datastructure == SourceDataStructureOptions.DEFAULT:
            params.datastructure = SourceDataStructureOptions.FULL
        '''convert boolean to elasticsearch syntax'''
        gene_operator = getattr(BooleanFilterOperator, gene_operator.upper())
        object_operator = getattr(BooleanFilterOperator, object_operator.upper())
        evidence_type_operator = getattr(BooleanFilterOperator, evidence_type_operator.upper())
        '''create multiple condition boolean query'''
        conditions = []
        if targets:
            conditions.append(self._get_complex_gene_filter(targets, gene_operator))
        if diseases:
            conditions.append(self._get_complex_object_filter(diseases, object_operator, is_direct=params.is_direct))
        if evidence_types:
            conditions.append(self._get_complex_evidence_type_filter(evidence_types, evidence_type_operator))
        if datasources or datatypes:
            requested_datasources = []
            if datasources:
                requested_datasources.extend(datasources)
            if datatypes:
                for datatype in datatypes:
                    requested_datasources.extend(self.datatypes.get_datasources(datatype))
            requested_datasources = list(set(requested_datasources))
            conditions.append(
                self._get_complex_datasource_filter_evidencestring(requested_datasources, BooleanFilterOperator.OR))
        if params.pathway:
            pathway_filter = self._get_complex_pathway_filter(params.pathway)
            if pathway_filter:
                conditions.append(pathway_filter)
        if params.uniprot_kw:
            uniprotkw_filter = self._get_complex_uniprot_kw_filter(params.uniprot_kw, BooleanFilterOperator.OR)
            if uniprotkw_filter:
                conditions.append(uniprotkw_filter)  # Proto-oncogene Nucleus
        # if not conditions:
        #     return EmptyPaginatedResult([], params, )
        '''boolean query joining multiple conditions with an AND'''
        source_filter = SourceDataStructureOptions.getSource(params.datastructure)
        if params.fields:
            source_filter["include"] = params.fields

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
            "sort": [{"scores.association_score": {"order": "desc"}}],
            '_source': source_filter,
        }
        res = self.handler.search(index=self._index_data,
                                  # doc_type=self._docname_data,
                                  body=query_body,
                                  timeout="10m",

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


    def get_associations_by_id(self, associationid, **kwargs):

        if isinstance(associationid, str):
            associationid = [associationid]

        params = params = SearchParams(**kwargs)
        if params.datastructure == SourceDataStructureOptions.DEFAULT:
            params.datastructure = SourceDataStructureOptions.FULL

        res = self.handler.search(index=self._index_association,
                                  body={"filter": {
                                            "ids": {"values": associationid},
                                            },
                                        "size" : len(associationid),
                                        }
                                  )
        if res['hits']['total']:
            return SimpleResult(res,
                                params,
                                data = [hit['_source'] for hit in res['hits']['hits']])


    def get_associations(self,
                         genes=[],
                         objects=[],
                         gene_operator='OR',
                         object_operator='OR',
                         **kwargs):
        """
        Get the association scores for the provided target and diseases.
        steps in the process:

        1. get all evidence for matching gene and disease

        2. calculate gene to disease(s) scores

        3. calculate facets limiting for gene and diseases within the selected score range

        4. apply all facets filters to data being returned. (on es use a post_filter)

        5. calculate histogram on filtered data returned
        """
        params = SearchParams(**kwargs)


        '''convert boolean to elasticsearch syntax'''
        gene_operator = getattr(BooleanFilterOperator, gene_operator.upper())
        object_operator = getattr(BooleanFilterOperator, object_operator.upper())
        '''create multiple condition boolean query'''
        aggs = None
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
            filter_data_conditions[FilterTypes.DATASOURCE] = self._get_complex_datasource_filter(requested_datasources,
                                                                                                 BooleanFilterOperator.OR)
        if params.filters[FilterTypes.PATHWAY]:
            pathway_filter = self._get_complex_pathway_filter(params.filters[FilterTypes.PATHWAY])
            if pathway_filter:
                filter_data_conditions[FilterTypes.PATHWAY] = pathway_filter
        if params.filters[FilterTypes.UNIPROT_KW]:
            uniprotkw_filter = self._get_complex_uniprot_kw_filter(params.filters[FilterTypes.UNIPROT_KW],
                                                                   BooleanFilterOperator.OR)
            if uniprotkw_filter:
                filter_data_conditions[FilterTypes.UNIPROT_KW] = uniprotkw_filter
        conditions = self._get_base_association_conditions(objects,
                                                           genes,
                                                           object_operator,
                                                           gene_operator,
                                                           is_direct = params.is_direct,
                                                           # is_direct=(len(genes) == 0) or (len(genes) == 1 and len(
                                                           #     objects) == 1)  # temporary handle here special cases for the ui. it should always be true.
                                                           )
        if objects:
            params.outputstructure = OutputStructureOptions.FLAT  # override datastructure as only flat is available
            aggs = self._get_efo_associations_agg(filters=filter_data_conditions, params=params)
        if genes:
            if not aggs:
                aggs = self._get_gene_associations_agg(filters=filter_data_conditions, params=params)
            full_conditions = copy(conditions)
            full_conditions.extend(filter_data_conditions.values())

        '''boolean query joining multiple conditions with an AND'''
        source_filter = SourceDataStructureOptions.getSource(params.datastructure)
        if params.fields:
            source_filter["include"] = params.fields

        ass_query_body = {
            # restrict the set of datapoints using the target and disease ids
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
            '_source': SourceDataStructureOptions.getSource(params.association_score_method),

            "sort": {params.association_score_method + ".overall": {"order": "desc"}}

        }
        # calculate aggregation using proper ad hoc filters
        if aggs:
            ass_query_body['aggs'] =  aggs
        # filter out the results as requested, this will not be applied to the aggregation
        if filter_data_conditions:
            ass_query_body['post_filter'] = {
                "bool": {
                    "must": filter_data_conditions.values()
                }
            }

        ass_data = self.handler.search(index=self._index_association,
                                       body=ass_query_body,
                                       timeout="20m",
                                       request_timeout=60 * 20,
                                       # routing=use gene here
                                       query_cache=True,
                                       )
        aggregation_results = {}

        if ass_data['timed_out']:
            raise Exception('elasticsearch query timed out')

        associations = [Association(h['_source'], params.association_score_method, self.datatypes)
                        for h in ass_data['hits']['hits']]
                        # for h in ass_data['hits']['hits'] if h['_source']['disease']['id'] != 'cttv_root']
        scores = [a.data for a in associations]
        therapeutic_areas = list(set([i for s in scores for i in s['disease']['therapeutic_area']['codes']]))
        efo_with_data = list(set([a.data['disease']['id'] for a in associations if a._is_direct]))
        if 'aggregations' in ass_data:
            aggregation_results = ass_data['aggregations']

        '''build data structure to return'''
        # if params.datastructure == OutputStructureOptions.FLAT:
        data = self._return_association_flat_data_structures(scores, aggregation_results)
        "TODO: use elasticsearch histogram to get this in the whole dataset ignoring filters??"
        data_distribution = self._get_association_data_distribution([s['association_score'] for s in data['data']])
        data_distribution["total"] = len(data['data'])
        if params.datastructure == OutputStructureOptions.TREE:
            extended_query_body = ass_query_body
            extended_query_body['aggs'] = {}
            extended_query_body["query"]["filtered"]["filter"]["bool"]["must"] = self._get_base_association_conditions(
                therapeutic_areas, genes, object_operator, gene_operator, is_direct=True)
            ta_data = self.handler.search(index=self._index_association,
                                          body=extended_query_body,
                                          timeout="20m",
                                          request_timeout=60 * 20,
                                          # routing=use gene here
                                          query_cache=True,
                                          )
            ta_associations = [Association(h['_source'], params.association_score_method, self.datatypes)
                               for h in ta_data['hits']['hits'] if h['_source']['disease']['id'] != 'cttv_root']
            ta_scores = [a.data for a in ta_associations]
            ta_scores.extend(scores)
            data = self._return_association_tree_data_structures(ta_scores, data, efo_with_data)

        total = len(data['data'])

        # data_distribution["evidence_count"]= datapoints
        aggregation_results['data_distribution'] = data_distribution

        return CountedResult([],
                             params,
                             data['data'],
                             total=total,
                             facets=data['facets'],
                             available_datatypes=self.datatypes.available_datatypes,
                             )

    def _get_complex_gene_filter(self,
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
            if bol == BooleanFilterOperator.OR:
                return {
                    "terms": {"target.id": genes}
                }
            else:
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
                                   is_direct=False):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param objects: list of objects
        :param bol: boolean operator to use for combining filters
        :param is_direct: search in the full efo parent list (True) or just direct links (False)
        :return: boolean filter
        '''
        if objects:
            if bol == BooleanFilterOperator.OR:
                if is_direct:
                    return {"terms": {"disease.id": objects}}
                else:
                    return {"terms": {"private.efo_codes": objects}}


            else:
                if is_direct:
                    return {
                        "bool": {
                            bol: [{
                                      "terms": {
                                          "disease.id": [object]}
                                  }
                                  for object in objects]
                        }

                    }
                else:
                    return {
                        "bool": {
                            bol: [{
                                      "terms": {
                                          "private.efo_codes": [object]}
                                  }
                                  for object in objects]
                        }

                    }
        return dict()

    def _get_score_data_object_filter(self, objects):
        if objects:
            return {"terms": {"disease": objects}}
        return dict()

    def _get_score_data_gene_filter(self, genes):
        if genes:
            return {"terms": {"target": genes}}
        return dict()

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
                                  "private.facets.datatype": [evidence_type]}
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
            return {
                "bool": {
                    bol: [{
                              "terms": {
                                  "private.facets.datasource": [datasource]}
                          }
                          for datasource in datasources]
                }
            }
        return dict()

    def _get_complex_datasource_filter_evidencestring(self, datasources, bol):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param evidence_types: list of dataasource strings
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if datasources:
            return {
                "bool": {
                    bol: [{
                              "terms": {
                                  "sourceID": [datasource]}
                          }
                          for datasource in datasources]
                }
            }
        return dict()

    def _get_complex_pathway_filter(self, pathway_codes):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param pathway_codes: list of pathway_codes strings
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if pathway_codes:
            genes = self._get_genes_for_pathway_code(pathway_codes)
            # if genes:
            #     return self._get_complex_gene_filter(genes, bol)
            return {"bool": {
                "should": [
                    {"terms": {"private.facets.reactome.pathway_code": pathway_codes}},
                    {"terms": {"private.facets.reactome.pathway_type_code": pathway_codes}},
                ]

            }
            }

        return dict()

    def _get_free_text_query(self, searchphrase):
        query_body = {"function_score": {
            "score_mode": "multiply",
            'query': {
                'filtered': {
                    'query': {
                        "bool": {
                            "should": [
                                {"multi_match": {
                                    "query": searchphrase,
                                    "fields": ["title^5",
                                               "description^2",
                                               "efo_synonyms",
                                               "symbol_synonyms",
                                               "approved_symbol",
                                               "approved_name",
                                               "name_synonyms",
                                               "gene_family_description",
                                               "efo_path_labels^0.1",
                                               ],
                                    "analyzer": 'standard',
                                    # "fuzziness": "AUTO",
                                    "tie_breaker": 0.0,
                                    "type": "phrase_prefix",
                                }
                                },
                                {"multi_match": {
                                    "query": searchphrase,
                                    "fields": ["title^3",
                                               "id",
                                               "approved_symbol",
                                               "symbol_synonyms",
                                               "name_synonyms",
                                               "uniprot_accessions",
                                               "hgnc_id",
                                               "ensembl_gene_id",
                                               "efo_path_codes",
                                               "efo_url",
                                               "efo_synonyms^0.1",
                                               ],
                                    "analyzer": 'keyword',
                                    # "fuzziness": "AUTO",
                                    # "tie_breaker": 0.1,
                                    "type": "best_fields",
                                }
                                },
                            ]
                        }
                    },
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
                },
            },
            "functions": [
                # "path_score": {
                  #   "script": "def score=doc['min_path_len'].value; if (score ==0) {score = 1}; 1/score;",
                  #   "lang": "groovy",
                  # },
                  # "script_score": {
                  #   "script": "def score=doc['total_associations'].value; if (score ==0) {score = 1}; score/10;",
                  #   "lang": "groovy",
                  # }
                {
                "field_value_factor":{
                    "field": "association_counts.total",
                    "factor": 0.01,
                    "modifier": "sqrt",
                    "missing": 1,
                    # "weight": 0.01,
                    }
                },
                {
                "field_value_factor":{
                    "field": "min_path_len",
                    "factor": 0.5,
                    "modifier": "reciprocal",
                    "missing": 1,
                    # "weight": 0.5,
                    }
                }
              ],
            # "filter": {
            #     "exists": {
            #       "field": "min_path_len"
            #     }
            #   }


            }

        }

        return query_body

    def _get_free_text_highlight(self):
        return {"fields": {
            "id": {},
            "title": {},
            "description": {},
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
            "efo_path_codes": {},
            "efo_url": {},
            "efo_path_labels": {},
        }
        }

    def _get_gene_associations_agg(self, expand_efo=True, filters={}, params=None):
        facets = params.facets
        aggs = {}
        if facets:
            aggs["datatypes"] = self._get_datatype_facet_aggregation(filters)
        return aggs

    def _get_efo_associations_agg(self, filters={}, params=None):

        facets = params.facets

        gene_related_aggs = self._get_gene_related_aggs(filters)

        aggs = {
        }
        if facets:
            aggs['datatypes'] = self._get_datatype_facet_aggregation(filters)
            aggs['pathway_type'] = gene_related_aggs["pathway_type"]
            aggs['uniprot_keywords'] = gene_related_aggs["uniprot_keywords"]

        return aggs

    def _get_datasource_init_list(self, params=None):
        datatype_list = []  # ["'all':[]"]
        for datatype in self.datatypes.available_datatypes:
            # datatype_list.append("'%s': []"%datatype)
            for datasource in self.datatypes.get_datasources(datatype):
                datatype_list.append("'%s': []" % datasource)
        return ',\n'.join(datatype_list)

    def _get_datatype_combine_init_list(self, params=None):
        datatype_list = ["'all':0"]
        for datatype in self.datatypes.available_datatypes:
            datatype_list.append("'%s': 0" % datatype)
            for datasource in self.datatypes.get_datasources(datatype):
                datatype_list.append("'%s': 0" % datasource)
        return ',\n'.join(datatype_list)

    def _get_complimentary_facet_filters(self, key, filters):
        conditions = []
        for filter_type, filter_value in filters.items():
            if filter_type != key:
                conditions.append(filter_value)
        return conditions

    def _return_association_flat_data_structures(self,
                                                 scores,
                                                 facets):

        if 'datatypes' in facets:
            facets['datatypes'] = facets['datatypes']['data']
        if 'pathway_type' in facets:
            facets['pathway_type'] = facets['pathway_type']['data']
        if 'uniprot_keywords' in facets:
            facets['uniprot_keywords'] = facets['uniprot_keywords']['data']
        facets = self._process_facets(facets)
        return dict(data=scores,
                    facets=facets)

    def _return_association_tree_data_structures(self,
                                                 scores,
                                                 flat_scores,
                                                 efo_with_data=[],
                                                 ):

        def transform_data_to_tree(data, efo_parents, efo_tas, efo_with_data=[]):
            data = dict([(i["disease"]['id'], i) for i in data])
            expanded_relations = []
            for code, paths in efo_parents.items():
                if code in data:
                    for path in paths:
                        expanded_relations.append([code, path])

            efo_tree_relations = sorted(expanded_relations, key=lambda items: len(items[1]))
            root = AssociationTreeNode()
            if not efo_with_data:
                extended_efo_with_data = [code for code, parents in efo_tree_relations]
            else:
                extended_efo_with_data = copy(efo_with_data)
                for code, parents in efo_tree_relations:
                    if len(parents) > 1:
                        ta_code = parents[1]
                        if ta_code not in extended_efo_with_data:
                            extended_efo_with_data.append(ta_code)

            for code, parents in efo_tree_relations:
                if code in extended_efo_with_data:
                    if not parents:
                        root.add_child(AssociationTreeNode(code, **data[code]))
                    else:
                        node = root.get_node_at_path(parents)
                        node.add_child(AssociationTreeNode(code, **data[code]))

            return root.to_dict_tree_with_children_as_array()

        facets = {}
        if scores:

            efo_parents, efo_labels, efo_tas = self._get_efo_data_for_associations([i["disease"]['id'] for i in scores])
            # scores_with_ta = inject_missing_ta(efo_parents, unfiltered_scores, scores)
            tree_data = transform_data_to_tree(scores, efo_parents, efo_tas, efo_with_data) or flat_scores['data']
            facets = flat_scores['facets']
        else:
            tree_data = scores

        return dict(data=tree_data,
                    facets=facets)

    def _get_efo_data_for_associations(self, efo_keys):
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
            parent_labels = {}
            for i, path in enumerate(efo['path_codes']):
                parents.append(path[:-1])
                parent_labels.update(dict(zip(efo['path_codes'][i], efo['path_labels'][i])))
            efo_parents[code] = parents
            efo_labels[code] = efo['label']
            ta = []
            for path in parents:
                if len(path) > 1:
                    if path[1] not in ta:
                        ta.append(path[1])
                        efo_labels[path[1]] = parent_labels[path[1]]
            efo_therapeutic_area[code] = ta
            # if len(efo['path_codes'])>2:
        # efo_labels = get_missing_ta_labels(efo_labels,efo_therapeutic_area)


        return efo_parents, efo_labels, efo_therapeutic_area

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

            source_filter = SourceDataStructureOptions.getSource(params.datastructure)
            if params.fields:
                source_filter["include"] = params.fields

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
                data = dict([(hit['_id'], hit['_source']) for hit in res['hits']['hits']])
                return SimpleResult(res, params, data)

    def _get_efo_with_data(self, conditions):
        efo_with_data = []
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
                                      '_source': ["disease.id"],
                                      "aggs": {"efo_codes": {
                                          "terms": {
                                              "field": "disease.id",
                                              'size': 100000,

                                          },
                                      }
                                      }
                                  })
        if res['hits']['total']:
            data = res['aggregations']["efo_codes"]["buckets"]
            efo_with_data = list(set([i['key'] for i in data]))
        return efo_with_data

    def _get_gene_info_agg(self, filters={}):

        return {
            "pathway_type": {
                "filter": {
                    "bool": {
                        "must": self._get_complimentary_facet_filters(FilterTypes.PATHWAY, filters),
                    }
                },
                "aggs": {
                    "data": {
                        "terms": {
                            "field": "private.facets.reactome.pathway_type_code",
                            'size': 10,
                        },

                        "aggs": {
                            "pathway": {
                                "terms": {
                                    "field": "private.facets.reactome.pathway_code",
                                    'size': 10,
                                },
                            }
                        },
                    }
                }
            }
        }

    def _get_genes_for_pathway_code(self, pathway_codes):
        data = []
        res = self.handler.search(index=self._index_genename,
                                  body={
                                      "query": {
                                          "filtered": {
                                              "filter": {
                                                  "bool": {
                                                      "should": [
                                                          {"terms": {
                                                              "private.facets.reactome.pathway_code": pathway_codes}},
                                                          {"terms": {
                                                              "private.facets.reactome.pathway_type_code": pathway_codes}},
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

    def _process_facets(self, facets):

        reactome_ids = []

        '''get data'''
        for facet in facets:
            if 'buckets' in facets[facet]:
                facet_buckets = facets[facet]['buckets']
                for bucket in facet_buckets:
                    if facet == 'pathway_type':
                        reactome_ids.append(bucket['key'])
                        if 'pathway' in bucket:
                            if 'buckets' in bucket['pathway']:
                                sub_facet_buckets = bucket['pathway']['buckets']
                                for sub_bucket in sub_facet_buckets:
                                    reactome_ids.append(sub_bucket['key'])

        reactome_ids = list(set(reactome_ids))
        reactome_labels = self._get_labels_for_reactome_ids(reactome_ids)

        '''alter data'''
        for facet in facets:
            if 'buckets' in facets[facet]:
                facet_buckets = facets[facet]['buckets']
                for bucket in facet_buckets:
                    if facet == 'pathway_type':  # reactome data
                        bucket['label'] = reactome_labels[bucket['key'].upper()] or bucket['key']
                        if 'pathway' in bucket:
                            if 'buckets' in bucket['pathway']:
                                sub_facet_buckets = bucket['pathway']['buckets']
                                for sub_bucket in sub_facet_buckets:
                                    sub_bucket['label'] = reactome_labels[sub_bucket['key'].upper()] or sub_bucket[
                                        'key']
                    elif facet == 'datatypes':  # need to filter out wrong datasource. an alternative is to map these object as nested in elasticsearch
                        dt = bucket["key"]
                        if 'datasources' in bucket:
                            if 'buckets' in bucket['datasources']:
                                new_sub_buckets = []
                                sub_facet_buckets = bucket['datasources']['buckets']
                                for sub_bucket in sub_facet_buckets:
                                    if sub_bucket['key'] in self.datatypes.get_datasources(dt):
                                        new_sub_buckets.append(sub_bucket)
                                bucket['datasources']['buckets'] = new_sub_buckets

        return facets

    def _get_labels_for_reactome_ids(self, reactome_ids):
        labels = defaultdict(str)
        if reactome_ids:
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
                    labels[hit['_id']] = hit['_source']['label']
        return labels

    def _get_datatype_facet_aggregation(self, filters):

        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.DATASOURCE, filters),
                }
            },
            "aggs": {
                "data": {
                    "terms": {
                        "field": "private.facets.datatype",
                        'size': 10,
                    },
                    "aggs": {
                        "datasources": {
                            "terms": {
                                "field": "private.facets.datasource",
                            },
                            "aggs": {
                                "unique_target_count": {
                                    "cardinality": {
                                        "field": "target.id",
                                        "precision_threshold": 1000},
                                },
                                "unique_disease_count": {
                                    "cardinality": {
                                        "field": "disease.id",
                                        "precision_threshold": 1000},
                                },
                            }
                        },
                        "unique_target_count": {
                            "cardinality": {
                                "field": "target.id",
                                "precision_threshold": 1000},
                        },
                        "unique_disease_count": {
                            "cardinality": {
                                "field": "disease.id",
                                "precision_threshold": 1000},
                        },

                    }
                }
            }
        }

    def _get_pathway_facet_aggregation(self, filters={}):

        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.PATHWAY, filters),
                }
            },
            "aggs": {
                "data": {
                    "terms": {
                        "field": "private.facets.reactome.pathway_type_code",
                        'size': 100,
                    },

                    "aggs": {
                        "pathway": {
                            "terms": {
                                "field": "private.facets.reactome.pathway_code",
                                'size': 10,
                            },
                            "aggs": {
                                "unique_target_count": {
                                    "cardinality": {
                                        "field": "target.id",
                                        "precision_threshold": 1000},
                                },
                                "unique_disease_count": {
                                    "cardinality": {
                                        "field": "disease.id",
                                        "precision_threshold": 1000},
                                },
                            }
                        },
                        "unique_target_count": {
                            "cardinality": {
                                "field": "target.id",
                                "precision_threshold": 1000},
                        },
                        "unique_disease_count": {
                            "cardinality": {
                                "field": "disease.id",
                                "precision_threshold": 1000},
                        },
                    }
                },
            }
        }

    def _get_gene_related_aggs(self, filters):
        return dict(
                pathway_type=self._get_pathway_facet_aggregation(filters),
                go=self._get_go_facet_aggregation(filters),
                uniprot_keywords=self._get_uniprot_keywords_facet_aggregation(filters),

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
            "aggs": {
                "data": {
                    "significant_terms": {
                        "field": "private.facets.uniprot_keywords",
                        'size': 25,
                    },
                    "aggs": {
                        "unique_target_count": {
                            "cardinality": {
                                "field": "target.id",
                                "precision_threshold": 1000},
                        },
                        "unique_disease_count": {
                            "cardinality": {
                                "field": "disease.id",
                                "precision_threshold": 1000},
                        },
                    },
                },
            }
        }

    def _get_uniprot_keywords_facet_aggregation_for_genes(self, filters):
        return {
            "aggs": {
                "data": {
                    "significant_terms": {
                        "field": "uniprot_keywords",
                        'size': 25,
                    },
                    # "aggs": {
                    #     "unique_target_count": {
                    #        "value_count" : {
                    #           "field" : "id",
                    #        },
                    #     },
                    # },
                },
            }

        }

    def _get_association_score_scripted_metric_script(self, params):
        # TODO:  use the scripted metric to calculate association score.
        # TODO: Use script parameters to pass the weights from request.
        # TODO: implement using the max for datatype and overall score in combine and reduce
        return dict(
                init_script="_agg['evs_scores'] = [%s];" % self._get_datasource_init_list(params),
                map_script="""
//get values from entry
ev_type = doc['type'].value;
ev_sourceID = doc['sourceID'].value
ev_score_ds = doc['scores.association_score'].value

// calculate single point score depending on parameters
%s

//store the score value in the proper category
//_agg.evs_scores['all'].add(ev_score_dt)
_agg.evs_scores[ev_sourceID].add(ev_score_ds)
//_agg.evs_scores[ev_type].add(ev_score_dt)
""" % self._get_datasource_score_calculation_script(params),
                combine_script="""
scores = [%s];
// sum all the values coming from a single shard
_agg.evs_scores.each { key, value ->
    for (v in value) {
        scores[key] += v;
        };
    };
return scores""" % self._get_datatype_combine_init_list(params),
                reduce_script="""
//init scores table with available datasource and datatypes
scores = [%s];
//generate a datasource to datatype (ds2dt) map
%s

_aggs.each {
    it.each { key, value ->
        for (v in value) {
            scores['all'] += v;
            scores[key] += v;
            ds2dt[key].each { dt ->
                scores[dt] += v;
                };
            };
        };
    };



// cap each data category sum to 1
scores.each { key, value ->
    if (value > 1) {
        scores[key] = 1;
        };
    };
return scores""" % (self._get_datatype_combine_init_list(params),
                    self._get_datasource_to_datatype_mapping_script(params)),
        )

    def _get_datasource_score_calculation_script(self, params=None):
        template_ds = """if (ev_sourceID == '%s') {
  ev_score_ds = doc['scores.association_score'].value * %f / %f;
  }"""
        script = []
        for ds in self.datatypes.datasources:
            script.append(template_ds % (ds, self.datatource_scoring.weights[ds], params.stringency))

        return '\n'.join(script)

    def _get_datasource_to_datatype_mapping_script(self, params=None):
        script = ['ds2dt = [']
        for ds in self.datatypes.datasources.values():
            script.append("'%s' : %s," % (ds.name, str(ds.datatypes)))

        script.append(']')
        script = '\n'.join(script)
        return script

    def _get_datatype_score_breakdown(self, scores):
        datatype_data = []
        for dt in self.datatypes.datatypes.values():
            dt_score = scores[dt.name]
            if dt_score != 0:
                dt_data = dict(datatype=dt.name,
                               association_score=dt_score,
                               datasources=[]
                               )
                for ds in dt.datasources:
                    ds_score = scores[ds]
                    if ds_score != 0:
                        dt_data['datasources'].append(dict(datasource=ds,
                                                           association_score=ds_score,
                                                           ))
                datatype_data.append(dt_data)

        return datatype_data

    def _get_association_data_distribution(self, scores):
        histogram, bin_edges = np.histogram(scores, 5, (0., 1.))
        distribution = dict(buckets={})
        for i in range(len(bin_edges) - 1):
            distribution['buckets'][round(bin_edges[i], 1)] = {'value': histogram[i]}

        return distribution

    def _get_complex_uniprot_kw_filter(self, kw, bol):
        pass
        '''
        :param kw: list of uniprot kw strings
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if kw:
            genes = self._get_genes_for_uniprot_kw(kw)
            if genes:
                return self._get_complex_gene_filter(genes, bol)
        return dict()

    def _get_genes_for_uniprot_kw(self, kw):
        data = []
        res = self.handler.search(index=self._index_genename,
                                  body={
                                      "query": {
                                          "filtered": {
                                              "filter": {
                                                  "bool": {
                                                      "should": [
                                                          {"terms": {"private.facets.uniprot_keywords": kw}},
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

    def _get_base_association_conditions(self, objects, genes, object_operator, gene_operator, is_direct=False):
        conditions = []
        if objects:
            conditions.append(self._get_complex_object_filter(objects, object_operator, is_direct=True))
        if genes:
            conditions.append(self._get_complex_gene_filter(genes, gene_operator))
        if is_direct:
            conditions.append(self._get_is_direct_filter())

        return conditions


    def _get_is_direct_filter(self):

        return {
            "term": {"is_direct": True}
        }

    def _get_search_doc_types(self, filter):
        doc_types = []
        for t in filter:
            t = t.lower()
            if t == FreeTextFilterOptions.ALL:
                return []
            elif t in FreeTextFilterOptions.__dict__.values():
                doc_types.append(self._docname_search + '-' + t)
        return doc_types

    def _free_text_query(self, searchphrase, doc_types, params):
        return self.handler.search(index=self._index_search,
                                   doc_type=doc_types,
                                   body={'query': self._get_free_text_query(searchphrase),
                                         'size': params.size,
                                         'from': params.start_from,
                                         '_source': SourceDataStructureOptions.getSource(
                                                 SourceDataStructureOptions.FULL),
                                         # "min_score": 0.,
                                         "highlight": self._get_free_text_highlight(),
                                         "explain": current_app.config['DEBUG'],

                                         },

                                   )

    def _get_search_doc_name(self, doc_type):
        return self._docname_search + '-' + doc_type



class SearchParams():
    _max_search_result_limit = 1000
    _default_return_size = 10
    _allowed_groupby = ['gene', 'evidence-type', 'efo']

    def __init__(self, **kwargs):

        self.size = kwargs.get('size', self._default_return_size) or self._default_return_size
        if (self.size > self._max_search_result_limit):
            raise AttributeError('Size cannot be bigger than %i'%self._max_search_result_limit)

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

        self.datastructure = kwargs.get('datastructure',
                                        SourceDataStructureOptions.DEFAULT) or SourceDataStructureOptions.DEFAULT

        self.outputstructure =  kwargs.get('outputstructure',
                                        OutputStructureOptions.FLAT) or OutputStructureOptions.FLAT

        self.fields = kwargs.get('fields')

        if self.fields:
            self.datastructure = SourceDataStructureOptions.CUSTOM

        self.filters = dict()
        self.filters[FilterTypes.ASSOCIATION_SCORE_MIN] = kwargs.get(FilterTypes.ASSOCIATION_SCORE_MIN, 0.2)
        if self.filters[FilterTypes.ASSOCIATION_SCORE_MIN] is None:
            self.filters[FilterTypes.ASSOCIATION_SCORE_MIN] = 0.2
        self.filters[FilterTypes.ASSOCIATION_SCORE_MAX] = kwargs.get(FilterTypes.ASSOCIATION_SCORE_MAX, 1)
        if self.filters[FilterTypes.ASSOCIATION_SCORE_MAX] is None:
            self.filters[FilterTypes.ASSOCIATION_SCORE_MAX] = 1
        self.filters[FilterTypes.DATASOURCE] = kwargs.get(FilterTypes.DATASOURCE)
        self.filters[FilterTypes.DATATYPE] = kwargs.get(FilterTypes.DATATYPE)
        self.filters[FilterTypes.PATHWAY] = kwargs.get(FilterTypes.PATHWAY)
        self.filters[FilterTypes.UNIPROT_KW] = kwargs.get(FilterTypes.UNIPROT_KW)
        # if self.filters[FilterTypes.PATHWAY]:
        #     self.filters[FilterTypes.PATHWAY] = map(str.upper, self.filters[FilterTypes.PATHWAY])

        self.stringency = kwargs.get('stringency', 1.) or 1.  # cannot be zero

        self.pathway = kwargs.get('pathway', []) or []
        self.target_class = kwargs.get('target_class', []) or []
        self.uniprot_kw = kwargs.get('uniprotkw', []) or []
        self.datatype = kwargs.get('datatype', []) or []

        self.is_direct = kwargs.get('direct', False)
        self.facets = kwargs.get('facets', True)
        self.association_score_method = kwargs.get('association_score_method', ScoringMethods.DEFAULT)


class AssociationTreeNode(object):
    ROOT = 'cttv_disease'

    def __init__(self, name=None, **kwargs):
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
                self.children[child.name] = child
        else:
            raise AttributeError("child needs to be an AssociationTreeNode ")

    def del_child(self, child):
        if isinstance(child, AssociationTreeNode):
            if child._is_root():
                raise AttributeError("child cannot be root ")
            if child == self:
                raise AttributeError(" cannot add a node to itself as a child")
            if self.has_child(child):
                del self.children[child.name]
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
            out['children'] = self.children_as_array()
        else:
            del out['children']
        return out

    def recursive_node_to_dict(self, node):
        if isinstance(node, AssociationTreeNode):
            out = node.single_node_to_dict()
            if 'children' in out:
                for i, child in enumerate(out['children']):
                    if isinstance(child, AssociationTreeNode):
                        child = child.recursive_node_to_dict(child)
                    out['children'][i] = child
            return out

    def to_dict_tree_with_children_as_array(self):
        out = self.recursive_node_to_dict(self)
        return out
