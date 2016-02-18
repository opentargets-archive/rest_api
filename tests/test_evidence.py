import unittest, json
import requests
import time

from flask import url_for

from app import create_app


class EvidenceTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.host = 'http://'+self.app_context.url_adapter.get_host('')


    def tearDown(self):
        self.app_context.pop()


    def testEvidenceByID(self):
        id = 'e1704ccbf8f2874000c5beb0ec84c2b8'
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/evidence', data={'id':id})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['data'][0]['id'],id, 'evidence found')



    def testEvidenceFilterNone(self):
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/evidence/filter')
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),0, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')

    def testEvidenceFilterTargetGet(self):
        target = 'ENSG00000157764'
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/evidence/filter',data={'target':target})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),0, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['target']['id'], target)

    def testEvidenceFilterTargetPost(self):
        target = 'ENSG00000157764'
        status_code = 429
        while status_code == 429:
            response= self.client.post('/api/latest/public/evidence/filter',
                                       data=json.dumps({'target':[target]}),
                                       content_type='application/json')
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),0, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['target']['id'], target)

    def testEvidenceFilterDiseaseGet(self):
        disease = 'EFO_0000311'
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/evidence/filter',data={'disease':disease,
                                                                                  'direct':True,
                                                                                  })
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),0, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['disease']['id'], disease)

    def testEvidenceFilterDiseasePost(self):
        disease = 'EFO_0000311'
        status_code = 429
        while status_code == 429:
            response= self.client.post('/api/latest/public/evidence/filter',
                                       data=json.dumps({'disease':[disease],
                                                        'direct':True,
                                                        }),
                                       content_type='application/json')
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),0, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['disease']['id'], disease)



    def testEvidenceFilterDirect(self):
        disease = 'EFO_0000311'
        'indirect call'
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/evidence/filter',data={'disease':disease,
                                                                                  'direct':False,
                                                                                  'fields':['disease.efo_info.path',
                                                                                            'disease.id'
                                                                                            ],
                                                                                  'size':10})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),0, 'evidence retrieved')
        indirect_found = False
        for i in range(len(json_response['data'])):
            entry_disease_id = json_response['data'][i]['disease']['id']
            paths = json_response['data'][i]['disease']['efo_info']['path']
            all_codes = []
            for p in paths:
                all_codes.extend(p)
            if entry_disease_id != disease:
                self.assertIn(disease, all_codes,'disease in path')
                indirect_found = True
        self.assertTrue(indirect_found, 'indirect evidence found')
        'direct call'
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/evidence/filter',data={'disease':disease,
                                                                                  'direct':True,
                                                                                  'fields':['disease.efo_info.path',
                                                                                            'disease.id'
                                                                                            ],
                                                                                  'size':100})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),0, 'evidence retrieved')
        for i in range(len(json_response['data'])):
            entry_disease_id = json_response['data'][i]['disease']['id']
            self.assertEqual(entry_disease_id, disease, 'entry is direct')





if __name__ == "__main__":
     unittest.main()