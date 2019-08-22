import json

from app.common.datatypes import DataTypes
from app.common.scoring_conf import ScoringMethods
from config import Config

__author__ = 'andreap'

from flask import Flask, Response, current_app, request
from flask_restful import fields
import pprint

class ResponseType():
    JSON='json'
    XML='xml'
    TSV= 'tab'
    CSV = 'csv'


class CTTVResponse():

    @staticmethod
    def OK(result,
           type = None,
           took =0.):
        '''
        :param result: instance of common.results.Result
        :param type: value of ResponseType
        :return:
        '''

        status = 200
        try:
            if result.status != ['ok']:
                status = 203
        except:
            pass

        accept_header = request.headers.get('Accept')

        if type is None and accept_header:
            if 'application/json' in accept_header:
                type = ResponseType.JSON
            elif "text/xml"in accept_header:
                type = ResponseType.XML
            elif "text/tab-separated-values" in accept_header:
                type = ResponseType.TSV
            elif "text/csv" in accept_header:
                type = ResponseType.CSV


        if type == ResponseType.JSON or result.format == ResponseType.JSON:
            resp = Response(response=result.toJSON(),
                            status=status,
                            mimetype="application/json")
        elif type == ResponseType.XML or result.format == ResponseType.XML:
            resp = Response(response=result.toXML(),
                            status=status,
                            mimetype="text/xml")
        elif type == ResponseType.TSV or result.format == ResponseType.TSV:
            resp = Response(response=result.toCSV(delimiter='\t'),
                            status=status,
                            mimetype="text/tab-separated-values")
        elif type == ResponseType.CSV or result.format == ResponseType.CSV:
            resp = Response(response=result.toCSV(delimiter=','),
                            status=status,
                            mimetype="text/csv")
        else:
            resp = Response(response=str(result),
                            status=status,
                            mimetype="application/json")
        return resp



class Results(fields.Raw):
    def format(self):
        return 'Results data'



class Association(object):

    def __init__(self,
                 hit,
                 scoring_method=ScoringMethods.DEFAULT,
                 datatypes = None,
                 cap_scores = True):
        '''

        :param hit: association object coming from elasticsearch
        :param scoring_method: association object coming from elasticsearch
        :return:
        '''

        self.data ={}
        self.search_metadata = {}
        self._scoring_method = scoring_method
        if datatypes is None:
            datatypes = DataTypes(current_app)
        self._datatypes = datatypes
        self.hit_source = {}
        if '_source' in hit:
            self.hit_source = hit['_source']
        self.is_scoring_capped = cap_scores

        if 'sort' in hit:
            self.search_metadata['sort'] = hit['sort']

        self.parse_hit()

    def parse_hit(self):
        self.data = self.hit_source
        # if self.search_metadata:
        #     self.data['search_metadata'] = self.search_metadata
        if self._scoring_method in self.hit_source:
            self.data['association_score'] = self.hit_source[self._scoring_method]
            del self.data[self._scoring_method]
            if 'overall' in self.data['association_score']:
                self.data['association_score']['overall'] = self._cap_score(self.data['association_score']['overall'])
            if 'datatypes' in self.data['association_score']:
                for dt in self.data['association_score']['datatypes']:
                    self.data['association_score']['datatypes'][dt] = self._cap_score(self.data['association_score']['datatypes'][dt])
            if 'datasources' in self.data['association_score']:
                for ds in self.data['association_score']['datasources']:
                    self.data['association_score']['datasources'][ds] = self._cap_score(
                        self.data['association_score']['datasources'][ds])

    def _cap_score(self, score):
        if self.is_scoring_capped:
            return self.cap_score(score)
        return score

    @staticmethod
    def cap_score(score):
        if score >1:
            return 1.
        return score

class SearchMetadataObject(object):

    def __init__(self,
                 hit,):
        '''

        :param hit: association object coming from elasticsearch
        :param scoring_method: association object coming from elasticsearch
        :return:
        '''

        self.data ={}
        self.search_metadata = {}
        self.hit_source = {}
        if '_source' in hit:
            self.hit_source = hit['_source']
            if 'id' in self.hit_source and not self.hit_source['id']:
                self.hit_source['id'] =  hit['_id']
        if 'sort' in hit:
            self.search_metadata['sort'] = hit['sort']
        self.parse_hit()

    def parse_hit(self):
        self.data = self.hit_source
        # if self.search_metadata:
        #     self.data['search_metadata'] = self.search_metadata


