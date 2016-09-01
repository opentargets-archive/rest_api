import base64
import hashlib
import pickle
import pprint
from collections import defaultdict
import copy

import logging
import numpy as np
import json

import time

# import ujson as json
import json as json

import sys
from flask import current_app, request
from elasticsearch import helpers
from pythonjsonlogger import jsonlogger
from app.common.request_templates import SourceDataStructureOptions, FilterTypes, \
    AssociationSortOptions, EvidenceSortOptions
from app.common.response_templates import Association, DataStats, Relation, RelationTypes
from app.common.results import PaginatedResult, SimpleResult, CountedResult, EmptyPaginatedResult, RawResult
from app.common.request_templates import FilterTypes
from app.common.scoring import Scorer
from app.common.scoring_conf import ScoringMethods
from config import Config

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


class InternalCache(object):

    NAMESPACE = 'CTTV_REST_API_CACHE'
    def __init__(self, r_server,
                 app_version = '',
                 default_ttl = 60):
        self.r_server  = r_server
        self.app_version = app_version
        self.default_ttl = default_ttl

    def get(self, key):
        value = self.r_server.get(self._get_namespaced_key(key))
        if value:
            return self._decode(value)

    def set(self, key, value, ttl = None):
        k = self._get_namespaced_key(key)
        v = self._encode(value)
        return self.r_server.setex(self._get_namespaced_key(key),
                                   self._encode(value),
                                   ttl or self.default_ttl)

    def _get_namespaced_key(self, key):
        #try cityhash for better performance (fast and non cryptographic hash library) from cityhash import CityHash64
        # hashed_key = hashlib.md5(key).digest().encode('base64')[:8]
        hashed_key = hashlib.md5(key).hexdigest()
        return ':'.join([self.NAMESPACE, self.app_version, hashed_key])

    def _encode(self, obj):
        # return base64.encodestring(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL))
        return json.dumps(obj)

    def _decode(self, obj):
        # return pickle.loads(base64.decodestring(obj))
        return json.loads(obj)


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
                 index_relation=None,
                 docname_data=None,
                 docname_efo=None,
                 docname_eco=None,
                 docname_genename=None,
                 docname_expression=None,
                 docname_reactome=None,
                 docname_association=None,
                 docname_search=None,
                 docname_relation=None,
                 cache = None,
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
        self._index_relation = index_relation

        self._docname_data = docname_data
        self._docname_efo = docname_efo
        self._docname_eco = docname_eco
        self._docname_genename = docname_genename
        self._docname_expression = docname_expression
        self._docname_reactome = docname_reactome
        self._docname_association = docname_association
        self._docname_search = docname_search
        self._docname_relation = docname_relation
        self.datatypes = datatypes
        self.datatource_scoring = datatource_scoring
        self.scorer = Scorer(datatource_scoring)
        self.cache = cache

        if log_level == logging.DEBUG:
            formatter = jsonlogger.JsonFormatter()
            # es_logger = logging.getLogger('elasticsearch')
            # for handler in es_logger.handlers:
            #     handler.setFormatter(formatter)
            # es_logger.setLevel(logging.DEBUG)
            # es_tracer = logging.getLogger('elasticsearch.trace')
            # es_tracer.setLevel(logging.DEBUG)
            # # es_tracer.addHandler(logging.FileHandler('es_trace.log'))
            # for handler in es_tracer.handlers:
            #     handler.setFormatter(formatter)

    def free_text_search(self, searchphrase,
                         doc_filter=(FreeTextFilterOptions.ALL),
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
                    res_opt = self._free_text_query(searchphrase, self._get_search_doc_types([opt]), params)
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
                                           "field": "private.suggestions"
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
            res = self._cached_search(index=self._index_genename,
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
        if not isinstance(efo_codes, list):
            efo_codes = [efo_codes]
        if efo_codes:
            res = self._cached_search(index=self._index_efo,
                                      doc_type=self._docname_efo,
                                      body={'query': {
                                              "ids": {
                                                  "values": efo_codes
                                              },
                                          },
                                          'size': 10000
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

        params = SearchParams(**kwargs)
        if params.datastructure == SourceDataStructureOptions.DEFAULT:
            params.datastructure = SourceDataStructureOptions.FULL

        res = self._cached_search(index=self._index_data,
                                  # doc_type=self._docname_data,
                                  body={"filter": {
                                            "ids": {"values": evidenceid},
                                            },
                                        "size" : len(evidenceid),
                                        }
                                  )
        return SimpleResult(res,
                            params,
                            data = [hit['_source'] for hit in res['hits']['hits']])

    def get_label_for_eco_code(self, code):
        res = self._cached_search(index=self._index_eco,
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
            conditions.append(self.get_complex_target_filter(targets, gene_operator))
        if diseases:
            conditions.append(self.get_complex_disease_filter(diseases, object_operator, is_direct=False))#temporary until params.is_direct is supported again
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
        if params.filters[FilterTypes.SCORE_RANGE][1] < 1 or \
                params.filters[FilterTypes.SCORE_RANGE][0] >0 :
            score_filter = self._get_evidence_score_range_filter(params)
            if score_filter:
                conditions.append(score_filter)
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
                        },
                    }
                }
            },
            'size': params.size,
            'from': params.start_from,
            "sort": self._digest_sort_strings(params),
            '_source': source_filter,
        }
        res = self._cached_search(index=self._index_data,
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

        params = SearchParams(**kwargs)
        if params.datastructure == SourceDataStructureOptions.DEFAULT:
            params.datastructure = SourceDataStructureOptions.FULL

        res = self._cached_search(index=self._index_association,
                                  body={"filter": {
                                            "ids": {"values": associationid},
                                            },
                                        "size" : len(associationid),
                                        'from': params.start_from,
                                        }
                                  )
        data = [Association(a,
                            params.association_score_method,
                            self.datatypes,
                            cap_scores=params.cap_scores).data
                    for a in res['hits']['hits']]

        return PaginatedResult(res,
                               params,
                               data)


    def get_associations(self,
                         **kwargs):
        """
        Get the association scores for the provided target and diseases.
        steps in the process:


        """
        params = SearchParams(**kwargs)

        '''create multiple condition boolean query'''

        agg_builder = AggregationBuilder(self)
        agg_builder.load_params(params)
        aggs = agg_builder.aggs
        filter_data_conditions = agg_builder.filters

        '''boolean query joining multiple conditions with an AND'''
        query_body = { "match_all": {}}
        if params.search:
            query_body = { "wildcard": { "_all":  '%s*'%params.search } }#could use '*%*' to match anywhere, but it is a very slow query

        if params.datastructure in [SourceDataStructureOptions.FULL, SourceDataStructureOptions.DEFAULT]:
            params.datastructure = SourceDataStructureOptions.SCORE
        source = SourceDataStructureOptions.getSource(params.datastructure, params)
        if 'include' in source:
            params.requested_fields = source['include']
        ass_query_body = {
            # restrict the set of datapoints using the target and disease ids
            "query" : query_body,
            'size': params.size,
            '_source': source,
            'from': params.start_from,
            "sort": self._digest_sort_strings(params)

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

        ass_data = self._cached_search(index=self._index_association,
                                       body=ass_query_body,
                                       timeout="20m",
                                       request_timeout=60 * 20,
                                       # routing=use gene here
                                       query_cache=True,
                                       )
        aggregation_results = {}

        if ass_data['timed_out']:
            raise Exception('elasticsearch query timed out')


        associations = (Association(h,
                                    params.association_score_method,
                                    self.datatypes,
                                    cap_scores=params.cap_scores)
                        for h in ass_data['hits']['hits'])
                        # for h in ass_data['hits']['hits'] if h['_source']['disease']['id'] != 'cttv_root']
        scores = [a.data for a in associations if a.data]
        # efo_with_data = list(set([a.data['disease']['id'] for a in associations if a.is_direct]))
        if 'aggregations' in ass_data:
            aggregation_results = ass_data['aggregations']

        '''build data structure to return'''
        data = self._return_association_flat_data_structures(scores, aggregation_results)
        # "TODO: use elasticsearch histogram to get this in the whole dataset ignoring filters??"
        # data_distribution = self._get_association_data_distribution([s['association_score'] for s in data['data']])
        # data_distribution["total"] = len(data['data'])
        if params.is_direct and params.target:
            try:
                therapeutic_areas = set()
                for s in scores:
                    for ta_code in s['disease']['efo_info']['therapeutic_area']['codes']:
                        therapeutic_areas.add(s['target']['id'] + '-' + ta_code)
                therapeutic_areas = list(therapeutic_areas)
                ta_data = self._cached_search(index=self._index_association,
                                              body={"filter": {
                                                        "ids": {"values": therapeutic_areas},
                                                    },
                                                    "size": 1000,
                                                    '_source': source,
                                                    },
                                                )
                ta_associations = (Association(h,
                                               params.association_score_method,
                                               self.datatypes,
                                               cap_scores=params.cap_scores
                                               )
                                   for h in ta_data['hits']['hits'] if h['_source']['disease']['id'] != 'cttv_root')
                ta_scores = [a.data for a in ta_associations]
                # ta_scores.extend(scores)


                return PaginatedResult(ass_data,
                                     params,
                                     data['data'],
                                     facets=data['facets'],
                                     available_datatypes=self.datatypes.available_datatypes,
                                     therapeutic_areas = ta_scores
                                     )
            except KeyError:
                current_app.logger.debug('fields containing therapeutic area information not available')
        return PaginatedResult(ass_data,
                                 params,
                                 data['data'],
                                 facets=data['facets'],
                                 available_datatypes=self.datatypes.available_datatypes,
                                 )

    def get_complex_target_filter(self,
                                  targets,
                                  bol=BooleanFilterOperator.OR,
                                  include_negative=False,
                                  ):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param targets: list of genes
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        targets=self._resolve_negable_parameter_set(targets, include_negative)
        if targets:
            if bol == BooleanFilterOperator.OR:
                return {
                    "terms": {"target.id": targets}
                }
            else:
                return {
                    "bool": {
                        bol: [{
                                  "terms": {
                                      "target.id": [target]}
                              }
                              for target in targets]
                    }
                }
        return dict()

    def get_complex_subject_filter(self,
                                  subject_ids,
                                  bol=BooleanFilterOperator.OR,
                                  include_negative=False,
                                  ):


        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param subject_ids: list of ids as subject
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        subject_ids = self._resolve_negable_parameter_set(subject_ids, include_negative)
        if subject_ids:
            if bol == BooleanFilterOperator.OR:
                return {
                    "terms": {"subject.id": subject_ids}
                }
            else:
                return {
                    "bool": {
                        bol: [{
                                  "terms": {
                                      "subject.id": [subject_id]}
                              }
                              for subject_id in subject_ids]
                    }
                }
        return dict()

    def get_complex_disease_filter(self,
                                   diseases,
                                   bol=BooleanFilterOperator.OR,
                                   is_direct=False,
                                   include_negative=False,
                                   ):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param diseases: list of objects
        :param bol: boolean operator to use for combining filters
        :param is_direct: search in the full efo parent list (True) or just direct links (False)
        :return: boolean filter
        '''
        diseases=self._resolve_negable_parameter_set(diseases, include_negative)
        if diseases:
            if bol == BooleanFilterOperator.OR:
                if is_direct:
                    return {"terms": {"disease.id": diseases}}
                else:
                    return {"terms": {"private.efo_codes": diseases}}


            else:
                if is_direct:
                    return {
                        "bool": {
                            bol: [{
                                      "terms": {
                                          "disease.id": [disease]}
                                  }
                                  for disease in diseases]
                        }

                    }
                else:
                    return {
                        "bool": {
                            bol: [{
                                      "terms": {
                                          "private.efo_codes": [disease]}
                                  }
                                  for disease in diseases]
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
                                    "fields": ["name^3",
                                               "description^2",
                                               "efo_synonyms",
                                               "symbol_synonyms",
                                               "approved_symbol",
                                               "approved_name",
                                               "name_synonyms",
                                               "gene_family_description",
                                               "efo_path_labels^0.1",
                                               "ortholog.*.symbol^0.5",
                                               "ortholog.*.name^0.2"
                                               ],
                                    "analyzer": 'standard',
                                    # "fuzziness": "AUTO",
                                    "tie_breaker": 0.0,
                                    "type": "phrase_prefix",
                                    }
                                },
                                {"multi_match": {
                                    "query": searchphrase,
                                    "fields": ["name^3",
                                               "description^2",
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
                                               "ortholog.*.symbol^0.5",
                                               "ortholog.*.id",
                                               ],
                                    "analyzer": 'keyword',
                                    # "fuzziness": "AUTO",
                                    "tie_breaker": 0,
                                    "type": "best_fields",
                                    },
                                },
                                # {"multi_match": {
                                #     "query": searchphrase,
                                #     "fields": ["name^3",
                                #                "description",
                                #                "approved_symbol",
                                #                "symbol_synonyms",
                                #                "name_synonyms",
                                #                "efo_synonyms^0.1",
                                #                "ortholog.*.symbol^0.5",
                                #                "ortholog.*.name^0.2"
                                #                ],
                                #     "word_delimiter_analyzer":{
                                #         "tokenizer":"whitespace",
                                #         "filter":[
                                #             "lowercase",
                                #             "word_delimiter"
                                #
                                #         ],
                                #         "ignore_case":True,
                                #     },
                                #     # "fuzziness": "AUTO",
                                #     "tie_breaker": 0,
                                #     "type": "best_fields",
                                #     }
                                # },
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
                # {
                # "field_value_factor":{
                #     "field": "min_path_len",
                #     "factor": 0.5,
                #     "modifier": "reciprocal",
                #     "missing": 1,
                #     # "weight": 0.5,
                #     }
                # }
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
            "ortholog.*.symbol": {},
            "ortholog.*.name": {},
            "ortholog.*.id":{}
        }
        }


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


    def _return_association_flat_data_structures(self,
                                                 scores,
                                                 facets):

        for facet_type in FilterTypes.__dict__.values():
            if facet_type in facets:
                facets[facet_type] = facets[facet_type]['data']
        if facets:
            facets = self._process_facets(facets)
        return dict(data=scores,
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

            res = self._cached_search(index=self._index_expression,
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
            data = dict([(hit['_id'], hit['_source']) for hit in res['hits']['hits']])
            return SimpleResult(res, params, data)

    def _get_efo_with_data(self, conditions):
        efo_with_data = []
        res = self._cached_search(index=self._index_data,
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
                                      'size': 10000,
                                      '_source': ["disease.id"],
                                      "aggs": {"efo_codes": {
                                          "terms": {
                                              "field": "disease.id",
                                              'size': 10000,

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
            "pathway": {
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
        res = self._cached_search(index=self._index_genename,
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
                                      'size': 10000,
                                      '_source': ["id"],

                                  })
        if res['hits']['total']:
            data = [hit['_id'] for hit in res['hits']['hits']]
        return data

    def _process_facets(self, facets):

        reactome_ids = []
        therapeutic_areas = []

        '''get data'''
        for facet in facets:
            if 'buckets' in facets[facet]:
                facet_buckets = facets[facet]['buckets']
                for bucket in facet_buckets:
                    if facet == FilterTypes.PATHWAY:
                        reactome_ids.append(bucket['key'])
                        if 'pathway' in bucket:
                            if 'buckets' in bucket['pathway']:
                                sub_facet_buckets = bucket['pathway']['buckets']
                                for sub_bucket in sub_facet_buckets:
                                    reactome_ids.append(sub_bucket['key'])
                    elif facet == FilterTypes.THERAPEUTIC_AREA:
                        therapeutic_areas.append(bucket['key'].upper())

        reactome_ids = list(set(reactome_ids))
        reactome_labels = self._get_labels_for_reactome_ids(reactome_ids)
        efo_data = self.get_efo_info_from_code(therapeutic_areas)
        therapeutic_area_labels = {}
        if efo_data:
            therapeutic_area_labels = dict([(efo['path_codes'][0][-1], efo['label']) for efo in efo_data])

        '''alter data'''
        for facet in facets:
            if 'buckets' in facets[facet]:
                facet_buckets = facets[facet]['buckets']
                for bucket in facet_buckets:
                    if facet == FilterTypes.PATHWAY:  # reactome data
                        bucket['label'] = reactome_labels[bucket['key'].upper()] or bucket['key']
                        if 'pathway' in bucket:
                            if 'buckets' in bucket['pathway']:
                                sub_facet_buckets = bucket['pathway']['buckets']
                                for sub_bucket in sub_facet_buckets:
                                    sub_bucket['label'] = reactome_labels[sub_bucket['key'].upper()] or sub_bucket[
                                        'key']
                    elif facet == FilterTypes.DATATYPE:  # need to filter out wrong datasource. an alternative is to map these object as nested in elasticsearch
                        dt = bucket["key"]
                        if 'datasource' in bucket:
                            if 'buckets' in bucket['datasource']:
                                new_sub_buckets = []
                                sub_facet_buckets = bucket['datasource']['buckets']
                                for sub_bucket in sub_facet_buckets:
                                    if sub_bucket['key'] in self.datatypes.get_datasources(dt):
                                        new_sub_buckets.append(sub_bucket)
                                bucket['datasource']['buckets'] = new_sub_buckets
                    elif facet == FilterTypes.THERAPEUTIC_AREA:
                        try:
                            bucket['label'] = therapeutic_area_labels[bucket['key'].upper()]
                        except KeyError:
                            try:
                                bucket['label'] = therapeutic_area_labels[bucket['key']]
                            except KeyError:
                                bucket['label'] = bucket['key']

        return facets

    def _get_labels_for_reactome_ids(self, reactome_ids):
        labels = defaultdict(str)
        if reactome_ids:
            res = self._cached_search(index=self._index_reactome,
                                      doc_type=self._docname_reactome,
                                      body={"query": {
                                              "ids": {
                                                  "values": reactome_ids
                                                  }
                                              },
                                          '_source': {"include": ['label']},
                                          'size': 10000,
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



    def get_genes_for_uniprot_kw(self, kw):
        data = []
        res = self._cached_search(index=self._index_genename,
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
                                      'size': 10000,
                                      '_source': ["id"],

                                  })
        if res['hits']['total']:
            data = [hit['_id'] for hit in res['hits']['hits']]
        return data

    def _get_base_association_conditions(self, objects, genes, object_operator, gene_operator, is_direct=False):
        conditions = []
        if objects:
            conditions.append(self.get_complex_disease_filter(objects, object_operator, is_direct=True))
        if genes:
            conditions.append(self.get_complex_target_filter(genes, gene_operator))
        if is_direct:
            conditions.append(self._get_is_direct_filter())

        return conditions




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
        return self._cached_search(index=self._index_search,
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


    def get_stats(self):

        stats = DataStats()
        stats.add_evidencestring(self._cached_search(index=self._index_data,
                                  # doc_type=self._docname_data,
                                  body= {"query": {"match_all":{}},
                                         "aggs" : {
                                            "data": {
                                                "terms": {
                                                    "field": "type",
                                                    'size': 10,
                                                },
                                                "aggs": {
                                                    "datasources": {
                                                        "terms": {
                                                            "field": "sourceID",
                                                        },
                                                    }
                                                }
                                            }
                                         },
                                         'size': 0,
                                         '_source': False,
                                    },
                                  timeout="10m",
                                      )
                                 )

        stats.add_associations(self._cached_search(index=self._index_association,
                                  # doc_type=self._docname_data,
                                  body= {"query": {"match_all":{}},
                                         "aggs" : {
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
                                                    }
                                                }
                                            }
                                         },
                                         'size': 0,
                                         '_source': False,
                                    },
                                  timeout="10m",
                                      ),
                               self.datatypes
                                 )

        target_count =self._cached_search(index=self._index_search,
                                  doc_type=self._docname_search+'-target',
                                  body= {"query": {
                                           "range" : {
                                                "association_counts.total" : {
                                                   "gt" : 0,
                                                    }
                                                }
                                          },
                                         'size': 0,
                                         '_source': False,
                                    })
        stats.add_key_value('targets', target_count['hits']['total'])

        disease_count =self._cached_search(index=self._index_search,
                                  doc_type=self._docname_search+'-disease',
                                  body= {"query": {
                                           "range" : {
                                                "association_counts.total" : {
                                                   "gt" : 0,
                                                    }
                                                }
                                          },
                                         'size': 0,
                                         '_source': False,
                                    })
        stats.add_key_value('diseases', disease_count['hits']['total'])


        return RawResult(str(stats))

    def _digest_sort_strings(self, params):
        digested=[]
        for s in params.sort:
            order = 'desc'
            if s.startswith('~'):
                order = 'asc'
                s=s[1:]
            if s.startswith('association_score'):
                s= s.replace('association_score', params.association_score_method)
            digested.append({s : {"order": order}})
        return digested



    def _get_evidence_score_range_filter(self, params):
        return {
                "range" : {
                    'scores.association_score' : {
                        "gt": params.filters[FilterTypes.SCORE_RANGE][0],
                        "lte": params.filters[FilterTypes.SCORE_RANGE][1]
                        }
                    }
                }

    def _cached_search(self, *args, **kwargs):
        key = str(args)+str(kwargs)
        no_cache = Config.NO_CACHE_PARAMS in request.values
        res = None
        if not no_cache:
            res = self.cache.get(key)
        if res is None:
            start_time = time.time()
            res = self.handler.search(*args,**kwargs)
            took = int(round(time.time() - start_time))
            self.cache.set(key, res, took*60)
        return res

    def _resolve_negable_parameter_set(self, params, include_negative=False):
        filtered_params =[]
        for p in params:#handle negative sets
            if p.startswith('!'):
                if include_negative:
                    filtered_params.append(p[1:])
            else:
                filtered_params.append(p)
        return filtered_params

    def _get_complex_uniprot_kw_filter(self, kw, bol):
        pass
        '''
        :param kw: list of uniprot kw strings
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if kw:
            genes = self.handler.get_genes_for_uniprot_kw(kw)
            if genes:
                return self.handler.get_complex_target_filter(genes, bol)
        return dict()


    def _get_complex_pathway_filter(self, pathway_codes):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param pathway_codes: list of pathway_codes strings
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if pathway_codes:
            # genes = self.handler._get_genes_for_pathway_code(pathway_codes)
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

    def get_relations(self, subject_ids, **kwargs):
        params = SearchParams(**kwargs)
        # query_body = {"match_all": {}}
        # if params.search:
        #     query_body = {"match_phrase_prefix": {"_all": {"query": params.search}}}

        query_body = {
            "query": self.get_complex_subject_filter(subject_ids),
            'size': params.size,
            'from': params.start_from,
            "sort": self._digest_sort_strings(params),
            '_source': True,

            }


        res = self._cached_search(index=self._index_relation,
                                    body=query_body,
                                      )
        data = []
        if res['hits']['total']:
            for hit in res['hits']['hits']:
                d = hit['_source']
                r = Relation(**d)
                r.value = d['scores']['euclidean']
                data.append(r.to_dict())

        return PaginatedResult(res,
                               params,
                               data,
                               )


    def get_targets_related_to_target(self, target_id):

        disease_profile = self._get_associated_diseases([target_id])
        scored_relations = self._get_associated_target_for_disease_profile(disease_profile)
        # scored_relations = self._score_relation(target_id,matching_targets)

        relations = [Relation(target_id,i[0],RelationTypes.SHARED_DISEASES,value=i[1]).to_dict() for i in scored_relations[:100]]
        return CountedResult(None, data =relations)

    def _get_associated_diseases(self, target_ids):
        data = []
        res = self._cached_search(index=self._index_association,
                                  body={
                                      "query": {
                                          "filtered": {
                                              "filter": {
                                                  "bool": {
                                                      "must": [
                                                          self.get_complex_target_filter(target_ids),
                                                          {"term": {"is_direct": True}},
                                                          {"range": { "harmonic-sum.overall": {
                                                                        "gte": 0.1,
                                                                        }
                                                                    }
                                                          }
                                                      ]
                                                  }
                                              }
                                          }
                                      },
                                      'size': 10000,
                                      '_source': ["disease.id", "harmonic-sum.overall"],

                                  })
        if res['hits']['total']:
            data = dict([[hit['_source']['disease']['id'], hit['_source']['harmonic-sum']['overall']] for hit in res['hits']['hits']])
        return data

    def _get_associated_target_for_disease_profile(self, disease_profile):
        def cap_float(f):
            if f>1:
                return 1.
            return f
        data = []

        res = helpers.scan(client=self.handler,
                           query={
                               "query": {
                                   "filtered": {
                                       "filter": {
                                           "bool": {
                                               "must": [
                                                   self.get_complex_disease_filter(disease_profile.keys(),
                                                                                   is_direct=True),
                                                   {"range": {"harmonic-sum.overall": {
                                                       "gte": 0.1,
                                                        }
                                                    }
                                                   }
                                               ]
                                           }
                                       }
                                   }
                               },
                               'size': 10000,
                               '_source': ["target.id", "disease.id", "harmonic-sum.overall"],

                           },
                           scroll='1h',
                           # doc_type=Config.ELASTICSEARCH_VALIDATED_DATA_DOC_NAME,
                           index=self._index_association,
                           timeout="10m",
                           )


        scored_targets = dict()
        for hit in res:
            # print hit['_source']['harmonic-sum']['overall'], disease_profile[hit['_source']['disease']['id']], (1-cap_float(abs(hit['_source']['harmonic-sum']['overall']-disease_profile[hit['_source']['disease']['id']])))/len(disease_profile)
            target = hit['_source']['target']['id']
            score = (1-cap_float(abs(hit['_source']['harmonic-sum']['overall']-disease_profile[hit['_source']['disease']['id']])))/len(disease_profile)
            if target not in scored_targets:
                scored_targets[target] = 0.
            scored_targets[target] += score
        if scored_targets:
            data = sorted(scored_targets.items(), key=lambda x: x[1], reverse=True)
        return data

    def get_diseases_related_to_disease(self, disease_id):

        target_profile = self._get_associated_targets([disease_id])
        scored_relations = self._get_associated_diseases_for_target_profile(target_profile)

        relations = [Relation(disease_id, i[0], RelationTypes.SHARED_TARGETS, value=i[1]).to_dict() for i in
                     scored_relations[:100]]
        return CountedResult(None, data=relations)

    def _get_associated_targets(self, disease_ids):
        data = []
        res = self._cached_search(index=self._index_association,
                                  body={
                                      "query": {
                                          "filtered": {
                                              "filter": {
                                                  "bool": {
                                                      "must": [
                                                          self.get_complex_disease_filter(disease_ids, is_direct=True),
                                                          {"term": {"is_direct": True}},
                                                          {"range": {"harmonic-sum.overall": {
                                                              "gte": 0.1,
                                                          }
                                                          }
                                                          }
                                                      ]
                                                  }
                                              }
                                          }
                                      },
                                      'size': 10000,
                                      '_source': ["target.id", "harmonic-sum.overall"],

                                  })
        if res['hits']['total']:
            data = dict([[hit['_source']['target']['id'], hit['_source']['harmonic-sum']['overall']] for hit in
                         res['hits']['hits']])
        return data

    def _get_associated_diseases_for_target_profile(self, target_profile):
        def cap_float(f):
            if f > 1:
                return 1.
            return f

        data = []

        res = helpers.scan(client=self.handler,
                           query={
                               "query": {
                                   "filtered": {
                                       "filter": {
                                           "bool": {
                                               "must": [
                                                   self.get_complex_target_filter(target_profile.keys()),
                                                   {"range": {"harmonic-sum.overall": {
                                                       "gte": 0.1,
                                                   }
                                                   }
                                                   }
                                               ]
                                           }
                                       }
                                   }
                               },
                               'size': 10000,
                               '_source': ["target.id", "disease.id", "harmonic-sum.overall"],

                           },
                           scroll='1h',
                           # doc_type=Config.ELASTICSEARCH_VALIDATED_DATA_DOC_NAME,
                           index=self._index_association,
                           timeout="10m",
                           )


        scored_diseases = dict()
        for hit in res:
            # print hit['_source']['harmonic-sum']['overall'], disease_profile[hit['_source']['disease']['id']],
            # (1-cap_float(abs(hit['_source']['harmonic-sum']['overall']-disease_profile[hit['_source']['disease'][
            # 'id']])))/len(disease_profile)
            disease = hit['_source']['disease']['id']
            score = (1 - cap_float(abs(
                hit['_source']['harmonic-sum']['overall'] - target_profile[hit['_source']['target']['id']]))) / len(
                target_profile)
            if disease not in scored_diseases:
                scored_diseases[disease] = 0.
            scored_diseases[disease] += score
        if scored_diseases:
            data = sorted(scored_diseases.items(), key=lambda x: x[1], reverse=True)
        return data


class SearchParams():
    _max_search_result_limit = 10000
    _default_return_size = 10
    _allowed_groupby = ['gene', 'evidence-type', 'efo']

    def __init__(self, **kwargs):

        self.sortmethod = None
        self.size = kwargs.get('size', self._default_return_size)
        if self.size is None:
            self.size =  self._default_return_size
        if (self.size > self._max_search_result_limit):
            raise AttributeError('Size cannot be bigger than %i'%self._max_search_result_limit)

        self.start_from = kwargs.get('from', 0) or 0
        self._max_score = 1e6
        self.cap_scores = kwargs.get('cap_scores', True)
        if self.cap_scores is None:
            self.cap_scores = True
        if self.cap_scores:
            self._max_score = 1e6

        self.groupby = []
        groupby = kwargs.get('groupby')
        if groupby:
            for g in groupby:
                if g in self._allowed_groupby:
                    self.groupby.append(g)


        self.sort = kwargs.get('sort', [ScoringMethods.DEFAULT+'.'+AssociationSortOptions.OVERALL]) or [ScoringMethods.DEFAULT+'.'+AssociationSortOptions.OVERALL]
        self.search = kwargs.get('search')

        self.gte = kwargs.get('gte')

        self.lt = kwargs.get('lt')

        self.format = kwargs.get('format', 'json') or 'json'

        self.datastructure = kwargs.get('datastructure',
                                        SourceDataStructureOptions.DEFAULT) or SourceDataStructureOptions.DEFAULT


        self.fields = kwargs.get('fields')
        self.requested_fields = None # to be populated after

        if self.fields:
            self.datastructure = SourceDataStructureOptions.CUSTOM

        self.filters = dict()
        self.filters[FilterTypes.TARGET] = kwargs.get(FilterTypes.TARGET)
        self.filters[FilterTypes.DISEASE] = kwargs.get(FilterTypes.DISEASE)
        self.filters[FilterTypes.THERAPEUTIC_AREA] = kwargs.get(FilterTypes.THERAPEUTIC_AREA)
        score_range = [0.,self._max_score]
        score_min =  kwargs.get(FilterTypes.ASSOCIATION_SCORE_MIN, 0.)
        if score_min is not  None:
            score_range[0] = score_min
        score_max = kwargs.get(FilterTypes.ASSOCIATION_SCORE_MAX, self._max_score)
        if score_max == 1:#temporary fix until max score cap can be done in elasticsearch
            score_max = self._max_score
        if score_max is not None:
            score_range[1] = score_max
        self.filters[FilterTypes.SCORE_RANGE] = score_range
        self.scorevalue_types = kwargs.get('scorevalue_types', [AssociationSortOptions.OVERALL]) or [AssociationSortOptions.OVERALL]
        self.filters[FilterTypes.PATHWAY] = kwargs.get(FilterTypes.PATHWAY)
        self.filters[FilterTypes.UNIPROT_KW] = kwargs.get(FilterTypes.UNIPROT_KW)
        self.filters[FilterTypes.IS_DIRECT] = kwargs.get(FilterTypes.IS_DIRECT)
        self.filters[FilterTypes.ECO] = kwargs.get(FilterTypes.ECO)


        datasource_filter = []
        ds_params = kwargs.get(FilterTypes.DATASOURCE)
        if ds_params is not None:
            datasource_filter.extend(ds_params)
        dt_params = kwargs.get(FilterTypes.DATATYPE)
        if dt_params is not None:
            datasource_filter.extend(dt_params)
        if datasource_filter == []:
            datasource_filter = None
        self.filters[FilterTypes.DATATYPE] = datasource_filter

        #required for evidence query. TODO: harmonise it with the filters in association endpoint
        self.pathway = kwargs.get('pathway', []) or []
        self.target_class = kwargs.get('target_class', []) or []
        self.uniprot_kw = kwargs.get('uniprotkw', []) or []
        self.datatype = kwargs.get('datatype', []) or []
        self.is_direct = kwargs.get('direct', False)
        self.target = kwargs.get('target', []) or []
        self.disease = kwargs.get('disease', []) or []
        self.eco = kwargs.get('eco', []) or []

        self.facets = kwargs.get('facets', False) or False
        self.association_score_method = kwargs.get('association_score_method', ScoringMethods.DEFAULT)


class AggregationUnit(object):
    '''
    base unit to build an aggregation query
    to be subclassed by implementations
    '''

    def __init__(self,
                 filter,
                 params,
                 handler,
                 compute_aggs = False):
        self.filter = filter
        self.params = params
        self.handler = handler
        self.compute_aggs = compute_aggs
        self.query_filter = {}
        self.agg = {}
        self.build_query_filter()

    def _get_complimentary_facet_filters(self, key, filters):
        conditions = []
        for filter_type, filter_value in filters.items():
            if filter_type != key:
                conditions.append(filter_value)
        return conditions


    def build_query_filter(self):
        raise NotImplementedError


    def build_agg(self, filters):
        pass
        # raise NotImplementedError

class AggregationUnitTarget(AggregationUnit):

    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter= self.handler.get_complex_target_filter(self.filter)

    def build_agg(self, filters):
        self.agg = self._get_target_facet_aggregation(filters)

    def _get_target_facet_aggregation(self, filters):
        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.TARGET, filters),
                }
            },
            "aggs": {
                "data": {
                    "terms": {
                        "field": "target.id",
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
            }
        }

class AggregationUnitDisease(AggregationUnit):

    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self.handler.get_complex_disease_filter(self.filter, is_direct=True)

    def build_agg(self, filters):
        self.agg = self._get_disease_facet_aggregation(filters)

    def _get_disease_facet_aggregation(self, filters):
        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.DISEASE, filters),
                }
            },
            "aggs": {
                "data": {
                    "terms": {
                        "field": "disease.id",
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
            }
        }

class AggregationUnitTherapeuticArea(AggregationUnit):

    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self._get_complex_therapeutic_area_filter(self.filter)

    def build_agg(self, filters):
        self.agg = self._get_disease_facet_aggregation(filters)

    def _get_disease_facet_aggregation(self, filters):
        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.THERAPEUTIC_AREA, filters),
                }
            },
            "aggs": {
                "data": {
                    "terms": {
                        "field" : "disease.efo_info.therapeutic_area.codes",
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
                    }
                },
            }
        }

    def _get_complex_therapeutic_area_filter(self, filter):
        return {"terms": {"disease.efo_info.therapeutic_area.codes": filter}}


