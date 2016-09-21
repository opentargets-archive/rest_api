'''
Created on Sep 20, 2016

@author: priyankaw
'''

import unittest, json


from app import create_app
from tests import GenericTestCase

class EvidenceFacetsTestCase(GenericTestCase):
    
    def testEvidenceFacetsSigTerms(self):
        target = 'ENSG00000157764'
        #dataype = 'literature'
        disease = 'EFO_0000616'
        datasource='europepmc'
#{"terms": {"disease.id": ["EFO_0000474"]}},
#{"terms": {"target.id": ["ENSG00000153253"]}}]}}
        print "Testing Evidence Facets using Significant Terms Aggregations"
      
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({'target':[target],
                                            'datasource':[datasource],
                                            'disease' :[disease],
                                            'direct':True,
                                            'facets':True,
                                            'size': 10
                                            }),content_type='application/json',
                                      method = 'POST',
                                      token=self._AUTO_GET_TOKEN)
 
    
        self.assertTrue(response.status_code == 200)
        
        json_response = json.loads(response.data.decode('utf-8'))
        print(json_response)
        print "Facets -------------"
        print json_response['facets']
        self.assertIsNotNone(json_response['facets'])
         
    def testEvidenceFacetsFiltering(self):
        target = 'ENSG00000157764'
        #dataype = 'literature'
        disease = 'EFO_0000616'
        datasource='europepmc'
        abstract='threonine'
#{"terms": {"disease.id": ["EFO_0000474"]}},
#{"terms": {"target.id": ["ENSG00000153253"]}}]}}
        print "Testing Evidence Facets Filtering"
      
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({'target':[target],
                                            'datasource':[datasource],
                                            'disease' :[disease],
                                            'abstract':abstract,
                                            'direct':True,
                                            'facets':True,
                                            'size': 10
                                            }),content_type='application/json',
                                      method = 'POST',
                                      token=self._AUTO_GET_TOKEN)
 
    
        self.assertTrue(response.status_code == 200)
        
        json_response = json.loads(response.data.decode('utf-8'))
        print(json_response)
        print "Facets -------------"
        print json_response['facets']
        self.assertIsNotNone(json_response['facets'])
        self.assertIsNotNone(json_response['data'])
              
