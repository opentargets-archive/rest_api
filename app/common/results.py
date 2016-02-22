import collections
from app.common.request_templates import SourceDataStructureOptions
from app.common.response_templates import ResponseType
from dicttoxml import dicttoxml
import collections
import pprint
import itertools
import csv
from StringIO import StringIO
import json

__author__ = 'andreap'

class Result(object):
    format = ResponseType.JSON

    def __init__(self,
                 res,
                 params = None,
                 data=None,
                 facets=None,
                 available_datatypes = [],
                 status = ['ok']):
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
        NOT_ALLOWED_FIELDS = ['evidence.evidence_chain']
        output = StringIO()
        if self.data is None:
            self.flatten(self.toDict())  # populate data if empty
        if isinstance(self.data[0], dict):
            key_set = set()
            flattened_data = []
            for row in self.data:
                flat = self.flatten(row,
                                    simplify=self.params.datastructure == SourceDataStructureOptions.SIMPLE)
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

    def flatten(self, d, parent_key='', sep='.', simplify=False):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return_dict = {}
        for k, v in items:
            if isinstance(v, list):
                if len(v) == 1:
                    v = v[0]
            return_dict[k] = v
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
    def toDict(self):
        if self.data is None:
            if self.params.datastructure == SourceDataStructureOptions.COUNT:
                return {'total': self.res['hits']['total'],
                        'took': self.res['took']
                }
            elif self.params.datastructure == SourceDataStructureOptions.SIMPLE:
                self.data = [self.flatten(hit['_source'], simplify=True) for hit in self.res['hits']['hits']]

            else:
                self.data = [hit['_source'] for hit in self.res['hits']['hits']]
        else:
            if self.params.datastructure == SourceDataStructureOptions.SIMPLE:
                self.data = [self.flatten(hit['_source'], simplify=True) for hit in self.res['hits']['hits']]
        if self.facets is None:
            if 'aggregations' in self.res:
                self.facets = self.res['aggregations']

        return {'data': self.data,
                'facets':self.facets,
                'total': self.res['hits']['total'],
                'took': self.res['took'],
                'size': len(self.data) or 0,
                'from': self.params.start_from,
                # 'status' : self.status,
        }

class EmptyPaginatedResult(Result):
    def toDict(self):

        return {'data': [],
                'facets':[],
                'total': 0,
                'took': 0,
                'size': 0,
                'from': 0,
                # 'status' : self.status,
        }


class SimpleResult(Result):
    ''' just need data to be passed and it will be returned as dict
    '''

    def toDict(self):
        if  self.data is None:
            try:
                self.data = [hit['_source'] for hit in self.res['hits']['hits']]
            except:
                raise AttributeError('some data is needed to be returned in a SimpleResult')
        return {'data': self.data,
                # 'status' : self.status,
                }

class RawResult(Result):
    ''' just need res to be passed and it will be returned as it is
    '''

    def toDict(self):
        return json.loads(self.res)
    def toJSON(self):
        return self.res

class EmptySimpleResult(Result):
    def toDict(self):
        return {'data':[],
                # 'status' : self.status,
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
                    # 'status' : self.status,
            }
        return {'data': self.data,
                'total': self.total,
                'available_datatypes': self.available_datatypes,
                # 'status' : self.status,
        }