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
            response= self.client.open('/api/latest/public/evidence/filter',data={'disease':disease})
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
                                       data=json.dumps({'disease':[disease]}),
                                       content_type='application/json')
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),0, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['disease']['id'], disease)








if __name__ == "__main__":
     unittest.main()