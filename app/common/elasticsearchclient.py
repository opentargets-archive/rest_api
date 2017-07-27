import hashlib
import json as json
import logging
import sys
import time
import itertools as itt
import addict
from collections import defaultdict

import jmespath
import numpy as np
from elasticsearch import TransportError
from elasticsearch import helpers
from flask import current_app, request
from pythonjsonlogger import jsonlogger
from scipy.stats import hypergeom

from app.common.request_templates import FilterTypes
from app.common.request_templates import SourceDataStructureOptions, AssociationSortOptions
from app.common.response_templates import Association, DataStats, Relation
from app.common.results import PaginatedResult, SimpleResult, RawResult, EmptySimpleResult, \
    EmptyPaginatedResult
from app.common.scoring import Scorer
from app.common.scoring_conf import ScoringMethods
from config import Config
# import pprint

__author__ = 'andreap'

KEYWORD_MAPPING_FIELDS = ["name",
                          "id",
                          "approved_symbol",
                          "symbol_synonyms",
                          "uniprot_accessions",
                          "hgnc_id",
                          "ensembl_gene_id",
                          "efo_url",
                          ]


def ex_level_meet_conditions(x, y, min_level, max_level):
    '''meet conditions for a numerical range with y > x y upper bound and x lower
    bound as max_level and min_level respectively
    '''
    diff = y - x
    return True if \
        min_level <= diff < max_level and \
        x >= min_level and \
        y <= max_level else False


def ex_level_tissues_to_terms_list(key, ts, expression_level):
    '''returns a list with a match dict per el in `ts` using the private facet and
    `epxression_level` based on the `key` as a str "protein" or "rna"
    '''
    return [
        {'match': {
            'private.facets.expression_tissues.' + key + '.' +
            str(expression_level) + '.id': t
        }} for t in ts]


def _copy_and_mutate_dict(d, del_k, **add_ks):
    d = { k: v for k, v in d.items() if k != del_k }
    for k, v in add_ks.items():
        d[k] = v

    return d

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


