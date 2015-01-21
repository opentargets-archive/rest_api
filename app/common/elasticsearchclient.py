from collections import defaultdict
import collections
import pprint
from flask import current_app
import itertools
import ujson as json
from dicttoxml import dicttoxml
import csv
from StringIO import StringIO
from elasticsearch import helpers
import operator
from app.common.responses import ResponseType
from app.common.requests import OutputDataStructureOptions
import logging


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
                 index_data = None,
                 index_efo = None,
                 index_eco = None,
                 index_genename = None,
                 docname_data = None,
                 docname_efo = None,
                 docname_eco = None,
                 docname_genename = None,
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

        self.handler= handler
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
        res = self.handler.search(index=self._index_data,
                doc_type=self._docname_data,
                body = {
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
                        'size':params.size,
                        'from':params.start_from,
                        '_source': OutputDataStructureOptions.getSource(params.datastructure)
                        }
                )

        if res['hits']['total']==0: #search by name
            ensemblid = self._get_ensemblid_from_gene_name(gene)
            if ensemblid:
                ensemblid = ensemblid[0]
                res = self.handler.search(index=self._index_data,
                        doc_type=self._docname_data,
                        body = {
                                "query": {
                                    "filtered": {
                                      "query": {
                                        "match_all": {}
                                      },
                                      "filter": {
                                        "term": {
                                          "biological_subject.about": "http://identifiers.org/ensembl/"+ensemblid,


                                        }
                                      }
                                    }
                                  },
                                'size':params.size,
                                'from':params.start_from,
                                '_source': OutputDataStructureOptions.getSource(params.datastructure)
                                }
                        )

        current_app.logger.debug("Got %d Hits in %ims"%(res['hits']['total'],res['took']))

        return PaginatedResult(res,params)

    def free_text_search(self, searchphrase,
                         filter = FreeTextFilterOptions.ALL,
                         **kwargs):
        '''
        Multiple types of fuzzy search are supported by elasticsearch and the differences can be confusing. The list below attempts to disambiguate these various types.

        match query + fuzziness option: Adding the fuzziness parameter to a match query turns a plain match query into a fuzzy one. Analyzes the query text before performing the search.
        fuzzy query: The elasticsearch fuzzy query type should generally be avoided. Acts much like a term query. Does not analyze the query text first.
        fuzzy_like_this/fuzzy_like_this_field: A more_like_this query, but supports fuzziness, and has a tuned scoring algorithm that better handles the characteristics of fuzzy matched results.*
        suggesters: Suggesters are not an actual query type, but rather a separate type of operation (internally built on top of fuzzy queries) that can be run either alongside a query, or independently. Suggesters are great for 'did you mean' style functionality.

        :param searchphrase:
        :param filter:
        :param kwargs:
        :return:
        '''
        searchphrase = searchphrase.lower()
        params = SearchParams(**kwargs)
        if filter.lower() == FreeTextFilterOptions.ALL:
            doc_types = [self._docname_efo,self._docname_genename]
        elif filter.lower() == FreeTextFilterOptions.GENE:
            doc_types = [self._docname_genename]
        elif filter.lower() == FreeTextFilterOptions.EFO:
            doc_types = [self._docname_efo]
        res = self.handler.search(index=[self._index_efo,
                                         self._index_genename],
                doc_type= doc_types,
                body={'query' : self._get_free_text_query(searchphrase),
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
            if hit['_type'] == self._docname_genename:
                datapoint['title'] = hit['_source']['approved_symbol']
                datapoint['description'] = hit['_source']['approved_name'].split('[')[0]
            elif hit['_type'] == self._docname_efo:
                datapoint['title'] = hit['_source']['label']
                datapoint['description'] = ' > '.join(hit['_source']['path_labels'])
            data.append(datapoint)
        return PaginatedResult(res, params, data)


    def autocomplete_search(self, searchphrase,
                         filter = FreeTextFilterOptions.ALL,
                         **kwargs):
        '''
        Multiple types of fuzzy search are supported by elasticsearch and the differences can be confusing. The list below attempts to disambiguate these various types.

        match query + fuzziness option: Adding the fuzziness parameter to a match query turns a plain match query into a fuzzy one. Analyzes the query text before performing the search.
        fuzzy query: The elasticsearch fuzzy query type should generally be avoided. Acts much like a term query. Does not analyze the query text first.
        fuzzy_like_this/fuzzy_like_this_field: A more_like_this query, but supports fuzziness, and has a tuned scoring algorithm that better handles the characteristics of fuzzy matched results.*
        suggesters: Suggesters are not an actual query type, but rather a separate type of operation (internally built on top of fuzzy queries) that can be run either alongside a query, or independently. Suggesters are great for 'did you mean' style functionality.

        :param searchphrase:
        :param filter:
        :param kwargs:
        :return:
        '''

        def format_datapoint(hit):
            datapoint = dict(type = hit['_type'],
                             id =  hit['_id'],
                             score =  hit['_score'],)
            datapoint.update(hit['_source'])
            if hit['_type'] == self._docname_genename:
                returned_ids['genes'].append(hit['_id'])
            elif hit['_type'] == self._docname_efo:
                returned_ids['efo'].append(hit['_id'])

            return datapoint



        searchphrase = searchphrase.lower()
        params = SearchParams(**kwargs)

        data = dict(besthit = None,
                    genes=[],
                    efo = [])
        returned_ids = dict(genes=[],
                            efo = [])

        res = self.handler.search(index=[self._index_efo,
                                         self._index_genename],
                doc_type= [self._docname_efo,self._docname_genename],
                body={'query' : self._get_free_text_query(searchphrase),
                      'size' : 30,
                      '_source': OutputDataStructureOptions.getSource(OutputDataStructureOptions.GENE_AND_DISEASE)
                      }
            )
        current_app.logger.debug("Got %d Hits in %ims"%(res['hits']['total'],res['took']))

        if res['hits']['total']:
            '''handle best hit'''
            best_hit = res['hits']['hits'][0]
            data['besthit'] = format_datapoint(best_hit)

            ''' store the other results in the corresponding object'''
            for hit in res['hits']['hits'][1:]:
                data['besthit']

                if hit['_type'] == self._docname_genename:
                    if len(data['genes'])<params.size:
                        data['genes'].append(format_datapoint(hit))
                elif hit['_type'] == self._docname_efo:
                     if len(data['efo'])<params.size:
                        data['efo'].append(format_datapoint(hit))
            '''if there are not enough fill the results for both the categories'''

            if len(data['genes'])<params.size:
                res_genes = self.handler.search(index= self._index_genename,
                    doc_type= self._docname_genename,
                    body={'query' : self._get_free_text_gene_query(searchphrase),
                          'size' : params.size+1,
                          '_source': OutputDataStructureOptions.getSource(OutputDataStructureOptions.GENE)
                          }
                )
                current_app.logger.debug("Got %d additional Gene Hits in %ims"%(res_genes['hits']['total'],res['took']))
                for hit in res_genes['hits']['hits']:
                    if len(data['genes'])<params.size:
                        if hit['_id'] not in returned_ids['genes']:
                            data['genes'].append(format_datapoint(hit))

            if len(data['efo'])<params.size:
                res_efo = self.handler.search(index=self._index_efo,
                    doc_type= self._docname_efo,
                    body={'query' : self._get_free_text_efo_query(searchphrase),
                          'size' : params.size+1,
                          '_source': OutputDataStructureOptions.getSource(OutputDataStructureOptions.DISEASE)
                          }
                )
                current_app.logger.debug("Got %d additional EFO Hits in %ims"%(res_efo['hits']['total'],res['took']))
                for hit in res_efo['hits']['hits']:
                    if len(data['efo'])<params.size:
                        if hit['_id'] not in returned_ids['efo']:
                            data['efo'].append(format_datapoint(hit))

        return SimpleResult(None, params, data)

    def _get_ensemblid_from_gene_name(self,genename, **kwargs):
        res = self.handler.search(index=self._index_genename,
                    doc_type=self._docname_genename,
                    body={'query': {
                            'match': {"Associated Gene Name":genename}

                            },
                          'size':1,
                          'fields': ['Ensembl Gene ID']
                          }
                )
        current_app.logger.debug("Got %d gene id  Hits in %ims"%(res['hits']['total'],res['took']))
        return [hit['fields']['Ensembl Gene ID'][0] for hit in res['hits']['hits']]

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
                             doc_type=self._docname_data,
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
                doc_type=self._docname_efo,
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
                doc_type=self._docname_efo,
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


        res = self.handler.search(index=self._index_data,
                doc_type=self._docname_data,
                body = {
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
                        'size':params.size,
                        'from':params.start_from,
                        '_source': OutputDataStructureOptions.getSource(params.datastructure)
                        },
                timeout="1m",
                )


        return  PaginatedResult(res,params)

    def get_evidences_by_id(self, evidenceid, **kwargs):

        if isinstance(evidenceid, str):
            evidenceid=[evidenceid]


        res = self.handler.search(index=self._index_data,
                doc_type=self._docname_data,
                body={'filter': {
                                "ids" : {
                                        "type" : self._docname_data,
                                        "values" : evidenceid
                                        }
                                }
                }
            )
        if res['hits']['total']:
                return [ hit['_source'] for hit in res['hits']['hits']]

    def get_label_for_eco_code(self, code):
        res = self.handler.search(index=self._index_eco,
                doc_type=self._docname_eco,
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
            doc_type=self._docname_data,
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

    def get_evidences(self,
                      genes =[],
                      objects = [],
                      evidence_types = [],
                      gene_operator = 'OR',
                      object_operator = 'OR',
                      evidence_type_operator = 'OR',
                      **kwargs):
        params = SearchParams(**kwargs)
        '''convert boolean to elasticsearch syntax'''
        gene_operator = getattr(BooleanFilterOperator, gene_operator.upper())
        object_operator =  getattr(BooleanFilterOperator, object_operator.upper())
        evidence_type_operator = getattr(BooleanFilterOperator, evidence_type_operator.upper())
        '''create multiple condition boolean query'''
        conditions = []
        if genes:
            conditions.append(self._get_complex_gene_filter(genes, gene_operator))
        if objects:
            conditions.append(self._get_complex_object_filter(objects, object_operator))
        if evidence_types:
            conditions.append(self._get_complex_evidence_type_filter(evidence_types, evidence_type_operator))
        '''boolean query joining multiple conditions with an AND'''
        res = self.handler.search(index=self._index_data,
                doc_type=self._docname_data,
                body = {
                        "query": {
                            "filtered": {
                                "filter" : {
                                    "bool" : {
                                        "must" : conditions
                                    }
                                }

                            }
                          },
                        'size':params.size,
                        'from':params.start_from,
                        '_source': OutputDataStructureOptions.getSource(params.datastructure)
                        }
                )

        data = None
        if params.datastructure in [OutputDataStructureOptions.FULL, OutputDataStructureOptions.SIMPLE] :
            data = self._inject_view_specific_data([hit['_source'] for hit in res['hits']['hits']], params)
        return PaginatedResult(res,params, data)

    def _get_gene_filter(self, gene):
        return [
                # gene,
                # "http://identifiers.org/uniprot/"+gene,
                "http://identifiers.org/ensembl/"+gene,
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
                        bol : [{
                                "terms" :{
                                    "biological_subject.about": self._get_gene_filter(gene)}
                                }
                               for gene in genes]
                        }
                   }
        return dict()


    def _get_object_filter(self, object):
        return [object,
                "http://identifiers.org/efo/"+object,
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
                                "terms" :{
                                    "biological_object.about": self._get_object_filter(object)}
                                }
                               for object in objects]
                        }
                   }
        return dict()

    def _get_evidence_type_filter(self, evidence_type):
        return [evidence_type,
                "http://identifiers.org/eco/"+evidence_type,
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
                        bol : [{
                                "terms" :{
                                    "evidence.evidence_codes": self._get_evidence_type_filter(evidence_type)}
                                }
                               for evidence_type in evidence_types]
                        }
                   }
        return dict()

    def _get_generic_gene_info(self, geneids, output_format = OutputDataStructureOptions.FULL):
        '''
        :param geneids: list of gene ids, must be the same used to index gene info in elasticsearch
        :return: dictionary containing generic data about the genes
        '''
        geneinfo = {}

        if geneids:
            res = self.handler.search(index=self._index_genename,
                doc_type=self._docname_genename,
                body={'filter': {
                                "ids" : {
                                        "type" : "genename",
                                        "values" : geneids
                                        }
                                }
                }
            )
            if res['hits']['total']:
                for hit in res['hits']['hits']:
                    if output_format == OutputDataStructureOptions.FULL:
                        geneinfo[hit['_id']]=dict(gene_name = hit['_source']["Associated Gene Name"],
                                                  gene_description = hit['_source']["Description"].split('[')[0].strip(),
                                                  ensembl_id = hit['_source']["Ensembl Gene ID"]
                                                  )
                    elif output_format == OutputDataStructureOptions.SIMPLE:
                        geneinfo[hit['_id']]=dict(gene_name = hit['_source']["Associated Gene Name"])

        return geneinfo

    def _get_generic_efo_info(self, efocodes, output_format = OutputDataStructureOptions.FULL):
        '''
        :param efocodes: list of efo code
        :return: dictionary containing generic data about the efo
        '''


        def get_match_query(code):
            return  { "match": { "label":  code}},

        def clean_code(code):
            if '/' in code:
                code = code.split('/')[-1]
            return code


        efoinfo = {}

        if efocodes:
            res = self.handler.search(index=self._index_efo,
                doc_type=self._docname_efo,
                body={"query": {
                        "bool": {
                          "should": [ get_match_query(code) for code in efocodes ]
                            }
                         }
                     }
            )
            if res['hits']['total']:
                for hit in res['hits']['hits']:
                    if output_format == OutputDataStructureOptions.FULL:
                        efoinfo[clean_code(hit['_id'])]=dict(efo_label = hit['_source']["label"],
                                                 efo_path = hit['_source']["path"])

                    elif output_format == OutputDataStructureOptions.SIMPLE:
                        efoinfo[clean_code(hit['_id'])]=dict(efo_label = hit['_source']["label"])
            if ('EFO_0000000' in efocodes) or ("http://identifiers.org/efo/EFO_0000000" in efocodes):
                if output_format == OutputDataStructureOptions.FULL:
                    efoinfo["EFO_0000000"]=dict(efo_label = "N/A",
                                                efo_path = "N/A")

                elif output_format == OutputDataStructureOptions.SIMPLE:
                    efoinfo["EFO_0000000"]=dict(efo_label = "N/A")

        return_info = {}
        for code in efocodes:
            if code in efoinfo:
                return_info[code]=efoinfo[code]
            else:
                if output_format == OutputDataStructureOptions.FULL:
                    return_info[code]=dict(efo_label = code,
                                           efo_path = "N/A")

                elif output_format == OutputDataStructureOptions.SIMPLE:
                    return_info[code]=dict(efo_label = code)
        return return_info

    def _get_generic_eco_info(self, ecocodes, output_format = OutputDataStructureOptions.FULL):
        '''
        :param ecocodes: list of lists of efo codes
        :return: dictionary containing generic data about each eco list
        '''
        ecoinfo = {}

        flat_eco_list = list(itertools.chain(*ecocodes))
        if flat_eco_list:
            res = self.handler.search(index=self._index_eco,
                doc_type=self._docname_eco,
                body={'filter': {
                                "ids" : {
                                        "type" : "eco",
                                        "values" : flat_eco_list
                                        }
                                }
                }
            )
            if res['hits']['total']:
                for hit in res['hits']['hits']:
                        ecoinfo[hit['_id']]=hit['_source']["definition"].split("[")[0].replace('"','').strip()
        return_info = dict()
        for codelist in ecocodes:
            labels=[]
            for code in codelist:
                if code in ecoinfo:
                    labels.append(ecoinfo[code])
                else:
                    labels.append("N/A")
            return_info[''.join(codelist)]= dict(eco_label = ', '.join(labels))

        return return_info

    def _inject_view_specific_data(self, evidences, params):
        def get_gene_id_from_evidence(evidence):
            about = evidence["biological_subject"]["about"][0]
            if '/' in about:
                geneid = about.split('/')[-1]
                if not geneid.startswith('ENSG'):
                    geneid = self.get_ensemblid_from_uniprotid(geneid)#TODO: cache this
                return geneid
            return about
        def get_efo_code_from_evidence(evidence):
            about = evidence["biological_object"]["about"][0]
            if '/' in about:
                code = about.split('/')[-1]
                if not code.startswith('EFO_'):
                    code = 'EFO_'+code
                if code == 'EFO_0000000':#temporary fix for EVA corrupted data
                    try:
                        code = evidence['biological_object']["properties"]["experimental_evidence_specific"]["unmapped_disease_term"]
                    except:
                        pass
                return code
            return about
        def get_eco_code_from_evidence(evidence):
            eco = []
            try:

                for code in evidence["evidence"]["evidence_codes"]:
                    eco.append(code.split('/')[-1])
            except:
                return ["N/A"]
            return eco

        gene_ids = list(set(map(get_gene_id_from_evidence, evidences)))
        gene_info = None
        try:
            gene_info = self._get_generic_gene_info(gene_ids, params.datastructure)
        except:
            pass
        efo_codes = list(set(map(get_efo_code_from_evidence, evidences)))
        efo_info = None
        try:
            efo_info = self._get_generic_efo_info(efo_codes, params.datastructure)
        except:
            pass
        eco_codes = map(get_eco_code_from_evidence, evidences)
        eco_info=None
        try:
            eco_info = self._get_generic_eco_info(eco_codes, params.datastructure)
        except:
            pass
        updated_evidences = []
        for evidence in evidences:
            try:
                if gene_info:
                    geneid = get_gene_id_from_evidence(evidence)
                    if geneid in gene_info:
                        if gene_info[geneid]:
                            evidence["biological_subject"]["gene_info"] = gene_info[geneid]
            except:
                pass #TODO: log this
            try:
                if efo_info:
                    efocode = get_efo_code_from_evidence(evidence)
                    if efocode in efo_info:
                        if efo_info[efocode]:
                            evidence["biological_object"]["efo_info"] = efo_info[efocode]
            except:
                pass #TODO: log this
            try:
                if eco_info:
                    ecocode = get_eco_code_from_evidence(evidence)
                    code_hash = ''.join(ecocode)
                    if code_hash in eco_info:
                        if eco_info[code_hash]:
                            evidence["evidence"]["evidence_type"] = eco_info[code_hash]
            except:
                pass #TODO: log this
            updated_evidences.append(evidence)
        return updated_evidences

    def _get_free_text_query(self, searchphrase):
        return {"bool" : {
                    "should" : [
                        {'match': {
                            "label" : {
                                    "query" :         searchphrase,
                                    "boost" :         2.0,
                                    "prefix_length" : 1,
                                    "max_expansions": 100,
                                    "fuzziness": "AUTO"

                                },
                            }},
                        {'match': {
                            "synonyms" : {
                                    "query" :         searchphrase,
                                    "boost" :         1.0,
                                    "prefix_length" : 1,
                                    "max_expansions": 100,
                                    "fuzziness": "AUTO"
                                },
                            }},
                        {'match': {
                            "biotype" : {
                                    "query" :         "unprocessed_pseudogene",
                                    "boost" :         -10.0,
                                },
                            }},

                        {'match': {
                            "label" : {
                                    "query" :         searchphrase,
                                    "boost" :         1.0,
                                    "prefix_length" : 1,
                                    "max_expansions": 100,
                                    "fuzziness": "AUTO"
                                },
                            }},
                        {'match': {
                            "id" : {
                                    "query" :         searchphrase,
                                    "boost" :         3.0,
                                },
                            }},
                        {'match': {
                            "approved_symbol" : {
                                    "query" :         searchphrase,
                                    "boost" :         5.0,
                                },
                            }},
                        {'prefix': {
                            "approved_symbol" : {
                                    "value" :         searchphrase,
                                    "boost" :         3.0,
                                },
                            }},
                        {'match': {
                            "approved_name" : {
                                    "query" :         searchphrase,
                                    "boost" :         5.0,
                                    "prefix_length" : 0,
                                    "max_expansions": 5,
                                    "fuzziness": "AUTO"
                                },
                            }},
                        {'match': {
                            "gene_family_description" : {
                                    "query" :         searchphrase,
                                    "boost" :         1.0,
                                    "prefix_length" : 0,
                                    "max_expansions": 5,
                                    "fuzziness": "AUTO"
                                },
                            }},
                        {'match': {
                            "uniprot_accessions" : {
                                    "query" :         searchphrase,
                                    "boost" :         3.0,
                                },
                            }},
                        {'match': {
                            "hgnc_id" : {
                                    "query" :         searchphrase,
                                    "boost" :         3.0,
                                },
                            }}
                        ]
                    }
                }


    def _get_free_text_gene_query(self, searchphrase):
        return { "bool" : {
                    "should" : [
                        {'match': {
                            "id" : {
                                    "query" :         searchphrase,
                                    "boost" :         3.0,
                                },
                            }},
                        {'match': {
                            "approved_symbol" : {
                                    "query" :         searchphrase,
                                    "boost" :         3.0,
                                },
                            }},
                        {'prefix': {
                            "approved_symbol" : {
                                    "value" :         searchphrase,
                                    "boost" :         5.0,
                                },
                            }},
                        {'match': {
                            "approved_name" : {
                                    "query" :         searchphrase,
                                    "boost" :         3.0,
                                    "prefix_length" : 1,
                                    "max_expansions": 5,
                                    "fuzziness": "AUTO"
                                },
                            }},
                        {'match': {
                            "gene_family_description" : {
                                    "query" :         searchphrase,
                                    "boost" :         1.0,
                                    "prefix_length" : 0,
                                    "max_expansions": 5,
                                    "fuzziness": "AUTO"
                                },
                            }},
                        {'match': {
                            "uniprot_accessions" : {
                                    "query" :         searchphrase,
                                    "boost" :         3.0,
                                },
                            }},
                        {'match': {
                            "biotype" : {
                                    "query" :         "unprocessed_pseudogene",
                                    "boost" :         -10.0,
                                },
                            }},
                        {'match': {
                            "hgnc_id" : {
                                    "query" :         searchphrase,
                                    "boost" :         3.0,
                                },
                            }}
                        ]
                    }

                }
    def _get_free_text_efo_query(self, searchphrase):
        return {"bool" : {
                    "should" : [
                       {'match': {
                            "label" : {
                                    "query" :         searchphrase,
                                    "boost" :         2.0,
                                    "prefix_length" : 1,
                                    "max_expansions": 100,
                                    "fuzziness": "AUTO"

                                },
                            }},
                        {'match': {
                            "synonyms" : {
                                    "query" :         searchphrase,
                                    "boost" :         1.0,
                                    "prefix_length" : 1,
                                    "max_expansions": 100,
                                    "fuzziness": "AUTO"
                                },
                            }},
                        {'match': {
                            "label" : {
                                    "query" :         searchphrase,
                                    "boost" :         1.0,
                                    "prefix_length" : 1,
                                    "max_expansions": 100,
                                    "fuzziness": "AUTO"
                                },
                            }},
                        {'match': {
                            "id" : {
                                    "query" :         searchphrase,
                                    "boost" :         3.0,
                                },
                            }},
                        ]
                    }

                }


