__author__ = 'andreap'

from flask import Flask, Response
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



        if type == ResponseType.JSON:
            resp = Response(response=result.toJSON(),
                            status=200,
                            mimetype="application/json")
        elif type == ResponseType.XML:
            resp = Response(response=result.toXML(),
                            status=200,
                            mimetype="text/xml")
        elif type == ResponseType.CSV:
            resp = Response(response=result.toCSV(),
                            status=200,
                            mimetype="text/csv")
        else:
            resp = Response(response=str(result),
                            status=200,
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
