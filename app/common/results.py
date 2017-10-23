import collections
import json
import sys
from io import BytesIO

import unicodecsv as csv
from dicttoxml import dicttoxml

from app.common.request_templates import SourceDataStructureOptions
from app.common.response_templates import ResponseType
from config import Config

reload(sys)
sys.setdefaultencoding('utf-8')

__author__ = 'andreap'

class Result(object):
    format = ResponseType.JSON

    def __init__(self,
                 res,
                 params = None,
                 data=[],
                 facets=None,
                 available_datatypes = [],
                 suggest=None,
                 status = ['ok'],
                 therapeutic_areas = []):

        '''
        :param res: elasticsearch query response
        :param params: get parameters
        :param data: data to display, use only to override default representation
        :param data_structure: a type of OutputDataStructureOptions
        '''

        self.res = res
        self.params = params
        self.data = data
        if params is not None:
            self.format = params.format
        self.facets = facets
        self.available_datatypes = available_datatypes
        self.status = status
        self.therapeutic_areas= therapeutic_areas
        self.suggest = suggest

    def toDict(self):
        raise NotImplementedError

    def __str__(self):
        if self.format == ResponseType.JSON:
            return self.toJSON()
        elif self.format == ResponseType.XML:
            return self.toXML()
        elif self.format == ResponseType.TSV:
            return self.toCSV(delimiter = '\t')
        elif self.format == ResponseType.CSV:
            return self.toCSV(delimiter=',')

    def toJSON(self):
        return json.dumps(self.toDict())

    def toXML(self):
        return dicttoxml(self.toDict(), custom_root='cttv-api-result')

    def toCSV(self, delimiter = '\t'):
        NOT_ALLOWED_FIELDS = ['evidence.evidence_chain', 'search_after']
        output = BytesIO()
        if not self.data:
            self.flatten(self.toDict())  # populate data if empty
        if self.data and isinstance(self.data[0], dict):
            key_set = set()
            flattened_data = []
            for row in self.data:
                flat = self.flatten(row,
                                    simplify=self.params.datastructure == SourceDataStructureOptions.SIMPLE)
                for field in NOT_ALLOWED_FIELDS:
                    flat.pop(field, None)
                flattened_data.append(flat)
                key_set.update(flat.keys())
            ordered_keys=self.params.fields or sorted(list(key_set))
            ordered_keys = map(unicode,ordered_keys)

            writer = csv.DictWriter(output,
                                    ordered_keys,
                                    restval='',
                                    delimiter=delimiter,
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL,
                                    doublequote=False,
                                    escapechar='\\',
                                    # extrasaction='ignore',
                                    )
            writer.writeheader()
            for row in flattened_data:
                writer.writerow(row)

        if self.data and isinstance(self.data[0], list):
            writer = csv.writer(output,
                                delimiter=delimiter,
                                quotechar='"',
                                quoting=csv.QUOTE_MINIMAL,
                                doublequote=False,
                                escapechar='\\',
                                # extrasaction = 'ignore',
                                )
            for row in self.data:
                writer.writerow(row)
        return output.getvalue()

    def flatten(self, d, parent_key='', sep='.', simplify=False):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return_dict = collections.OrderedDict()
        for k, v in items:
            if isinstance(v, list):
                try:
                    v = '|'.join(v).encode('utf-8')
                except:
                    if len(v) == 1:
                        v = v[0]
                    else:
                        v = json.dumps(v, encoding='utf-8')
            if isinstance(v, str):
                try:
                    v= unicode(v)
                except UnicodeDecodeError:
                    pass
            if not isinstance(v, unicode):
                v= json.dumps(v, encoding='utf-8')
            return_dict[unicode(k)] = unicode(v)
        if simplify:
            for k, v in items:
                try:
                    if v.startswith("http://identifiers.org/") or \
                            k.startswith("biological_object.properties."):
                        return_dict.pop(k)
                except:
                    pass

        return return_dict


