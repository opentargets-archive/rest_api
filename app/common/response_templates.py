import json
import time
from datetime import datetime

from app.common.datatypes import DataTypes
from app.common.rate_limit import increment_call_rate, RateLimiter, ceil_dt_to_future_time
from app.common.scoring_conf import ScoringMethods

__author__ = 'andreap'

from flask import Flask, Response, current_app, request
from flask.ext.restful import fields
from flask_restful_swagger import swagger


class ResponseType():
    JSON='json'
    XML='xml'
    CSV='table'


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
            elif "text/csv"in accept_header:
                type = ResponseType.CSV


        if type == ResponseType.JSON:
            resp = Response(response=result.toJSON(),
                            status=status,
                            mimetype="application/json")
        elif type == ResponseType.XML:
            resp = Response(response=result.toXML(),
                            status=status,
                            mimetype="text/xml")
        elif type == ResponseType.CSV:
            resp = Response(response=result.toCSV(),
                            status=status,
                            mimetype="text/csv")
        else:
            resp = Response(response=str(result),
                            status=status,
                            mimetype="application/json")
        if took > 0.5:
            cache_time = str(int(3600*took))# set cache to last one our for each second spent in the request
            resp.headers.add('X-Accel-Expires', cache_time)
        msec = int(round(took*1000))
        current_values = increment_call_rate(msec)
        rate_limiter = RateLimiter()
        now = datetime.now()
        resp.headers.add('X-API-Took', int(round(msec)))
        resp.headers.add('X-RateLimit-Limit-10s', rate_limiter.short_window_rate)
        resp.headers.add('X-RateLimit-Limit-1h', rate_limiter.long_window_rate)
        resp.headers.add('X-RateLimit-Remaining-10s', rate_limiter.short_window_rate-current_values['short'])
        resp.headers.add('X-RateLimit-Remaining-1h', rate_limiter.long_window_rate-current_values['long'])
        resp.headers.add('X-RateLimit-Reset-10s', round(ceil_dt_to_future_time(now, 10),2))
        resp.headers.add('X-RateLimit-Reset-1h', round(ceil_dt_to_future_time(now, 3600),2))
        return resp


class Results(fields.Raw):
    def format(self):
        return 'Results data'

@swagger.model
class PaginatedResponse():
     resource_fields = {
      'data': fields.List(Results,attribute='Query results'),
      'total':fields.Integer(attribute='total of results returned', ),
      'took': fields.Integer(attribute='time took to complete the query'),
      'from': fields.Integer(attribute='paginate from',),
      'size': fields.Integer(attribute='size to return', ),

  }



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
        self.hit = hit
        self.cap_scores = cap_scores
        self.parse_hit()

    def parse_hit(self):
        self.data['target'] = {}
        self.data['target']['id'] = self.hit['target']['id']
        self.data['target']['name'] = self.hit['target']['gene_info']['name']
        self.data['target']['symbol'] = self.hit['target']['gene_info']['symbol']

        self.data['disease'] = {}
        self.data['disease']['id'] = self.hit['disease']['id']
        self.data['disease']['name'] = self.hit['disease']['efo_info']['label']
        # self.data['label'] = self.hit['disease']['efo_info']['label']
        self.data['disease']['therapeutic_area'] = self.hit['disease']['efo_info']['therapeutic_area']
        self.data['therapeutic_area'] = self.hit['disease']['efo_info']['therapeutic_area']

        self.data['id'] = self.hit['id']

        self.data['is_direct'] = self.hit['is_direct']
        self._is_direct = self.hit['is_direct']

        evidence_count = self.hit['evidence_count']
        self.data['evidence_count'] = evidence_count['total']
        score = self.hit[self._scoring_method]
        self.data['association_score'] = self._cap_score(score['overall'])
        self.data['datatypes']=[]
        for dt in score['datatypes']:
            datasources = []
            for ds in self._datatypes.get_datasources(dt):
                datasources.append(dict(datasource = ds,
                                        association_score = self._cap_score(score['datasources'][ds]),
                                        evidence_count = evidence_count['datasource'][ds],))

            self.data['datatypes'].append(dict(datatype = dt,
                                               association_score = self._cap_score(score['datatypes'][dt]),
                                               evidence_count = evidence_count['datatype'][dt],
                                               datasources =datasources))

    def _cap_score(self, score):
        if self.cap_scores:
            if score >1:
                return 1.
        return score


class DataStats(object):

    def __init__(self):
        pass

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