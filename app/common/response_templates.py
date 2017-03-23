import json
import time
from datetime import datetime

from app.common.signals import LogApiCallWeight
from app.common.datatypes import DataTypes
from app.common.rate_limit import increment_call_rate, RateLimiter, ceil_dt_to_future_time
from app.common.scoring_conf import ScoringMethods
from config import Config

__author__ = 'andreap'

from flask import Flask, Response, current_app, request
from flask.ext.restful import fields


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
            elif "text/tab-separated-values"in accept_header:
                type = ResponseType.TSV
            elif "text/csv" in accept_header:
                type = ResponseType.TSV


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
        self._scoring_method = scoring_method
        if datatypes is None:
            datatypes = DataTypes(current_app)
        self._datatypes = datatypes
        self.hit_source = {}
        if '_source' in hit:
            self.hit_source = hit['_source']
        self.is_scoring_capped = cap_scores
        self.parse_hit()

    def parse_hit(self):
        self.data = self.hit_source
        # self.data['target'] = {}
        # self.data['target']['id'] = self.hit['target']['id']
        # self.data['target']['name'] = self.hit['target']['gene_info']['name']
        # self.data['target']['symbol'] = self.hit['target']['gene_info']['symbol']
        #
        # self.data['disease'] = {}
        # self.data['disease']['id'] = self.hit['disease']['id']
        # self.data['disease']['name'] = self.hit['disease']['efo_info']['label']
        # # self.data['label'] = self.hit['disease']['efo_info']['label']
        # self.data['disease']['therapeutic_area'] = self.hit['disease']['efo_info']['therapeutic_area']
        # self.data['disease']['path'] = self.hit['disease']['efo_info']['path']
        #
        # self.data['id'] = self.hit['id']
        #
        # self.data['is_direct'] = self.hit['is_direct']
        # self.is_direct = self.hit['is_direct']
        #
        # evidence_count = self.hit['evidence_count']
        # self.data['evidence_count'] = evidence_count['total']
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

    # self.data['datatypes']=[]
        # for dt in score['datatypes']:
        #     datasources = []
        #     for ds in self._datatypes.get_datasources(dt):
        #         datasources.append(dict(datasource = ds,
        #                                 association_score = self._cap_score(score['datasources'][ds]),
        #                                 evidence_count = evidence_count['datasource'][ds],))
        #
        #     self.data['datatypes'].append(dict(datatype = dt,
        #                                        association_score = self._cap_score(score['datatypes'][dt]),
        #                                        evidence_count = evidence_count['datatype'][dt],
        #                                        datasources =datasources))

    def _cap_score(self, score):
        if self.is_scoring_capped:
            self.cap_score(score)
        return score

    @staticmethod
    def cap_score(score):
        if score >1:
            return 1.
        return score


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

        self.evidencestrings = dict(total = res['hits']['total'],
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


        self.associations = dict(total = res['hits']['total'],
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