class SearchObjectTypes():
    TARGET = 'search-object-target'
    DISEASE = 'search-object-disease'


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
                 app_version='',
                 default_ttl=60):
        self.r_server = r_server
        self.app_version = app_version
        self.default_ttl = default_ttl

    def get(self, key):
        value = self.r_server.get(self._get_namespaced_key(key))
        if value:
            return self._decode(value)

    def set(self, key, value, ttl=None):
        return self.r_server.setex(self._get_namespaced_key(key),
                                   self._encode(value),
                                   ttl or self.default_ttl)

    def _get_namespaced_key(self, key):
        # try cityhash for better performance (fast and non cryptographic hash library) from cityhash import CityHash64
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
                 # docname_search_target=None,
                 # docname_search_disease=None,
                 docname_relation=None,
                 cache=None,
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
        self._docname_search_target = docname_search + '-target',
        self._docname_search_disease = docname_search + '-disease'
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
        if 'hits' in res and res['hits']['total']:
            for hit in res['hits']['hits']:
                datapoint = dict(type=hit['_type'],
                                 data=hit['_source'],
                                 id=hit['_id'],
                                 score=hit['_score'],
                                 )
                if params.highlight:
                    highlight = None
                    if 'highlight' in hit:
                        highlight = hit['highlight']
                    datapoint['highlight'] = highlight
                data.append(datapoint)
            return PaginatedResult(res, params, data)
        elif 'suggest' in res:
            suggestions = self._digest_suggest(res)
            return EmptyPaginatedResult(None, suggest=suggestions)
        else:
            return EmptyPaginatedResult(None)

    def get_enrichment_for_targets(self,
                                   targets,
                                   pvalue_threshold = 1e-3,
                                   from_ = 0,
                                   size = 10,
                                   sort='enrichment.score'):

        '''
        N is the population size - all_targets
        K is the number of success states in the population,
        n is the number of draws, - targets_in_set
        k is the number of observed successes, - all_targets_in_disease
        Args:
            query: list of targets

        Returns:

        '''

        params = SearchParams(targets = targets,
                              pvalue=pvalue_threshold,
                              from_ = from_,
                              size = size,
                              sort =sort)

        entry_time = time.time()
        query_cache_key = hashlib.md5(''.join(sorted(list(set(targets))))).hexdigest()
        data = None
        M=len(targets)
        if M <2  :
            data = []
        if data is None:
            data = self.cache.get(query_cache_key)
        if data is None:
            # We get the 3 numbers
            # The total number of targets with associations
            start_time = time.time()
            q = addict.Dict()
            q.query.bool.filter.range['association_counts.total'].gte = 1
            all_targets = self._cached_search(index=self._index_search,
                                              doc_type=self._docname_search_target,
                                              body=q.to_dict(),
                                              size=0)
            N = all_targets["hits"]["total"]
            # print 'all targets query', time.time() - start_time


            '''get all data'''
            start_time = time.time()
            # cache_file='/tmp/'+query_cache_key
            # if os.path.exists('/tmp/'+query_cache_key):
            #     disease_data = pickle.load(open(cache_file))
            # else:
            disease_data = {}
            all_data = helpers.scan(client=self.handler,
                                      query={
                                          "query": self.get_complex_target_filter(targets),
                                          'size': 1000,
                                          "_source": ["target.*",
                                                      "harmonic-sum.datatypes",
                                                      "harmonic-sum.overall",
                                                      "disease.id",
                                                      "disease.efo_info.label",
                                                      "disease.efo_info.therapeutic_area",
                                                      ]
                                      },
                                      scroll='1h',
                                      index=self._index_association,
                                      # doc_type="search-object-disease",
                                      timeout='10m'
                                      )
            for a in all_data:
                disease_id = jmespath.search('_source.disease.id',a)
                if disease_id not in disease_data:
                    disease_data[disease_id] = []
                disease_data[disease_id].append(a)
            # pickle.dump(disease_data, open(cache_file, 'w'), protocol=pickle.HIGHEST_PROTOCOL)
            # print 'get all data', time.time() - start_time

            start_time = time.time()
            background = self.handler.mget(body = dict(ids=disease_data.keys()),
                                           index = self._index_search,
                                           doc_type = self._docname_search_disease,
                                           _source = ['association_counts', 'name'],
                                           realtime=False,
                                          )

            background_counts = dict()
            for doc in background['docs']:
                if doc['found']:
                    background_counts[doc['_id']] = {
                        "id": doc['_id'],
                        "label": doc["_source"]["name"],
                        "association_counts": doc["_source"]["association_counts"]
                    }
                else:
                    raise KeyError('document with id %s not found' % (doc['_id']))

            # print 'background query', time.time() - start_time



            start_time = time.time()
            score_cache = {}
            data = []
            for disease_id, disease_targets in disease_data.items():
                bg = background_counts[disease_id]
                k = bg["association_counts"]["total"]
                x = len(disease_targets)

                key = '_'.join(map(str,[N,M,k,x]))
                pvalue = score_cache.get(key)
                if pvalue is None:
                    # pvalue = HypergeometricTest.run(N, M, k, x)
                    pvalue = hypergeom.pmf(x, N, k, M)
                    # print key, hypergeom.pmf(x,N, k, M), HypergeometricTest.run(N, M, k, x)
                    score_cache[key] =pvalue

                disease_properties = disease_targets[0]['_source']['disease']['efo_info']
                target_data = []
                for d in disease_targets:
                    source = d['_source']
                    source['association_score'] = source.pop('harmonic-sum')
                    del source['disease']
                    target_data.append(source)
                target_data = sorted(target_data, key=lambda k: k['association_score']['overall'], reverse=True)
                for t in target_data:
                    t['association_score']['overall'] = Association.cap_score(t['association_score']['overall'])

                data.append({
                    "enriched_entity": {
                        "type": "disease",
                        "id": disease_id,
                        "label": bg["label"],
                        "properties": disease_properties
                    },
                    "enrichment":{
                        "method": "hypergeometric",
                        "params": {
                            "all_targets": N,
                            "all_targets_in_disease": k,
                            "targets_in_set": M,
                            "targets_in_set_in_disease": x
                        },
                        "score": pvalue
                    },
                    "targets": target_data
                })
            self.cache.set(query_cache_key, data, ttl = current_app.config['APP_CACHE_EXPIRY_TIMEOUT'])
            # print 'enrichment calculation', time.time() - start_time
        if pvalue_threshold < 1:
            data = [d for d in data if d['enrichment']['score'] <= pvalue_threshold]
        data = sorted(data, key=lambda k: jmespath.search(params.sort, k))
        total_time = time.time() - entry_time
        # print 'total time: %f | Targets = %i | Time per target %f'%(total_time, len(targets), total_time/len(targets))
        return PaginatedResult(None,
                               data=data[from_:from_ + size],
                               total = len(data),
                               took = int(total_time*1000),
                               params=params,

                               )

    def best_hit_search(self,
                        searchphrases,
                        doc_filter=(FreeTextFilterOptions.ALL),
                        **kwargs):
        '''
        similar to free_text_serach but can take multiple queries

        :param searchphrase:
        :param doc_filter:
        :param kwargs:
        :return:
        '''

        params = SearchParams(**kwargs)

        if doc_filter is None:
            doc_filter = [FreeTextFilterOptions.ALL]
        doc_filter = self._get_search_doc_types(doc_filter)
        results = self._best_hit_query(searchphrases, doc_filter, params)
        # current_app.logger.debug("Got %d Hits in %ims" % (res['hits']['total'], res['took']))
        data = []

        # there are len(params.q) responses - one per query
        for i, res in enumerate(results['responses']):
            searchphrase = searchphrases[
                i]  # even though we are guaranteed that responses come back in order, and can match query to the result - this might be convenient to have
            lower_name = searchphrase.lower()
            exact_match = False
            if 'hits' in res and res['hits']['total']:
                hit = res['hits']['hits'][0]
                highlight = hit.get('highlight', None)
                type_ = hit['_type']
                if highlight:
                    for field_name, matched_strings in highlight.items():
                        if field_name in KEYWORD_MAPPING_FIELDS:
                            for string in matched_strings:
                                if string.lower() == '<em>%s</em>' % lower_name:
                                    exact_match = True
                                    break

                datapoint = dict(type=type_,
                                 data=hit['_source'],
                                 id=hit['_id'],
                                 score=hit['_score'],
                                 q=searchphrase,
                                 exact=exact_match)
                if params.highlight:
                    datapoint['highlight'] = highlight
            else:
                datapoint = dict(id=None,
                                 q=searchphrase)
            data.append(datapoint)

        return SimpleResult(results, params, data)

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
        else:
            suggestions = []
            if 'suggest' in res:
                suggestions = self._digest_suggest(res)

            return EmptySimpleResult(None, data = {}, suggest=suggestions)


        return SimpleResult(None, params, data)

    def _digest_suggest(self, res):
        suggestions = []
        for suggest_field in res['suggest'].values():
            for i in suggest_field:
                for option in i['options']:
                    if option not in suggestions:
                        suggestions.append(option['text'])
        return suggestions

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

    def get_gene_info(self, gene_ids, **kwargs):
        params = SearchParams(**kwargs)

        if params.datastructure == SourceDataStructureOptions.DEFAULT:
            params.datastructure = SourceDataStructureOptions.FULL
        source_filter = SourceDataStructureOptions.getSource(params.datastructure)
        if params.fields:
            source_filter["includes"] = params.fields

        if gene_ids:
            q = addict.Dict()
            q.query.bool.filter.ids['values'] = gene_ids
            q._source = source_filter
            q.size = len(gene_ids)
            q['from'] = params.start_from

            res = self._cached_search(index=self._index_genename,
                                      doc_type=self._docname_genename,
                                      body=q.to_dict())

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
                                  body={"query": {
                                      "ids": {"values": evidenceid},
                                  },
                                      "size": len(evidenceid),
                                  }
                                  )
        return SimpleResult(res,
                            params,
                            data = [hit['_source'] for hit in res['hits']['hits']])

    def get_label_for_eco_code(self, code):
        res = self._cached_search(index=self._index_eco,
                                  doc_type=self._docname_eco,
                                  body={'query': {
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
            conditions.append(self.get_complex_disease_filter(diseases, object_operator,
                                                              is_direct=False))  # temporary until params.is_direct is supported again
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
            source_filter["includes"] = params.fields

        q = addict.Dict()
        q.query.bool.filter.bool.must = conditions
        q.size = params.size
        q['from'] = params.start_from
        q.sort = self._digest_sort_strings(params)
        q._source = source_filter

        res = self._cached_search(index=self._index_data,
                                  # doc_type=self._docname_data,
                                  body=q.to_dict(),
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

        #TODO:use get or mget methods here
        res = self._cached_search(index=self._index_association,
                                  body={"query": {
                                            "ids": {"values": associationid},
                                            },
                                        "size": len(associationid),
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
        query_body = {"match_all": {}}
        if params.search:
            query_body = {
                "match_phrase_prefix": {
                    "private.facets.free_text_search": params.search
                }
            }
            #     "bool": {
            #         "should": [
            #             {"multi_match": {
            #                 "query": params.search,
            #                 "fields": ["target.*",
            #                            "disease.*",
            #                            # "private.*",
            #                            ],
            #                 "type": "phrase_prefix",
            #                 "lenient": True,
            #                 "analyzer": 'whitespace',
            #
            #             }
            #             },
            #             {"multi_match": {
            #                 "query": params.search,
            #                 "fields": ["target.*",
            #                            "disease.*",
            #                            # "private.*",
            #                            ],
            #                 "analyzer": 'keyword',
            #                 "type": "best_fields",
            #                 "lenient": True,
            #             }
            #             },
            #         ],
            #     }
            # }

        if params.datastructure in [SourceDataStructureOptions.FULL, SourceDataStructureOptions.DEFAULT]:
            params.datastructure = SourceDataStructureOptions.SCORE
        source = SourceDataStructureOptions.getSource(params.datastructure, params)
        if 'includes' in source:
            params.requested_fields = source['includes']
        ass_query_body = {
            # restrict the set of datapoints using the target and disease ids
            "query": query_body,
            'size': params.size,
            '_source': source,
            'from': params.start_from,
            "sort": self._digest_sort_strings(params)
        }

        if params.search_after is not None:
            if params.search_after:
                ass_query_body['search_after'] = params.search_after

            ass_query_body['sort'].append({"id.keyword": "desc"})
            ass_query_body['from'] = -1



        # calculate aggregation using proper ad hoc filters
        if aggs:
            ass_query_body['aggs'] = aggs
        # filter out the results as requested, this will not be applied to the aggregation
        if filter_data_conditions:
            ass_query_body['post_filter'] = {
                "bool": {
                    "must": [i for i in filter_data_conditions.values() if i]
                }
            }

        # pprint.pprint(ass_query_body)

        ass_data = self._cached_search(index=self._index_association,
                                       body=ass_query_body,
                                       timeout="20m",
                                       request_timeout=60 * 20,
                                       # routing=use gene here
                                       request_cache=True,
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

        # TODO: use elasticsearch histogram to get this in the whole dataset ignoring filters??"
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
                                              body={"query": {
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
                                       therapeutic_areas=ta_scores,
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
        targets = self._resolve_negable_parameter_set(targets, include_negative)
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
        diseases = self._resolve_negable_parameter_set(diseases, include_negative)
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

    def _get_exact_mapping_query(self, searchphrase):
        mm1 = addict.Dict()
        mm1.multi_match.query = searchphrase
        mm1.multi_match.fields = ["name^3",
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
                                  "efo_synonyms^0.5",
                                  "ortholog.*.symbol^0.5",
                                  "ortholog.*.id",
                                ]
        mm1.multi_match.analyzer = 'keyword'
        mm1.multi_match.tie_breaker = 0
        mm1.multi_match.type = 'best_fields'

        q = addict.Dict()
        q.bool.should = [mm1]

        return q.to_dict()

    def _get_free_text_query(self, searchphrase):
        mm_f1 = ["name^3", "description^2", "efo_synonyms",
                 "symbol_synonyms", "approved_symbol", "approved_name",
                 "name_synonyms", "gene_family_description",
                 "efo_path_labels^0.1", "ortholog.*.symbol^0.2",
                 "ortholog.*.name^0.2", "drugs.*^0.5", "phenotypes.*^0.3"]

        mm1 = addict.Dict()
        mm1.multi_match.query = searchphrase
        mm1.multi_match.fields = mm_f1
        mm1.multi_match.analyzer = 'standard'
        mm1.multi_match.tie_breaker = '0'
        mm1.multi_match.type = 'phrase_prefix'

        mm_f2 = ["name^3", "description", "id", "approved_symbol",
                 "symbol_synonyms", "name_synonyms", "uniprot_accessions",
                 "hgnc_id", "ensembl_gene_id", "efo_path_codes", "efo_url",
                 "efo_synonyms^2", "ortholog.*.symbol^0.2", "ortholog.*.id^0.2",
                 "drugs.*^0.5", "phenotypes.*^0.3"]

        mm2 = addict.Dict()
        mm2.multi_match.query = searchphrase
        mm2.multi_match.fields = mm_f2
        mm2.multi_match.analyzer = 'keyword'
        mm2.multi_match.tie_breaker = 0
        mm2.multi_match.type = 'best_fields'

        q = addict.Dict()
        q.function_score.score_mode = 'multiply'
        q.function_score.query.bool.should = [mm1, mm2]
        q.function_score.query.bool.filter = {
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

        f1 = addict.Dict()
        f1.field_value_factor.field = 'association_counts.total'
        f1.field_value_factor.factor = 0.05
        f1.field_value_factor.modifier = 'sqrt'
        f1.field_value_factor.missing = 1
        # f1.field_value_factor.weight = 0.01

        q.function_score.functions = [f1]

                # "path_score": {
                #   "script": "def score=doc['min_path_len'].value; if (score ==0) {score = 1}; 1/score;",
                #   "lang": "groovy",
                # },
                # "script_score": {
                #   "script": "def score=doc['total_associations'].value; if (score ==0) {score = 1}; score/10;",
                #   "lang": "groovy",
                # }
                # {
                # "field_value_factor":{
                #     "field": "min_path_len",
                #     "factor": 0.5,
                #     "modifier": "reciprocal",
                #     "missing": 1,
                #     # "weight": 0.5,
                #     }
                # }
            # "filter": {
            #     "exists": {
            #       "field": "min_path_len"
            #     }
            #   }

        return q.to_dict()

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
            "ortholog.*.id":{},
            "drugs.*":{},
            "phenotypes.*":{},
        }
        }

    def _get_mapping_highlights(self):
        highlight = {"fields": {}}
        for key in KEYWORD_MAPPING_FIELDS:
            highlight['fields'][key] = {}

        return highlight

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
                source_filter["includes"] = params.fields

            q = addict.Dict()
            q.query.ids['values'] = genes
#             q.query.constant_score.filter.bool.should.terms.gene = genes
#             q.size = params.size
#             q._source = OutputDataStructureOptions.getSource(OutputDataStructureOptions.COUNT)

            res = self._cached_search(index=self._index_expression,
                                      body=q.to_dict()
                                      )
            data = dict([(hit['_id'], hit['_source']) for hit in res['hits']['hits']])
            return SimpleResult(res, params, data)

    def _get_efo_with_data(self, conditions):
        efo_with_data = []
        q = addict.Dict()
        q.query.bool.filter.bool.must = conditions
        q.size = 10000
        q._source = ['disease.id']
        q.aggs.efo_codes.terms.field = 'disease.id'
        q.aggs.efo_codes.terms.size = 10000

        res = self._cached_search(index=self._index_data,
                                  body=q.to_dict())
        if res['hits']['total']:
            data = res['aggregations']["efo_codes"]["buckets"]
            efo_with_data = list(set([i['key'] for i in data]))
        return efo_with_data

    def _get_genes_for_pathway_code(self, pathway_codes):
        data = []
        q = addict.Dict()
        q.query.bool.filter.bool.should = [
            {"terms": {
                "private.facets.reactome.pathway_code": pathway_codes}},
            {"terms": {
                "private.facets.reactome.pathway_type_code": pathway_codes}},
        ]
        q.size = 10000
        q._source = ['id']

        res = self._cached_search(index=self._index_genename,
                                  body=q.to_dict())
        if res['hits']['total']:
            data = [hit['_id'] for hit in res['hits']['hits']]
        return data

    def _process_facets(self, facets):

        reactome_ids = []
        therapeutic_areas = []

        # TODO: implement disease name injection

        '''get data'''
        for facet in facets:
            if 'buckets' in facets[facet]:
                facet_buckets = facets[facet]['buckets']
                for bucket in facet_buckets:
                    if 'label' in bucket:
                        bucket['label'] = bucket['label']['buckets'][0]['key']
                    if facet == FilterTypes.PATHWAY:
                        reactome_ids.append(bucket['key'])
                        if 'pathway' in bucket:
                            if 'buckets' in bucket['pathway']:
                                sub_facet_buckets = bucket['pathway']['buckets']
                                for sub_bucket in sub_facet_buckets:
                                    reactome_ids.append(sub_bucket['key'])
                    elif facet == FilterTypes.THERAPEUTIC_AREA:
                        therapeutic_areas.append(bucket['key'].upper())
                    elif facet == FilterTypes.TARGET_CLASS:
                        if FilterTypes.TARGET_CLASS in bucket:
                            if 'buckets' in bucket[FilterTypes.TARGET_CLASS]:
                                sub_facet_buckets = bucket[FilterTypes.TARGET_CLASS]['buckets']
                                for sub_bucket in sub_facet_buckets:
                                    if 'label' in sub_bucket:
                                        sub_bucket['label'] = sub_bucket['label']['buckets'][0]['key']

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
                                          '_source': {"includes": ['label']},
                                          'size': 10000,
                                          'from': 0,
                                          }
                                      )
            if res['hits']['total']:
                for hit in res['hits']['hits']:
                    labels[hit['_id']] = hit['_source']['label']
        return labels

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
        q = addict.Dict()
        q.query.bool.filter.bool.should = [
            {"terms": {"private.facets.uniprot_keywords": kw}}
        ]
        q.size = 10000
        q._source = ['id']
        res = self._cached_search(index=self._index_genename,
                                  body=q.to_dict())
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

    def _get_search_doc_types(self, filter_):
        doc_types = []
        for t in filter_:
            t = t.lower()
            if t == FreeTextFilterOptions.ALL:
                return []
            elif t in FreeTextFilterOptions.__dict__.values():
                doc_types.append(self._docname_search + '-' + t)
        return doc_types

    def _free_text_query(self, searchphrase, doc_types, params):
        '''
           If  'fields' parameter is passed, only these fields would be returned
           and 'highlights' would be added only if it is of the fields parameters.
           If there is not a 'fields' parameter, then fields are included by default

        '''

        highlight = self._get_free_text_highlight()
        source_filter = SourceDataStructureOptions.getSource(params.datastructure)
        if params.fields:
            source_filter["includes"] = params.fields

        body = {'query': self._get_free_text_query(searchphrase),
                'size': params.size,
                'from': params.start_from,
                '_source': source_filter,
                "explain": current_app.config['DEBUG'],
                "suggest": self._get_free_text_suggestions(searchphrase)
                }
        if highlight is not None:
            body['highlight'] = highlight

        try:
            res = self._cached_search(index=self._index_search,
                                   doc_type=doc_types,
                                   body=body,
                                   )
        except TransportError as e :#TODO: remove this try. needed to go around rare elastiscsearch error due to fields with different mappings
            if e.error == u'search_phase_execution_exception':
                return {}
            raise
        return res

    def _best_hit_query(self, searchphrases, doc_types, params):
        '''
           If  'fields' parameter is passed, only these fields would be returned
           and 'highlights' would be added only if it is of the fields parameters.
           If there is not a 'fields' parameter, then fields are included by default

        '''
        head = {'index': self._index_search, 'type': doc_types}
        multi_body = []
        highlight = self._get_mapping_highlights()

        source_filter = SourceDataStructureOptions.getSource(params.datastructure)
        if params.fields:
            source_filter["includes"] = params.fields

        for searchphrase in searchphrases:
            # body = {'query': self._get_exact_mapping_query(searchphrase.lower()), #this is 3 times faster if needed
            body = {'query': self._get_free_text_query(searchphrase.lower()),
                    'size': 1,
                    'from': params.start_from,
                    '_source': source_filter,
                    "explain": current_app.config['DEBUG'],
                    'highlight': highlight,
                    }

            multi_body.append(head)
            multi_body.append(body)

        return self._cached_search(body=multi_body,
                                   is_multi=True)

    def _get_search_doc_name(self, doc_type):
        return self._docname_search + '-' + doc_type

    def get_stats(self):

        stats = DataStats()
        stats.add_evidencestring(self._cached_search(index=self._index_data,
                                                     # doc_type=self._docname_data,
                                                     body={"query": {"match_all": {}},
                                                           "aggs": {
                                                               "data": {
                                                                   "terms": {
                                                                       "field": "type.keyword",
                                                                       'size': 10,
                                                                   },
                                                                   "aggs": {
                                                                       "datasources": {
                                                                           "terms": {
                                                                               "field": "sourceID.keyword",
                                                                           },
                                                                       }
                                                                   }
                                                               }
                                                           },
                                                           'size': 1,
                                                           '_source': False,
                                                           },
                                                     timeout="10m",
                                                     )
                                 )

        stats.add_associations(self._cached_search(index=self._index_association,
                                                   # doc_type=self._docname_data,
                                                   body={"query": {"match_all": {}},
                                                         "aggs": {
                                                             "data": {
                                                                 "terms": {
                                                                     "field": "private.facets.datatype.keyword",
                                                                     'size': 10,
                                                                 },
                                                                 "aggs": {
                                                                     "datasources": {
                                                                         "terms": {
                                                                             "field": "private.facets.datasource.keyword",
                                                                         },
                                                                     }
                                                                 }
                                                             }
                                                         },
                                                         'size': 1,
                                                         '_source': False,
                                                         },
                                                   timeout="10m",
                                                   ),
                               self.datatypes
                               )

        target_count = self._cached_search(index=self._index_search,
                                           doc_type=self._docname_search_target,
                                           body={"query": {
                                               "range": {
                                                   "association_counts.total": {
                                                       "gt": 0,
                                                   }
                                               }
                                           },
                                               'size': 1,
                                               '_source': False,
                                           })
        stats.add_key_value('targets', target_count['hits']['total'])

        disease_count = self._cached_search(index=self._index_search,
                                            doc_type=self._docname_search_disease,
                                            body={"query": {
                                                "range": {
                                                    "association_counts.total": {
                                                        "gt": 0,
                                                    }
                                                }
                                            },
                                                'size': 1,
                                                '_source': False,
                                            })
        stats.add_key_value('diseases', disease_count['hits']['total'])

        return RawResult(str(stats))

    def _digest_sort_strings(self, params):
        digested = []
        for s in params.sort:
            order = 'desc'
            mode = 'min'
            if s.startswith('~'):
                order = 'asc'
                s=s[1:]
                mode = 'min'
            if s.startswith('association_score'):
                s= s.replace('association_score', params.association_score_method)
            digested.append({s : {"order": order,
                                  "mode": mode}})
        return digested

    def _get_evidence_score_range_filter(self, params):
        return {
                "range" : {
                    'scores.association_score' : {
                        "gte": params.filters[FilterTypes.SCORE_RANGE][0],
                        "lte": params.filters[FilterTypes.SCORE_RANGE][1]
                        }
                    }
                }

    def _cached_search(self, *args, **kwargs):
        key = str(args) + str(kwargs)
        no_cache = Config.NO_CACHE_PARAMS in request.values
        is_multi = False

        if ('is_multi' in kwargs):
            is_multi = kwargs.pop('is_multi')

        if no_cache:
            if is_multi:
                res = self.handler.msearch(*args, **kwargs)
            else:
                res = self.handler.search(*args, **kwargs)
            return res

        res = self.cache.get(key)
        if res is None:
            start_time = time.time()

            if is_multi:
                res = self.handler.msearch(*args, **kwargs)
            else:
                res = self.handler.search(*args, **kwargs)

            took = int(round(time.time() - start_time))
            self.cache.set(key, res, took * 60)
        return res

    def _resolve_negable_parameter_set(self, params, include_negative=False):
        filtered_params = []
        for p in params:  # handle negative sets
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
                r.value = d['scores']['overlap']
                data.append(r.to_dict())

        return PaginatedResult(res,
                               params,
                               data,
                               )



    def _get_free_text_suggestions(self, searchphrase):
        return {
            "text": searchphrase,
            # "label": {
            #     "term": {
            #         "field": "approved_symbol"
            #     }
            # },
            "name": {
                "term": {
                    "field": "name"
                }
            },
        }


class SearchParams():
    _max_search_result_limit = 10000
    _default_return_size = 10
    _allowed_groupby = ['gene', 'evidence-type', 'efo']
    _default_pvalue = 1e-3

    def __init__(self, **kwargs):

        self.sortmethod = None
        self.size = kwargs.get('size', self._default_return_size)
        if self.size is None:
            self.size = self._default_return_size
        if (self.size > self._max_search_result_limit):
            raise AttributeError('Size cannot be bigger than %i' % self._max_search_result_limit)

        self.start_from = kwargs.get('from', 0) or kwargs.get('from_', 0) or 0
        self.search_after = kwargs.get('search_after', None)
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

        self.sort = kwargs.get('sort', [ScoringMethods.DEFAULT + '.' + AssociationSortOptions.OVERALL]) or [
            ScoringMethods.DEFAULT + '.' + AssociationSortOptions.OVERALL]
        self.search = kwargs.get('search')
        if self.search:
            self.search = self.search.lower().strip()

        self.gte = kwargs.get('gte')

        self.lt = kwargs.get('lt')

        self.format = kwargs.get('format', 'json') or 'json'

        self.datastructure = kwargs.get('datastructure',
                                        SourceDataStructureOptions.DEFAULT) or SourceDataStructureOptions.DEFAULT

        self.enrichment_method = kwargs.get('targets_enrichment')

        self.fields = kwargs.get('fields')
        self.requested_fields = None  # to be populated after

        if self.fields:
            self.datastructure = SourceDataStructureOptions.CUSTOM

        self.filters = dict()
        self.filters[FilterTypes.TARGET] = kwargs.get(FilterTypes.TARGET)
        self.filters[FilterTypes.DISEASE] = kwargs.get(FilterTypes.DISEASE)
        self.filters[FilterTypes.THERAPEUTIC_AREA] = kwargs.get(FilterTypes.THERAPEUTIC_AREA)
        self.filters[FilterTypes.RNA_EXPRESSION_LEVEL] = \
            kwargs.get(FilterTypes.RNA_EXPRESSION_LEVEL, 0)
        self.filters[FilterTypes.RNA_EXPRESSION_TISSUE] = \
            kwargs.get(FilterTypes.RNA_EXPRESSION_TISSUE, [])
        self.filters[FilterTypes.PROTEIN_EXPRESSION_LEVEL] = \
            kwargs.get(FilterTypes.PROTEIN_EXPRESSION_LEVEL, 0)
        self.filters[FilterTypes.PROTEIN_EXPRESSION_TISSUE] = \
            kwargs.get(FilterTypes.PROTEIN_EXPRESSION_TISSUE, [])
        score_range = [0., self._max_score]
        score_min = kwargs.get(FilterTypes.ASSOCIATION_SCORE_MIN, 0.)
        if score_min is not None:
            score_range[0] = score_min
        score_max = kwargs.get(FilterTypes.ASSOCIATION_SCORE_MAX, self._max_score)
        if score_max == 1:  # temporary fix until max score cap can be done in elasticsearch
            score_max = self._max_score
        if score_max is not None:
            score_range[1] = score_max
        self.filters[FilterTypes.SCORE_RANGE] = score_range
        self.scorevalue_types = kwargs.get('scorevalue_types', [AssociationSortOptions.OVERALL]) or [
            AssociationSortOptions.OVERALL]
        self.filters[FilterTypes.PATHWAY] = kwargs.get(FilterTypes.PATHWAY)
        self.filters[FilterTypes.UNIPROT_KW] = kwargs.get(FilterTypes.UNIPROT_KW)
        self.filters[FilterTypes.IS_DIRECT] = kwargs.get(FilterTypes.IS_DIRECT)
        self.filters[FilterTypes.ECO] = kwargs.get(FilterTypes.ECO)
        self.filters[FilterTypes.GO] = kwargs.get(FilterTypes.GO)
        self.filters[FilterTypes.TARGET_CLASS] = kwargs.get(FilterTypes.TARGET_CLASS)

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

        # required for evidence query. TODO: harmonise it with the filters in association endpoint
        self.pathway = kwargs.get('pathway', []) or []
        self.target_class = kwargs.get('target_class', []) or []
        self.uniprot_kw = kwargs.get('uniprotkw', []) or []
        self.datatype = kwargs.get('datatype', []) or []
        self.is_direct = kwargs.get('direct', False)
        self.target = kwargs.get('target', []) or []
        self.disease = kwargs.get('disease', []) or []
        self.eco = kwargs.get('eco', []) or []

        setattr(self, FilterTypes.RNA_EXPRESSION_LEVEL,
                kwargs.get(FilterTypes.RNA_EXPRESSION_LEVEL, 0))

        setattr(self, FilterTypes.RNA_EXPRESSION_TISSUE,
                kwargs.get(FilterTypes.RNA_EXPRESSION_TISSUE, []))

        setattr(self, FilterTypes.PROTEIN_EXPRESSION_LEVEL,
                kwargs.get(FilterTypes.PROTEIN_EXPRESSION_LEVEL, 0))

        setattr(self, FilterTypes.PROTEIN_EXPRESSION_TISSUE,
                kwargs.get(FilterTypes.PROTEIN_EXPRESSION_TISSUE, []))

        self.facets = kwargs.get('facets', "false") or "false"
        self.facets_size = kwargs.get('facets_size', None) or None

        self.association_score_method = kwargs.get('association_score_method', ScoringMethods.DEFAULT)

        highlight_default = True
        self.highlight = kwargs.get('highlight', highlight_default)
        if self.highlight is None:
            self.highlight = highlight_default
        self.pvalue =  kwargs.get('pvalue', self._default_pvalue)
        self.query_params =  {k:v for k,v in self.__dict__.items() if k in kwargs}
        if 'from_' in kwargs:
            self.query_params['from']=self.start_from


class AggregationUnit(object):
    '''
    base unit to build an aggregation query
    to be subclassed by implementations
    '''

    def __init__(self,
                 filter,
                 params,
                 handler,
                 compute_aggs=False):
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
            if filter_type != key and filter_value:
                conditions.append(filter_value)
        return conditions

    def build_query_filter(self):
        raise NotImplementedError

    def build_agg(self, filters):
        pass
        # raise NotImplementedError

    def get_default_size(self):
        raise NotImplementedError

    def get_size(self):
        default_size = self.get_default_size()
        facet_size = self.params.facets_size
        return facet_size or default_size



class AggregationUnitTarget(AggregationUnit):
    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self.handler.get_complex_target_filter(self.filter)

    def build_agg(self, filters):
        self.agg = self._get_target_facet_aggregation(filters)

    def get_default_size(self):
        return 25

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
                        'size': self.get_size(),
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

    def get_default_size(self):
        return 25

    def _get_disease_facet_aggregation(self, filters):
        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.DISEASE, filters),
                }
            },
            "aggs": self.get_disease_aggregation(),
        }

    def get_disease_aggregation(self):
        return {
                "data": {
                    "terms": {
                        "field": "disease.id",
                        'size': self.get_size(),
                    },
                    "aggs": {
                        "unique_disease_count": {
                            "cardinality": {
                                "field": "disease.id",
                                "precision_threshold": 1000},
                        },
                        "sum_scores": {
                            "sum": {
                                "field": "harmonic_sum.association_score.overall",
                            },
                        },
                    }
                }
            }


class AggregationUnitTherapeuticArea(AggregationUnit):
    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self._get_complex_therapeutic_area_filter(self.filter)

    def build_agg(self, filters):
        self.agg = self._get_disease_facet_aggregation(filters)

    def get_default_size(self):
        return 25

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
                        "field": "disease.efo_info.therapeutic_area.codes.keyword",
                        'size': self.get_size(),
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
        return {"terms": {"disease.efo_info.therapeutic_area.codes.keyword": filter}}


class AggregationUnitIsDirect(AggregationUnit):
    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self._get_is_direct_filter(self.filter)

    def build_agg(self, filters):
        self.agg = self._get_is_direct_facet_aggregation(filters)

    def get_default_size(self):
        return 10

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
                        'size': self.get_size(),
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


class AggregationUnitUniprotKW(AggregationUnit):
    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self._get_uniprot_filter(self.filter)

    def build_agg(self, filters):
        self.agg = self._get_uniprot_facet_aggregation(filters)

    def get_default_size(self):
        return 50

    def _get_uniprot_facet_aggregation(self, filters):
        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.IS_DIRECT, filters),
                }
            },
            "aggs": {
                "data": {
                    "significant_terms": {
                        "field": "private.facets.uniprot_keywords",
                        'size': self.get_size(),
                        "chi_square": {"include_negatives": True,
                                       "background_is_superset": False},
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

    def _get_uniprot_filter(self, kw):
        return {
            "terms": {"private.facets.uniprot_keywords": kw}
        }


class AggregationUnitGO(AggregationUnit):
    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self._get_go_filter(self.filter)

    def build_agg(self, filters):
        self.agg = self._get_go_facet_aggregation(filters)

    def get_default_size(self):
        return 50

    def _get_go_facet_aggregation(self, filters):
        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.GO, filters),
                }
            },
            "aggs": {
                "data": {
                    "significant_terms": {
                        "field": "private.facets.go.*.code",
                        'size': self.get_size(),

                    },
                    "aggs": {
                        "label": {
                            "terms": {
                                "field": "private.facets.go.*.term",
                                'size': 1,
                            },
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

    def _get_go_filter(self, kw):
        return {
            "terms": {"private.facets.go.*.code": kw}
        }


class AggregationUnitPathway(AggregationUnit):
    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self._get_complex_pathway_filter(self.filter)

    def build_agg(self, filters):
        self.agg = self._get_pathway_facet_aggregation(filters)

    # TODO: Only the pathway_type_code is affected by the default size, the pathway_code is not (see below)
    def get_default_size(self):
        return 20

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
                        'size': self.get_size(),
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


class AggregationUnitTargetClass(AggregationUnit):

    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self._get_target_class_filter(self.filter)

    def build_agg(self, filters):
        self.agg = self._get_target_class_aggregation(filters)

    # TODO: Only the target_class.level1.id is affected by the default size, there are others not affected (see below)
    def get_default_size(self):
        return 25

    def _get_target_class_aggregation(self, filters={}):
        return {
            "filter": {
                "bool": {
                    "must": self._get_complimentary_facet_filters(FilterTypes.TARGET_CLASS, filters),
                }
            },
            "aggs": {
                "data": {
                    "terms": {
                        "field": "private.facets.target_class.level1.id",
                        'size': self.get_size(),
                    },

                    "aggs": {
                        "label": {
                            "terms": {
                                "field": "private.facets.target_class.level1.label",
                                'size': 1,
                            },
                        },
                        FilterTypes.TARGET_CLASS: {
                            "terms": {
                                "field": "private.facets.target_class.level2.id",
                                'size': 50,
                            },
                            "aggs": {
                                "label": {
                                    "terms": {
                                        "field": "private.facets.target_class.level2.label",
                                        'size': 1,
                                    },
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

    def _get_target_class_filter(self, target_class_ids):
        '''
        http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/combining-filters.html
        :param target_class_ids: list of target class ids strings
        :return: boolean filter
        '''
        if target_class_ids:
            return {"bool": {
                "should": [
                    {"terms": {"private.facets.target_class.level1.id": target_class_ids}},
                    {"terms": {"private.facets.target_class.level2.id": target_class_ids}},
                ]
                }
            }

        return dict()


class AggregationUnitRNAExLevel(AggregationUnit):
    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = \
                self._get_association_rna_range_filter(self.params)

    def get_default_size(self):
        return 300

    def build_agg(self, filters):
        d = addict.Dict()
        d.constant_score.filter.bool.must = \
            ex_level_tissues_to_terms_list('rna',
                                           self.params.rna_expression_tissue, 1)
        mut_filters = _copy_and_mutate_dict(filters,
                                             del_k='rna_expression_tissue',
                                             rna_expression_tissue=d.to_dict())
        self.agg = self._get_aggregation_on_rna_expression_level(
            mut_filters, self._get_complimentary_facet_filters,
            self.get_size(), self.params.rna_expression_level)


    @staticmethod
    def _get_association_rna_range_filter(params):
        range_ok = ex_level_meet_conditions(
            params.rna_expression_level, 11, 1, 11)

        q = {}
        if range_ok:
            # here the functionality
            q = {
                'constant_score': {
                    'filter': {
                        'bool': {
                            'must': [{
                                'exists': {
                                    'field':
                                    'private.facets.expression_tissues.rna.' +
                                    str(params.rna_expression_level)
                                }
                            }]
                        }
                    }
                }
            }

        return q

    @staticmethod
    def _get_aggregation_on_rna_expression_level(filters, filters_func, size,
                                                 ex_level):
        f_agg = {}
        if ex_level > 0:
            f_agg = {
                "filter": {
                    "bool": {
                        "must": filters_func(FilterTypes.RNA_EXPRESSION_LEVEL,
                                             filters)
                    }
                },
                "aggs": {
                    "data": {
                        "terms": {
                            "field":
                            "private.facets.expression_tissues.rna." +
                            str(1) + ".level",
                            "order": {
                                "unique_target_count": "desc"
                            },
                            'size': size
                        },
                        "aggs": {
                            "unique_target_count": {
                                "cardinality": {
                                    "field": "target.id",
                                    "precision_threshold": 1000
                                },
                            },
                            "unique_disease_count": {
                                "cardinality": {
                                    "field": "disease.id",
                                    "precision_threshold": 1000
                                },
                            }
                        }
                    }
                }
            }
        else:
            f_agg = {
                "filter": {},
                "aggs": {
                    "data": {
                        "terms": {
                            "field":
                            "private.facets.expression_tissues.rna." +
                            str(1) + ".level",
                            "order": {
                                "unique_target_count": "desc"
                            },
                            'size': size
                        },
                        "aggs": {
                            "unique_target_count": {
                                "cardinality": {
                                    "field": "target.id",
                                    "precision_threshold": 1000
                                },
                            },
                            "unique_disease_count": {
                                "cardinality": {
                                    "field": "disease.id",
                                    "precision_threshold": 1000
                                },
                            }
                        }
                    }
                }
            }

        return f_agg


class AggregationUnitRNAExTissue(AggregationUnit):
    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = \
                self._get_association_rna_range_filter(self.params)

    def build_agg(self, filters):
        self.agg = self._get_aggregation_on_rna_expression_tissue(
            filters, self._get_complimentary_facet_filters,
            self.get_size(), self.params.rna_expression_level)

    def get_default_size(self):
        return 300

    @staticmethod
    def _get_association_rna_range_filter(params):
        range_ok = ex_level_meet_conditions(
            params.rna_expression_level, 11, 1, 11)

        tissues = params.rna_expression_tissue
        t2tl = ex_level_tissues_to_terms_list

        q_score = {}
        if range_ok and tissues:
            # here the functionality
            q_score = {
                'constant_score': {
                    'filter': {
                        'bool': {
                            'must': t2tl('rna', tissues, params.rna_expression_level)
                        }
                    }
                }
            }

        return q_score

    @staticmethod
    def _get_aggregation_on_rna_expression_tissue(filters, filters_func, size,
                                                  ex_level):
        agg_filter = {}
        if ex_level > 0:
            agg_filter = {
                "filter": {
                    "bool": {
                        "must": filters_func(FilterTypes.RNA_EXPRESSION_TISSUE,
                                             filters),
                    }
                },
                "aggs": {
                    "data": {
                        "terms": {
                            "field": "private.facets.expression_tissues.rna." +
                            str(ex_level) + ".id.keyword",
                            "order" : { "_term" : "asc" },
                            'size': size
                        },
                        "aggs": {
                            "unique_target_count": {
                                "cardinality": {
                                    "field": "target.id",
                                    "precision_threshold": 1000
                                }
                            },
                            "unique_disease_count": {
                                "cardinality": {
                                    "field": "disease.id",
                                    "precision_threshold": 1000
                                }
                            }
                        }
                    }
                }
            }
        else:
            agg_filter = {
                "filter": {},
                "aggs": {
                    "data": {
                        "terms": {
                            "field": "private.facets.expression_tissues.rna." +
                            str(1) + ".id.keyword",
                            "order" : { "_term" : "asc" },
                            'size': size
                        },
                        "aggs": {
                            "unique_target_count": {
                                "cardinality": {
                                    "field": "target.id",
                                    "precision_threshold": 1000
                                }
                            },
                            "unique_disease_count": {
                                "cardinality": {
                                    "field": "disease.id",
                                    "precision_threshold": 1000
                                }
                            }
                        }
                    }
                }
            }

        # print(json.dumps(agg_filter, indent=4, sort_keys=True))
        return agg_filter


class AggregationUnitPROExLevel(AggregationUnit):
    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = \
                self._get_association_pro_range_filter(self.params)

    def get_default_size(self):
        return 25

    def build_agg(self, filters):
        d = addict.Dict()
        d.constant_score.filter.bool.must = \
            ex_level_tissues_to_terms_list('protein',
                                           self.params.protein_expression_tissue, 1)
        mut_filters = _copy_and_mutate_dict(filters,
                                             del_k='protein_expression_tissue',
                                             protein_expression_tissue=d.to_dict())
        self.agg = self._get_aggregation_on_pro_expression_level(
            mut_filters, self._get_complimentary_facet_filters,
            self.get_size(), self.params.protein_expression_level)

    @staticmethod
    def _get_association_pro_range_filter(params):
        range_ok = ex_level_meet_conditions(
            params.protein_expression_level, 4, 1, 4)

        q_filter = {}
        if range_ok:
            # here the functionality
            q_filter = {
                'constant_score': {
                    'filter': {
                        'bool': {
                            'must': [{
                                'exists': {
                                    'field':
                                    'private.facets.expression_tissues.protein.' +
                                    str(params.protein_expression_level)
                                }
                            }]
                        }
                    }
                }
            }

        return q_filter

    @staticmethod
    def _get_aggregation_on_pro_expression_level(filters, filters_func, size,
                                                 ex_level):
        agg_filter = {}

        if ex_level > 0:
            agg_filter = {
                "filter": {
                    "bool": {
                        "must": filters_func(FilterTypes.PROTEIN_EXPRESSION_LEVEL,
                                             filters)
                    }
                },
                "aggs": {
                    "data": {
                        "terms": {
                            "field":
                            "private.facets.expression_tissues.protein." +
                            str(1) + ".level",
                            "order": {
                                "unique_target_count": "desc"
                            },
                            'size': size
                        },
                        "aggs": {
                            "unique_target_count": {
                                "cardinality": {
                                    "field": "target.id",
                                    "precision_threshold": 1000
                                },
                            },
                            "unique_disease_count": {
                                "cardinality": {
                                    "field": "disease.id",
                                    "precision_threshold": 1000
                                },
                            }
                        }
                    }
                }
            }
        else:
            agg_filter = {
                "filter": {},
                "aggs": {
                    "data": {
                        "terms": {
                            "field":
                            "private.facets.expression_tissues.protein." +
                            str(1) + ".level",
                            "order": {
                                "unique_target_count": "desc"
                            },
                            'size': size
                        },
                        "aggs": {
                            "unique_target_count": {
                                "cardinality": {
                                    "field": "target.id",
                                    "precision_threshold": 1000
                                },
                            },
                            "unique_disease_count": {
                                "cardinality": {
                                    "field": "disease.id",
                                    "precision_threshold": 1000
                                },
                            }
                        }
                    }
                }
            }
        # print(json.dumps(agg_filter, indent=4, sort_keys=True))
        return agg_filter


class AggregationUnitPROExTissue(AggregationUnit):
    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = \
                self._get_association_pro_range_filter(self.params)

    def build_agg(self, filters):
        self.agg = self._get_aggregation_on_pro_expression_tissue(
            filters, self._get_complimentary_facet_filters,
            self.get_size(), self.params.protein_expression_level)

    def get_default_size(self):
        return 300

    @staticmethod
    def _get_association_pro_range_filter(params):
        range_ok = ex_level_meet_conditions(
            params.protein_expression_level, 4, 1, 4)

        tissues = params.protein_expression_tissue
        t2tl = ex_level_tissues_to_terms_list

        q_filter = {}
        if range_ok and tissues:
            # here the functionality
            q_filter = {
                'constant_score': {
                    'filter': {
                        'bool': {
                            'must': t2tl('protein', tissues, params.protein_expression_level)
                        }
                    }
                }
            }

        return q_filter

    @staticmethod
    def _get_aggregation_on_pro_expression_tissue(filters, filters_func, size,
                                                  ex_level):

        expression = {}
        if ex_level > 0:
            expression = {
                "filter": {
                    "bool": {
                        "must": filters_func(FilterTypes.PROTEIN_EXPRESSION_TISSUE,
                                             filters),
                    }
                },
                "aggs": {
                    "data": {
                        "terms": {
                            "field": "private.facets.expression_tissues.protein." +
                            str(ex_level) + ".id.keyword",
                            "order" : { "_term" : "asc" },
                            'size': size,
                        },
                        "aggs": {
                            "unique_target_count": {
                                "cardinality": {
                                    "field": "target.id",
                                    "precision_threshold": 1000
                                },
                            },
                            "unique_disease_count": {
                                "cardinality": {
                                    "field": "disease.id",
                                    "precision_threshold": 1000
                                },
                            }
                        }
                    }
                }
            }
        else:
            expression = {
                "filter": {},
                "aggs": {
                    "data": {
                        "terms": {
                            "field": "private.facets.expression_tissues.protein." +
                            str(1) + ".id.keyword",
                            "order" : { "_term" : "asc" },
                            'size': size,
                        },
                        "aggs": {
                            "unique_target_count": {
                                "cardinality": {
                                    "field": "target.id",
                                    "precision_threshold": 1000
                                },
                            },
                            "unique_disease_count": {
                                "cardinality": {
                                    "field": "disease.id",
                                    "precision_threshold": 1000
                                },
                            }
                        }
                    }
                }
            }


        return expression


class AggregationUnitScoreRange(AggregationUnit):
    def build_query_filter(self):
        if self.filter is not None:
            self.query_filter = self._get_association_score_range_filter(self.params)

    @staticmethod
    def _get_association_score_range_filter(params):
        if len(params.scorevalue_types) == 1:
            return {
                        "range" : {
                            params.association_score_method+"."+params.scorevalue_types[0] : {
                                "gte": params.filters[FilterTypes.SCORE_RANGE][0],
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
                                        "gte": params.filters[FilterTypes.SCORE_RANGE][0],
                                        "lte": params.filters[FilterTypes.SCORE_RANGE][1]
                                    }
                                }
                              }
                              for st in params.scorevalue_types]
                    }
                }

# class AggregationUnitUniprotKW(AggregationUnit):
#
#     def build_query_filter(self):
#         if self.filter is not None:
#             self.query_filter = self._get_complex_uniprot_kw_filter(self.filter,
#                                                                     BooleanFilterOperator.OR)
#     def build_agg(self, filters):
#         self.agg = self._get_uniprot_keywords_facet_aggregation(filters)
#
#     def _get_uniprot_keywords_facet_aggregation(self, filters):
#         return {
#             "filter": {
#                 "bool": {
#                     "must": self._get_complimentary_facet_filters(FilterTypes.UNIPROT_KW, filters),
#                 }
#             },
#             "aggs": {
#                 "data": {
#                     "significant_terms": {
#                         "field": "private.facets.uniprot_keywords",
#                         'size': 25,
#                     },
#                     "aggs": {
#                         "unique_target_count": {
#                             "cardinality": {
#                                 "field": "target.id",
#                                 "precision_threshold": 1000},
#                         },
#                         "unique_disease_count": {
#                             "cardinality": {
#                                 "field": "disease.id",
#                                 "precision_threshold": 1000},
#                         },
#                     },
#                 },
#             }
#         }
#
#     def _get_complex_uniprot_kw_filter(self, kw, bol):
#         pass
#         '''
#         :param kw: list of uniprot kw strings
#         :param bol: boolean operator to use for combining filters
#         :return: boolean filter
#         '''
#         if kw:
#             genes = self.handler.get_genes_for_uniprot_kw(kw)
#             if genes:
#                 return self.handler.get_complex_target_filter(genes, bol)
#         return dict()

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

    # TODO: Only the datatype length is affected by the default size, the datasource is not (see below)
    def get_default_size(self):
        return 20


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
                        "field": "private.facets.datatype.keyword",
                        'size': self.get_size(),
                    },
                    "aggs": {
                        "datasource": {
                            "terms": {
                                "field": "private.facets.datasource.keyword",
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

    _UNIT_MAP = {
        FilterTypes.DATATYPE: AggregationUnitDatasource,
        # FilterTypes.ECO : AggregationUnitECO,
        FilterTypes.DISEASE: AggregationUnitDisease,
        FilterTypes.TARGET: AggregationUnitTarget,
        FilterTypes.IS_DIRECT: AggregationUnitIsDirect,
        FilterTypes.PATHWAY: AggregationUnitPathway,
        FilterTypes.UNIPROT_KW: AggregationUnitUniprotKW,
        FilterTypes.SCORE_RANGE: AggregationUnitScoreRange,
        FilterTypes.THERAPEUTIC_AREA: AggregationUnitTherapeuticArea,
        FilterTypes.GO: AggregationUnitGO,
        FilterTypes.TARGET_CLASS: AggregationUnitTargetClass,
        FilterTypes.RNA_EXPRESSION_LEVEL: AggregationUnitRNAExLevel,
        FilterTypes.RNA_EXPRESSION_TISSUE: AggregationUnitRNAExTissue,
        FilterTypes.PROTEIN_EXPRESSION_LEVEL: AggregationUnitPROExLevel,
        FilterTypes.PROTEIN_EXPRESSION_TISSUE: AggregationUnitPROExTissue
    }

    _SERVICE_FILTER_TYPES = [FilterTypes.IS_DIRECT,
                             FilterTypes.SCORE_RANGE
                             ]

    def __init__(self, handler):
        self.handler = handler
        self.filter_types = FilterTypes().__dict__
        self.units = {}
        self.aggs = {}
        self.filters = {}

    def load_params(self, params):
        '''define and init units'''
        facets = params.facets != "false"
        for unit_type in self._UNIT_MAP:
            self.units[unit_type] = self._UNIT_MAP[unit_type](params.filters[unit_type],
                                                              params,
                                                              self.handler,
                                                              compute_aggs=facets)
        '''get filters'''
        for query_filter in self._UNIT_MAP:
            self.filters[query_filter] = self.units[query_filter].query_filter

        '''get aggregations if requested'''
        if params.facets != "false":
            aggs_not_to_be_returned = self._get_aggs_not_to_be_returned(params)
            '''get available aggregations'''
            for agg in self._UNIT_MAP:
                if agg not in aggs_not_to_be_returned:
                    if params.facets == "true" or params.facets == agg:
                        self.units[agg].build_agg(self.filters)
                        if self.units[agg].agg:
                            self.aggs[agg] = self.units[agg].agg


    def _get_AggregationUnit(self,str):
        return getattr(sys.modules[__name__], str)

    def _get_aggs_not_to_be_returned(self, params):
        '''avoid calculate a big facet if only one parameter is passed'''
        filters_to_apply = list(set([k for k,v in params.filters.items() if v is not None]))
        for filter_type in self._SERVICE_FILTER_TYPES:
            if filter_type in filters_to_apply:
                filters_to_apply.pop(filters_to_apply.index(filter_type))
        aggs_not_to_be_returned = []
        if len(filters_to_apply) == 1:  # do not return facet if only one filter is applied
            aggs_not_to_be_returned = filters_to_apply[0]

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

