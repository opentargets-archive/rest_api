__author__ = 'andreap'

from flask import Flask, Response

class ResponseType():
    JSON='json'
    XML='xml'
    CSV='table'


class CTTVResponse():

    @staticmethod
    def OK(result,type = None):
        '''
        :param result: instance of common.elasticsearchclient.Result
        :param type: value of ResponseType
        :return:
        '''

        if type is None:
            resp = Response(response=str(result),
                            status=200,
                            mimetype="application/json")
            return resp

        if type == ResponseType.JSON:
            resp = Response(response=result.toJSON(),
                            status=200,
                            mimetype="application/json")
            return resp
        elif type == ResponseType.XML:
            resp = Response(response=result.toXML(),
                            status=200,
                            mimetype="text/xml")
            return resp
        elif type == ResponseType.CSV:
            resp = Response(response=result.toCSV(),
                            status=200,
                            mimetype="text/csv")
            return resp