class TherapeuticArea(object):

    def __init__(self):
        self.data_version=Config.DATA_VERSION

    def __str__(self):
        return json.dumps(self.__dict__)

    def add_therapeuticareas(self, res):
        datatypes = []
        index = 0
        for bucket in res['aggregations']['therapeutic_labels']['buckets']:
            datasources = {}
            datasources['label'] = bucket['key']
            datasources['code'] = res['aggregations']['therapeutic_codes']['buckets'][index]['key']
            datatypes.append(datasources)
            index=index+1

        self.therapeuticareas = datatypes
        self.total = str(index)

class DataMetrics(object):

    def __init__(self):
        self.data_version=Config.DATA_VERSION

    def __str__(self):
        return json.dumps(self.__dict__)

    def add_genes(self, res):
        self.genes = res['aggregations']

    def add_evidences(self, res):
        self.evidences = res['aggregations']

    def add_evidencestring(self, res):
        datatypes = {}
        for bucket in res['aggregations']['data']['buckets']:
            datatypes[bucket['key']]={'total':bucket['doc_count']}
            datasources = {}
            for ds_bucket in bucket['datasources']['buckets']:
                datasources[ds_bucket['key']]={'total':ds_bucket['doc_count']}
                datatypes[bucket['key']]['datasources']=datasources

        self.evidencestrings = dict(total = res['hits']['total']['value'],
                                    datatypes= datatypes)

    def add_associations(self, res, known_datatypes):
        datatypes = {}
        for bucket in res['aggregations']['data']['buckets']:
            datatypes[bucket['key']]={'total':bucket['doc_count']}
            datasources = {}
            for ds_bucket in bucket['datasources']['buckets']:
                try:
                    if known_datatypes.is_datasources_in_datatype(ds_bucket['key'], bucket['key']):
                        datasources[ds_bucket['key']]={'total':ds_bucket['doc_count']}
                        datatypes[bucket['key']]['datasources']=datasources
                except KeyError:
                    pass


        self.associations = dict(total = res['hits']['total']['value'],
                                 datatypes= datatypes)


class DataStats(object):

    def __init__(self):
        self.data_version=Config.DATA_VERSION

    def __str__(self):
        return json.dumps(self.__dict__)

    def add_evidencestring(self, res):
        datatypes = {}
        for bucket in res['aggregations']['data']['buckets']:
            datatypes[bucket['key']]={'total':bucket['doc_count']}
            datasources = {}
            for ds_bucket in bucket['datasources']['buckets']:
                datasources[ds_bucket['key']]={'total':ds_bucket['doc_count']}
                datatypes[bucket['key']]['datasources']=datasources

        self.evidencestrings = dict(datatypes= datatypes)

    def add_associations(self, res, index_association_stats, known_datatypes):
        datatypes = {}
        for bucket in res['aggregations']['data']['buckets']:
            datatypes[bucket['key']]={'total':bucket['doc_count']}
            datasources = {}
            for ds_bucket in bucket['datasources']['buckets']:
                try:
                    if known_datatypes.is_datasources_in_datatype(ds_bucket['key'], bucket['key']):
                        datasources[ds_bucket['key']]={'total':ds_bucket['doc_count']}
                        datatypes[bucket['key']]['datasources']=datasources
                except KeyError:
                    pass


        self.associations = dict(total = index_association_stats,
                                 datatypes= datatypes)

    def add_key_value(self, key, value):
        self.__dict__[key]={'total': value}

class RelationTypes(object):
    SHARED_TARGETS = 'shared-targets'
    SHARED_DISEASES = 'shared-diseases'
    UNKNOWN = None

class RelationDirection(object):
        RIGHT = 'right'
        LEFT = 'left'
        BOTH = 'both'
        UNKNOWN = None

class Relation(object, ):

    def __init__(self,
                 subject,
                 object,
                 type=RelationTypes.UNKNOWN,
                 direction = RelationDirection.UNKNOWN,
                 value = 0.,
                 **kwargs):
        self.subject = subject
        self.object = object
        self.type = type
        self.direction = direction
        self.value = value
        self.__dict__.update(**kwargs)

    def to_dict(self):
        return self.__dict__