class AggregationUnitIsDirect(AggregationUnit):

    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self._get_is_direct_filter(self.filter)

    def build_agg(self, filters):
        self.agg = self._get_is_direct_facet_aggregation(filters)

    def _get_is_direct_facet_aggregation(self, filters):
        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.IS_DIRECT, filters),
                }
            },
            "aggs": {
                "data": {
                    "terms": {
                        "field": "is_direct",
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
            }
        }

    def _get_is_direct_filter(self, is_direct):

        return {
            "term": {"is_direct": is_direct}
        }



class AggregationUnitPathway(AggregationUnit):

    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self._get_complex_pathway_filter(self.filter)

    def build_agg(self, filters):
        self.agg = self._get_pathway_facet_aggregation(filters)

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
                        'size': 20,
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

    def _get_complex_pathway_filter(self, pathway_codes):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param pathway_codes: list of pathway_codes strings
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if pathway_codes:
            # genes = self.handler._get_genes_for_pathway_code(pathway_codes)
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

class AggregationUnitScoreRange(AggregationUnit):

    def build_query_filter(self):
        if self.filter is not None:
           self.query_filter = self._get_association_score_range_filter(self.params)

    @staticmethod
    def _get_association_score_range_filter(params):
        if len(params.scorevalue_types) ==1:
            return {
                        "range" : {
                            params.association_score_method+"."+params.scorevalue_types[0] : {
                                "gt": params.filters[FilterTypes.SCORE_RANGE][0],
                                "lte": params.filters[FilterTypes.SCORE_RANGE][1]
                            }
                        }
                    }
        else:
            return {
                    "bool": {
                        'must': [{
                                "range" : {
                                    params.association_score_method+"."+st : {
                                        "gt": params.filters[FilterTypes.SCORE_RANGE][0],
                                        "lte": params.filters[FilterTypes.SCORE_RANGE][1]
                                    }
                                }
                              }
                              for st in params.scorevalue_types]
                    }
                }

class AggregationUnitUniprotKW(AggregationUnit):

    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self._get_complex_uniprot_kw_filter(self.filter,
                                                                    BooleanFilterOperator.OR)
    def build_agg(self, filters):
        self.agg = self._get_uniprot_keywords_facet_aggregation(filters)

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

    def _get_complex_uniprot_kw_filter(self, kw, bol):
        pass
        '''
        :param kw: list of uniprot kw strings
        :param bol: boolean operator to use for combining filters
        :return: boolean filter
        '''
        if kw:
            genes = self.handler.get_genes_for_uniprot_kw(kw)
            if genes:
                return self.handler.get_complex_target_filter(genes, bol)
        return dict()

class AggregationUnitECO(AggregationUnit):

    def build_query_filter(self):
        raise NotImplementedError


class AggregationUnitDatasource(AggregationUnit):

    def build_query_filter(self):
        if self.filter is not None:
            requested_datasources = []
            for d in self.filter:
                if d in self.handler.datatypes.datatypes:
                    requested_datasources.extend(self.handler.datatypes.get_datasources(d))
                else:
                    requested_datasources.append(d)
            requested_datasources = list(set(requested_datasources))
            self.query_filter = self._get_complex_datasource_filter(requested_datasources,
                                                                    BooleanFilterOperator.OR)

    def build_agg(self, filters):
        self.agg = self.get_datatype_facet_aggregation(filters)

    def get_datatype_facet_aggregation(self, filters):

        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.DATATYPE, filters),
                }
            },
            "aggs": {
                "data": {
                    "terms": {
                        "field": "private.facets.datatype",
                        'size': 10,
                    },
                    "aggs": {
                        "datasource": {
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

    def _get_complex_datasource_filter(self, datasources, bol):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param evidence_types: list of datasource strings
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

class AggregationBuilder(object):
    '''
    handles the construction of an aggregation query based on a set of filters
    '''

    _UNIT_MAP={
        FilterTypes.DATATYPE : AggregationUnitDatasource,
        # FilterTypes.ECO : AggregationUnitECO,
        FilterTypes.DISEASE : AggregationUnitDisease,
        FilterTypes.TARGET : AggregationUnitTarget,
        FilterTypes.IS_DIRECT : AggregationUnitIsDirect,
        FilterTypes.PATHWAY : AggregationUnitPathway,
        FilterTypes.UNIPROT_KW : AggregationUnitUniprotKW,
        FilterTypes.SCORE_RANGE : AggregationUnitScoreRange,
        FilterTypes.THERAPEUTIC_AREA : AggregationUnitTherapeuticArea
    }

    _SERVICE_FILTER_TYPES = [FilterTypes.IS_DIRECT,
                             FilterTypes.SCORE_RANGE,
                             ]

    def __init__(self, handler):
        self.handler=handler
        self.filter_types=FilterTypes().__dict__
        self.units = {}
        self.aggs = {}
        self.filters = {}


    def load_params(self, params):



        '''define and init units'''
        for unit_type in self._UNIT_MAP:
            self.units[unit_type]= self._UNIT_MAP[unit_type](params.filters[unit_type],
                                                             params,
                                                             self.handler,
                                                             compute_aggs = params.facets)
        '''get filters'''
        for query_filter in self._UNIT_MAP:
            self.filters[query_filter] = self.units[query_filter].query_filter

        '''get aggregations if requested'''
        if params.facets:
            aggs_not_to_be_returned = self._get_aggs_not_to_be_returned(params)
            '''get available aggregations'''
            for agg in self._UNIT_MAP:
                if agg not in aggs_not_to_be_returned:
                    self.units[agg].build_agg(self.filters)
                    if self.units[agg].agg:
                        self.aggs[agg] = self.units[agg].agg


    def _get_AggregationUnit(self,str):
        return getattr(sys.modules[__name__], str)

    def _get_aggs_not_to_be_returned(self,params):
        '''avoid calculate a big facet if only one parameter is passed'''
        filters_to_apply = list(set([k for k,v in params.filters.items() if v is not None]))
        for filter_type in self._SERVICE_FILTER_TYPES:
            if filter_type in filters_to_apply:
                filters_to_apply.pop(filters_to_apply.index(filter_type))
        aggs_not_to_be_returned = []
        if len(filters_to_apply) == 1:#do not return facet if only one filter is applied
            aggs_not_to_be_returned=filters_to_apply[0]
        return aggs_not_to_be_returned



    #
    # def _get_go_facet_aggregation(self, filters):
    #     pass

    #
    #
    # def _get_uniprot_keywords_facet_aggregation_for_genes(self, filters):
    #     return {
    #         "aggs": {
    #             "data": {
    #                 "significant_terms": {
    #                     "field": "uniprot_keywords",
    #                     'size': 25,
    #                 },
    #                 # "aggs": {
    #                 #     "unique_target_count": {
    #                 #        "value_count" : {
    #                 #           "field" : "id",
    #                 #        },
    #                 #     },
    #                 # },
    #             },
    #         }
    #
    #     }
