from app import DataTypes
from app.common.scoring_conf import ScoringMethods

__author__ = 'andreap'

from flask import Flask, Response, current_app
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
           took = 0):
        '''
        :param result: instance of common.elasticsearchclient.Result
        :param type: value of ResponseType
        :return:
        '''

        status = 200
        if result.status != ['ok']:
            status = 203

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
        resp.headers.add('X-API-Took', int(round(took*1000)))
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

