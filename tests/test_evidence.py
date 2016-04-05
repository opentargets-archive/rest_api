import unittest, json
import requests
import time

from flask import url_for

from app import create_app
from tests import GenericTestCase


class EvidenceTestCase(GenericTestCase):



    def testEvidenceByID(self):
        id = 'e1704ccbf8f2874000c5beb0ec84c2b8'
        response = self._make_request('/api/latest/public/evidence',
                                      data={'id':id},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['data'][0]['id'],id, 'evidence found')



    def testEvidenceFilterNone(self):
        response = self._make_request('/api/latest/public/evidence/filter',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')

    def testEvidenceFilterTargetGet(self):
        target = 'ENSG00000157764'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'target':target},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['target']['id'], target)

    def testEvidenceFilterTargetPost(self):
        target = 'ENSG00000157764'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({'target':[target]}),
                                      content_type='application/json',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['target']['id'], target)

    def testEvidenceFilterDiseaseGet(self):
        disease = 'EFO_0000311'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'disease':disease,
                                            'direct':True,},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        efo_code_found = False
        for path in json_response['data'][0]['disease']['efo_info']['path']:
            if disease in path:
                efo_code_found = True
                break
        self.assertTrue(efo_code_found)

    def testEvidenceFilterDiseasePost(self):
        disease = 'EFO_0000311'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({'disease':[disease],
                                                        'direct':True,
                                                        }),
                                      content_type='application/json',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        efo_code_found = False
        for path in json_response['data'][0]['disease']['efo_info']['path']:
            if disease in path:
                efo_code_found = True
                break
        self.assertTrue(efo_code_found)

    # def testEvidenceFilterDirect(self):
    #     disease = 'EFO_0000311'
    #     'indirect call'
    #     response = self._make_request('/api/latest/public/evidence/filter',
    #                                   data={'disease':disease,
    #                                         'direct':False,
    #                                         'fields':['disease.efo_info.path',
    #                                                 'disease.id'
    #                                                 ],
    #                                         'size':10},
    #                                   token=self._AUTO_GET_TOKEN)
    #     self.assertTrue(response.status_code == 200)
    #     json_response = json.loads(response.data.decode('utf-8'))
    #     self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
    #     indirect_found = False
    #     for i in range(len(json_response['data'])):
    #         entry_disease_id = json_response['data'][i]['disease']['id']
    #         paths = json_response['data'][i]['disease']['efo_info']['path']
    #         all_codes = []
    #         for p in paths:
    #             all_codes.extend(p)
    #         if entry_disease_id != disease:
    #             self.assertIn(disease, all_codes,'disease in path')
    #             indirect_found = True
    #     self.assertTrue(indirect_found, 'indirect evidence found')
    #     'direct call'
    #     response = self._make_request('/api/latest/public/evidence/filter',
    #                                   data={'disease':disease,
    #                                         'direct':True,
    #                                         'fields':['disease.efo_info.path',
    #                                                 'disease.id'
    #                                                 ],
    #                                         'size':100},
    #                                   token=self._AUTO_GET_TOKEN)
    #     self.assertTrue(response.status_code == 200)
    #     json_response = json.loads(response.data.decode('utf-8'))
    #     self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
    #     for i in range(len(json_response['data'])):
    #         entry_disease_id = json_response['data'][i]['disease']['id']
    #         self.assertEqual(entry_disease_id, disease, 'evidence is direct')

    def testEvidenceFilterScore(self):
        disease = 'EFO_0000311'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'size': 0,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        full_json_response = json.loads(response.data.decode('utf-8'))
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'scorevalue_min': 0.2,
                                            'scorevalue_max': 0.9,
                                            'size':0,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        filtered_json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreater(filtered_json_response['total'],0)
        self.assertGreater(full_json_response['total'],filtered_json_response['total'])

    def testEvidenceFilterSortByField(self):
        disease = 'EFO_0000311'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'size': 10,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        default_json_response = json.loads(response.data.decode('utf-8'))
        sorted_scores = [d['scores']['association_score'] for d in default_json_response['data']]
        for i in range(len(sorted_scores) - 1):
            self.assertLessEqual(sorted_scores[i + 1],
                                    sorted_scores[i],
                                    )
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'sort': 'target.id',
                                            'size':1,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        reordered_json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(default_json_response['total'],reordered_json_response['total'])
        self.assertNotEqual(default_json_response['data'][0]['id'],
                            reordered_json_response['data'][0]['id'])




if __name__ == "__main__":
     unittest.main()