import unittest, json
import requests
import time

from flask import url_for

from app import create_app


class AssociationTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.host = 'http://'+self.app_context.url_adapter.get_host('')


    def tearDown(self):
        self.app_context.pop()


    def testAssociationID(self):
        id = 'ENSG00000157764-EFO_0000701'#braf-skin disease
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/association', data={'id':id})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['data'][0]['id'],id, 'association found')



    def testAssociationFilterNone(self):
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/association/filter')
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),0, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')

    def testAssociationFilterTargetGet(self):
        target = 'ENSG00000157764'
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/association/filter',data={'target':target})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['target']['id'], target)

    def testAssociationFilterTargetPost(self):
        target = 'ENSG00000157764'
        status_code = 429
        while status_code == 429:
            response= self.client.post('/api/latest/public/association/filter',
                                       data=json.dumps({'target':[target]}),
                                       content_type='application/json')
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['target']['id'], target)

    def testAssociationFilterDiseaseGet(self):
        disease = 'EFO_0000311'
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/association/filter',
                                       data={'disease':disease,
                                             'direct':False,
                                            })
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['disease']['id'], disease)

    def testAssociationFilterDiseasePost(self):
        disease = 'EFO_0000311'
        status_code = 429
        while status_code == 429:
            response= self.client.post('/api/latest/public/association/filter',
                                       data=json.dumps({'disease':[disease],
                                                        'direct':False,
                                                        }),
                                       content_type='application/json')
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['disease']['id'], disease)



    def testAssociationFilterDirect(self):
        disease = 'EFO_0000311'
        'indirect call'
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/association/filter',data={'disease':disease,
                                                                                  'direct':False,
                                                                                  'fields':['is_direct',
                                                                                            'disease.id'
                                                                                            ],
                                                                                  'size':1000})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
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
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/association/filter',data={'disease':disease,
                                                                                  'direct':True,
                                                                                  'fields':['is_direct',
                                                                                            'disease.id'
                                                                                            ],
                                                                                  'size':1000})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        for i in range(len(json_response['data'])):
            entry_disease_id = json_response['data'][i]['disease']['id']
            self.assertEqual(entry_disease_id, disease, 'association is direct')





if __name__ == "__main__":
     unittest.main()