class PaginatedResult(Result):
    def __init__(self, *args, **kwargs):
        '''

        :param total: count to return, needs to be passed as kwarg
        '''

        self.total = kwargs.pop('total', None)
        self.took = kwargs.pop('took', None)
        super(self.__class__,self).__init__(*args, **kwargs)
        if self.total is None:
            if self.res:
                self.total = self.res['hits']['total']
            else:
                self.total = len(self.data)
        if self.took is None:
            if self.res:
                self.took = self.res['took']
            else:
                self.took = 0.


    def toDict(self):
        if not self.data :
            if self.params.datastructure == SourceDataStructureOptions.COUNT:
                return {'total': self.total,
                        'took': self.took
                }
            elif self.params.datastructure == SourceDataStructureOptions.SIMPLE:
                self.data = [self.flatten(hit['_source'], simplify=True) for hit in self.res['hits']['hits']]

            else:
                self.data = [hit['_source'] for hit in self.res['hits']['hits']]
        else:
            if self.params and self.params.datastructure == SourceDataStructureOptions.SIMPLE:
                self.data = [self.flatten(hit['_source'], simplify=True) for hit in self.res['hits']['hits']]
        if self.facets is None:
            if self.res and 'aggregations' in self.res:
                self.facets = self.res['aggregations']

        response =  {'data': self.data,
                    'total': self.total,
                    'took': self.took,
                    'size': len(self.data) or 0,
                    'from': self.params.start_from,
                    'data_version' : Config.DATA_VERSION,
                    'query': self.params.query_params,
                    }
        if self.facets:
            response[ 'facets'] = self.facets
        if self.therapeutic_areas:
            response['therapeutic_areas'] = self.therapeutic_areas
        if self.params.search_after:
            response['query']['search_after']= self.params.search_after,
        return response

class EmptyPaginatedResult(Result):
    def toDict(self):
        if self.suggest:
            return {'data': [],
                    'suggest': self.suggest,
                    'facets': [],
                    'total': 0,
                    'took': 0,
                    'size': 0,
                    'from': 0,
                    'data_version': Config.DATA_VERSION,
                    }

        return {'data': [],
                'facets':[],
                'total': 0,
                'took': 0,
                'size': 0,
                'from': 0,
                'data_version': Config.DATA_VERSION,
        }


class SimpleResult(Result):
    ''' just need data to be passed and it will be returned as dict
    '''

    def toDict(self):
        if not self.data:
            try:
                self.data = [hit['_source'] for hit in self.res['hits']['hits']]
            except:
                raise AttributeError('some data is needed to be returned in a SimpleResult')
        return {'data': self.data,
                'data_version' : Config.DATA_VERSION,
                }

class RawResult(Result):
    ''' just need res to be passed and it will be returned as it is
    '''

    def toDict(self):
        if isinstance(self.res, dict):
            return self.res
        return json.loads(self.res)
    def toJSON(self):
        if isinstance(self.res, dict):
            return json.dumps(self.res)
        return self.res

class EmptySimpleResult(Result):
    def toDict(self):
        if self.suggest:
            return {'data': self.data,
                    'suggest':self.suggest,
                    'data_version': Config.DATA_VERSION,

                    }
        return {'data': self.data,
                'data_version' : Config.DATA_VERSION,
                }


class CountedResult(Result):

    def __init__(self, *args, **kwargs):
        '''

        :param total: count to return, needs to be passed as kwarg
        '''
        self.total = None
        if 'total' in kwargs:
            self.total = kwargs.pop('total')
        super(self.__class__,self).__init__(*args, **kwargs)
        if self.total is None:
            self.total = len(self.data)

    def toDict(self):
        if self.facets:
            return {'data': self.data,
                    'facets': self.facets,
                    'total': self.total,
                    'available_datatypes': self.available_datatypes,
                    'data_version': Config.DATA_VERSION,
                    }
        return {'data': self.data,
                'total': self.total,
                'available_datatypes': self.available_datatypes,
                'data_version' : Config.DATA_VERSION,
        }
