'''
Created on Sep 20, 2016

@author: priyankaw
'''

import unittest, json


from app import create_app
from tests import GenericTestCase

class EvidenceFacetsTestCase(GenericTestCase):
    
    def testEvidenceFacets(self):
        #target = 'ENSG00000157764'
        #dataype = 'literature'
        #disease = 'EFO_0000616'
        datasource='europepmc'
        target_ibd = 'ENSG00000073756'
        disease_ibd = 'EFO_0003767'
        target_als = 'ENSG00000089280'
        disease_als = 'EFO_0000253'
        target_parkinson = 'ENSG00000145335'
        disease_parkinson='EFO_0002508'
        target_cancer = 'ENSG00000066468'
        disease_cancer='EFO_0000311'

        response = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({'target':[target_cancer],
                                            'datasource':[datasource],
                                            'disease' :[disease_cancer],
                                            'facets':True,
                                            'size': 10
                                            }),content_type='application/json',
                                      method = 'POST',
                                      token=self._AUTO_GET_TOKEN)
 
    
        self.assertTrue(response.status_code == 200)
        
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response['facets'])

        self.assertGreater(len(json_response['facets']['journal']['data']['buckets']),0)
        self.assertGreater(len(json_response['facets']['disease']['data']['buckets']),0)
        self.assertGreater(len(json_response['facets']['pub_date']['data']['buckets']),0)
        self.assertGreater(len(json_response['facets']['meshterms']['data']['buckets']), 0)

    def testEvidenceFacets(self):
        # target = 'ENSG00000157764'
        # dataype = 'literature'
        # disease = 'EFO_0000616'
        datasource = 'europepmc'
        target_ibd = 'ENSG00000073756'
        disease_ibd = 'EFO_0003767'
        target_als = 'ENSG00000089280'
        disease_als = 'EFO_0000253'
        target_parkinson = 'ENSG00000145335'
        disease_parkinson = 'EFO_0002508'
        target_cancer = 'ENSG00000066468'
        disease_cancer = 'EFO_0000311'

        response = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({'target': [target_cancer],
                                                       'datasource': [datasource],
                                                       'disease': [disease_cancer],
                                                       'facets': True,
                                                       'size': 10
                                                       }), content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response['facets'])

        self.assertGreater(len(json_response['facets']['journal']['data']['buckets']), 0)
        self.assertGreater(len(json_response['facets']['disease']['data']['buckets']), 0)
        self.assertGreater(len(json_response['facets']['pub_date']['data']['buckets']), 0)
        self.assertGreater(len(json_response['facets']['meshterms']['data']['buckets']), 0)

    def testEvidenceFacetsFilteringByJournalFacet(self):
        target = 'ENSG00000157764'
        disease = 'EFO_0000616'
        datasource='europepmc'
        journal='pharmacol'
        target_ibd = 'ENSG00000073756'
        disease_ibd = 'EFO_0003767'
        disease_facet_filter = 'EFO_0000311'
      
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({'target':[target_ibd],
                                            'datasource':[datasource],
                                            'disease' :[disease_ibd],

                                            'facets':True,
                                            'size': 10
                                            }),content_type='application/json',
                                      method = 'POST',
                                      token=self._AUTO_GET_TOKEN)
 
    
        self.assertTrue(response.status_code == 200)
        
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response['facets'])
        self.assertIsNotNone(json_response['data'])

        response1 = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({'target': [target_ibd],
                                                       'datasource': [datasource],
                                                       'disease': [disease_ibd],
                                                       'disease_kw':[disease_facet_filter],

                                                       'facets': True,
                                                       'size': 10
                                                       }), content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)

        self.assertTrue(response1.status_code == 200)

        json_response1 = json.loads(response1.data.decode('utf-8'))
        self.assertNotEquals(json_response['total'],json_response1['total'])
        
    def testEvidenceWithoutFacets(self):
        datasource='europepmc'
        target_ibd = 'ENSG00000073756'
        disease_ibd = 'EFO_0003767'
        print "Testing Evidence API without faceting"
      
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({'target':[target_ibd],
                                            'datasource':[datasource],
                                            'disease' :[disease_ibd],
                                            'facets':False,
                                            'size': 10
                                            }),content_type='application/json',
                                      method = 'POST',
                                      token=self._AUTO_GET_TOKEN)
 
    
        self.assertTrue(response.status_code == 200)
        
        json_response = json.loads(response.data.decode('utf-8'))
        print(json_response)
        print "Facets -------------"
        print json_response['facets']
        self.assertIsNone(json_response['facets'])

    def testEvidenceFilteringUniprot(self):
            datasource = 'europepmc'
            target_ibd = 'ENSG00000073756'
            disease_ibd = 'EFO_0003767'
            uniprotkw = 'Acetylation'


            response = self._make_request('/api/latest/public/evidence/filter',
                                          data=json.dumps({'target': [target_ibd],
                                                           'datasource': [datasource],
                                                           'disease': [disease_ibd],
                                                           'uniprotkw':[uniprotkw],
                                                           'facets': True,
                                                           'size': 10
                                                           }), content_type='application/json',
                                          method='POST',
                                          token=self._AUTO_GET_TOKEN)

            self.assertTrue(response.status_code == 200)

            json_response = json.loads(response.data.decode('utf-8'))
            print(json_response)
            print "Facets -------------"
            print json_response['facets']
            self.assertIsNone(json_response['facets'])

    def testAssociationFilterTargetFacet(self):
        target = 'ENSG00000157764'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target':target, 'facets':True, 'therapeutic_area':'efo_0000651','no_cache':True},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['data'][0]['target']['id'], target)
        self.assertIsNotNone(json_response['facets'])