class SearchParams():

    _max_search_result_limit = 1000
    _default_return_size = 10
    _allowed_groupby = ['gene','evidence-type', 'efo']


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
        NOT_ALLOWED_FIELDS=['evidence.evidence_chain']
        output = StringIO()
        if self.data is None:
            self.flatten(self.toDict())#populate data if empty
        if isinstance(self.data[0], dict):
            key_set = set()
            flattened_data = []
            for row in self.data:
                flat = self.flatten(row,
                                    simplify=self.params.datastructure==OutputDataStructureOptions.SIMPLE)
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

    def flatten(self, d, parent_key='', sep='.', simplify = False):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return_dict = {}
        for k,v in items:
            if isinstance(v,list):
                if len(v) ==1:
                    v= v[0]
            return_dict[k]=v
        if simplify:
            for k,v in items:
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
                 return {'total' :self.res['hits']['total'],
                         'took' : self.res['took']
                        }
            elif self.params.datastructure == OutputDataStructureOptions.SIMPLE:
                self.data = [self.flatten(hit['_source'], simplify=True) for hit in self.res['hits']['hits']]

            else:
                self.data = [hit['_source'] for hit in self.res['hits']['hits']]
        else:
            if self.params.datastructure == OutputDataStructureOptions.SIMPLE:
                self.data = [self.flatten(hit['_source'], simplify=True) for hit in self.res['hits']['hits']]

        return {'data' : self.data,
                'total' :self.res['hits']['total'],
                'took' : self.res['took'],
                'size' : len(self.data) or 0,
                'from' : self.params.start_from
                }

class SimpleResult(Result):
    ''' just need data to be passed and it will be returned as dict
    '''
    def toDict(self):
        if not  self.data:
            raise AttributeError('some data is needed to be returned in a SimpleResult')
        return {'data' : self.data}