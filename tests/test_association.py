import decimal
import unittest
import ujson as json
import requests
import time

from flask import url_for

from app import create_app
from tests import GenericTestCase


class AssociationTestCase(GenericTestCase):

    def _get_score(self, datapoint,score_type):
            if score_type == 'overall':
                 return datapoint['association_score']
            elif score_type.startswith('datatypes'):
                for i in datapoint['datatypes']:
                    if i['datatype']== score_type.split('.')[1]:
                        return i['association_score']
            elif score_type.startswith('datasources'):
                for i in datapoint['datasources']:
                    if i['datatype']== score_type.split('.')[1]:
                        return i['association_score']


    def testAssociationID(self):
        id = 'ENSG00000157764-EFO_0000701'#braf-skin disease
        response = self._make_request('/api/latest/public/association',
                                      data={'id':id},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['data'][0]['id'],id, 'association found')



    def testAssociationFilterNone(self):
        response = self._make_request('/api/latest/public/association/filter',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),0, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')

    def testAssociationFilterTargetGet(self):
        target = 'ENSG00000157764'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target':target},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['target']['id'], target)

    def testAssociationFilterTargetPost(self):
        target = 'ENSG00000157764'
        response = self._make_request('/api/latest/public/association/filter',
                                      data=json.dumps({'target':[target]}),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['target']['id'], target)

    def testAssociationFilterDiseaseGet(self):
        disease = 'EFO_0000311'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                             'direct':False},
                                      token=self._AUTO_GET_TOKEN)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['disease']['id'], disease)

    def testAssociationFilterDiseasePost(self):
        disease = 'EFO_0000311'
        response = self._make_request('/api/latest/public/association/filter',
                                      data=json.dumps({'disease':[disease],
                                                        'direct':False,
                                                        }),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['disease']['id'], disease)



    def testAssociationFilterDirect(self):
        disease = 'EFO_0000311'
        'indirect call'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                              'direct':False,
                                              'fields':['is_direct',
                                                        'disease.id'
                                                        ],
                                              'size':1000},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        indirect_found = False
        for i in range(len(json_response['data'])):
            d = json_response['data'][i]['is_direct']
            indirect_found = not d
            if indirect_found:
                break
        self.assertTrue(indirect_found, 'indirect association found')
        'direct call'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                              'direct':True,
                                              'fields':['is_direct',
                                                        'disease.id'
                                                        ],
                                              'size':1000},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        for i in range(len(json_response['data'])):
            entry_disease_id = json_response['data'][i]['disease']['id']
            self.assertEqual(entry_disease_id, disease, 'association is direct')


    def testAssociationFilterOrder(self):

        disease = 'EFO_0000270'
        score_type='overall'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'sort': score_type,
                                            'size': '30',
                                            },
                                      token=self._AUTO_GET_TOKEN)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        sorted_scores = [self._get_score(d, score_type) for d in json_response['data']]
        for i in range(len(sorted_scores)-1):
            self.assertGreaterEqual(sorted_scores[i],
                                    sorted_scores[i+1],
                                    )

        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'sort': '~overall',
                                            'size': '30',
                                            },
                                      token=self._AUTO_GET_TOKEN)
        json_response = json.loads(response.data.decode('utf-8'),)
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        sorted_scores = [self._get_score(d, score_type) for d in json_response['data']]
        for i in range(len(sorted_scores)-1):
            self.assertGreaterEqual(sorted_scores[i+1],
                                    sorted_scores[i],
                                    )

    def testAssociationFilterSearch(self):

        disease = 'EFO_0000270'
        search_query='ENSG00000100012'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'size': 0,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        full_json_response = json.loads(response.data.decode('utf-8'))


        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'search': search_query,
                                            'size': 0,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        filtered_json_response = json.loads(response.data.decode('utf-8'),)
        self.assertGreater(full_json_response['total'],filtered_json_response['total'])
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'search': search_query[:-2],
                                            'size': 0,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        filtered_json_response = json.loads(response.data.decode('utf-8'),)
        self.assertGreater(full_json_response['total'],filtered_json_response['total'])




if __name__ == "__main__":
     unittest.main()