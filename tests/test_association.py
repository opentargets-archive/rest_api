import ujson as json
import unittest

from app import create_app
from app.common.request_templates import FilterTypes
from tests import GenericTestCase


class AssociationTestCase(GenericTestCase):


    #@unittest.skip("testAssociationID")
    def testAssociationID(self):
        id = 'ENSG00000157764-EFO_0000701'#braf-skin disease
        response = self._make_request('/api/latest/public/association',
                                      data={'id':id},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['data'][0]['id'],id, 'association found')


    #@unittest.skip("testAssociationFilterNone")
    def testAssociationFilterNone(self):
        response = self._make_request('/api/latest/public/association/filter',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),0, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')

    #@unittest.skip("testAssociationFilterTargetGet")
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

    #@unittest.skip("testAssociationFilterTargetPost")
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
    
    def testAssociationFilterTargetsDiseaseGet(self):
        target = ['ENSG00000113448','ENSG00000172057']
        disease = 'EFO_0000270'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target':target,'disease':disease },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),2, 'association retrieved')
        if(json_response['data'][0]['target']['id'] == target[0]):
            self.assertEqual(json_response['data'][1]['target']['id'], target[1])
        elif(json_response['data'][0]['target']['id'] == target[1]):
            self.assertEqual(json_response['data'][1]['target']['id'], target[0])
        
        
    #@unittest.skip("testAssociationFilterTargetFacet")
    def testAssociationFilterTargetFacet(self):
        target = 'ENSG00000157764'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target':target, 'facets':"true", 'no_cache':True},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['data'][0]['target']['id'], target)
        self.assertIsNotNone(json_response['facets'])

    def testAssociationsSpecificFacet(self):
        target = 'ENSG00000157764'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target':target, 'facets':"disease", 'no_cache':True, 'size':0},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response['facets'])
        self.assertTrue('disease' in json_response['facets'])
        self.assertFalse('datatype' in json_response['facets'])

    def testAssociationDefaultDiseaseFacetSize(self):
        target = 'ENSG00000157764'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target':target, 'facets':"disease", 'no_cache':True, 'size':0},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response['facets'])
        self.assertTrue('disease' in json_response['facets'])
        self.assertEqual(len(json_response['facets']['disease']['buckets']), 25)


    def testAssociationsFacetSize(self):
        target = 'ENSG00000157764'
        facets_size = 50
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target':target, 'facets':"disease", 'facets_size': facets_size, 'no_cache':True, 'size':0},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response['facets'])
        self.assertTrue('disease' in json_response['facets'])
        self.assertEqual(len(json_response['facets']['disease']['buckets']), facets_size)


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

    def testAssociationFilterDiseaseTargetClassFacet(self):
        disease = 'EFO_0000311'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'facets': "true",
                                            },
                                      token=self._AUTO_GET_TOKEN)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response['facets'])
        self.assertIn('target_class', json_response['facets'])
        first_filter = json_response['facets'][FilterTypes.TARGET_CLASS]['buckets'][0]
        self.assertIn('key', first_filter)
        self.assertIn('label', first_filter)
        self.assertTrue(first_filter['label'])
        self.assertIn(FilterTypes.TARGET_CLASS, first_filter)
        first_sub_filter = first_filter[FilterTypes.TARGET_CLASS]['buckets'][0]
        self.assertIn('key', first_sub_filter)
        self.assertIn('label', first_sub_filter)
        self.assertTrue(first_sub_filter['label'])
        expected_results = first_filter['doc_count']
        query_key = first_filter['key']
        filtered_response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'facets': "true",
                                            FilterTypes.TARGET_CLASS : query_key,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        json_filtered_response = json.loads(filtered_response.data.decode('utf-8'))
        self.assertEqual(json_filtered_response['total'], expected_results)
        expected_results_sub = first_sub_filter['doc_count']
        query_key_sub = first_sub_filter['key']
        filtered_response_sub = self._make_request('/api/latest/public/association/filter',
                                               data={'disease': disease,
                                                     'facets': "true",
                                                     FilterTypes.TARGET_CLASS: query_key_sub,
                                                     },
                                               token=self._AUTO_GET_TOKEN)
        json_filtered_response_sub = json.loads(filtered_response_sub.data.decode('utf-8'))
        self.assertEqual(json_filtered_response_sub['total'], expected_results_sub)



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
                                              'size':1000},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        for i in range(len(json_response['data'])):
            entry_disease_id = json_response['data'][i]['disease']['id']
            self.assertEqual(entry_disease_id, disease, 'association is direct')

    def testAssociationFiltersearch(self):
        target = 'ENSG00000157764'
        '''test partial term'''
        search_query = 'lymph'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target': target,
                                            'size': 0,
                                            'search': search_query},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(json_response['total'], 2)

        '''test first term'''
        search_query = 'lymphoid'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target':target,
                                              'size':0,
                                            'search' : search_query },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(json_response['total'],2)

        '''test case sensitivity'''
        target = 'ENSG00000157764'
        search_query = 'LymPhoid'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target': target,
                                            'size': 0,
                                            'search': search_query,
                                            'no_cache': True},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(json_response['total'], 2)

        '''test empty space'''
        search_query = 'lymphoid '
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target': target,
                                            'size': 0,
                                            'search': search_query},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(json_response['total'], 2)

        '''test multi word'''
        search_query = 'lymphoid neoplasm'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target': target,
                                            'size': 0,
                                            'search': search_query},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(json_response['total'], 1)

        '''restrict by SOD1'''
        disease = 'EFO_0000253'
        search_query = 'SOD1'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease': disease,
                                            'size': 1,
                                            'search': search_query,
                                            'no_cache': True},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(json_response['total'], 1)
        self.assertEqual(json_response['data'][0]['target']['gene_info']['symbol'], search_query)

        '''restrict by threrapeutic area'''
        target = 'ENSG00000099769'
        search_query = 'endocri'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target': target,
                                            'size': 0,
                                            'search': search_query,
                                            'no_cache': True},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(json_response['total'], 3)



    def testAssociationFilterOrderByScore(self):

        disease = 'EFO_0000270'
        score_type='association_score.overall'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'sort': score_type,
                                            'size': '30',
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        sorted_scores = [d['association_score']['overall']for d in json_response['data']]
        for i in range(len(sorted_scores)-1):
            self.assertGreaterEqual(sorted_scores[i],
                                    sorted_scores[i+1],
                                    )

        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'sort': '~'+score_type,
                                            'size': '30',
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'),)
        self.assertGreaterEqual(len(json_response['data']),1, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        sorted_scores = [d['association_score']['overall']for d in json_response['data']]
        for i in range(len(sorted_scores)-1):
            self.assertGreaterEqual(sorted_scores[i+1],
                                    sorted_scores[i],
                                    )

    def testAssociationFilterOrderByDiseaseLabel(self):
        target = 'ENSG00000157764'
        sort_string = '~disease.efo_info.label'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target': target,
                                            'direct': True,
                                            'sort': sort_string,
                                            'size': '30',
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        sorted_disease_labels = [d['disease']['efo_info']['label'] for d in json_response['data']]
        for i in range(len(sorted_disease_labels) - 1):
            self.assertLessEqual(sorted_disease_labels[i],
                                 sorted_disease_labels[i+1],
                                )
        sort_string = 'disease.efo_info.label'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target': target,
                                            'direct': True,
                                            'sort': sort_string,
                                            'size': '30',
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        sorted_disease_labels = [d['disease']['efo_info']['label'] for d in json_response['data']]
        for i in range(len(sorted_disease_labels) - 1):
            self.assertGreaterEqual(sorted_disease_labels[i],
                                 sorted_disease_labels[i + 1],
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
        self.assertTrue(response.status_code == 200)
        full_json_response = json.loads(response.data.decode('utf-8'))
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'search': search_query,
                                            'size': 0,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
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

    def testAssociationFilterscore_value(self):

        disease = 'EFO_0000270'
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'size': 0,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        full_json_response = json.loads(response.data.decode('utf-8'))
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'scorevalue_min': 0.2,
                                            'scorevalue_types': ['datasources.gwas_catalog',
                                                                 'overall',
                                                                 'datatypes.literature'],
                                            'size': 0,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        filtered_json_response = json.loads(response.data.decode('utf-8'),)
        self.assertGreater(filtered_json_response['total'],0)
        self.assertGreater(full_json_response['total'],filtered_json_response['total'])

    def testAssociationCsvExport(self):

        disease = 'EFO_0000311'
        size = 100
        '''check size with no fields'''
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease': disease,
                                            'size': size,
                                            'format': 'csv',
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        full_response = response.data.decode('utf-8')
        '''check response size is equal to requeste size +header and empty final line'''
        self.assertTrue(len(full_response.split('\n'))==(size+2))

        '''check header order with requested fields'''
        fields = ['association_score.datatypes.literature',
                  'target.id',
                  'disease.id',
                  'association_score.overall']
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease': disease,
                                            'size': size,
                                            'format': 'csv',
                                            'fields':fields,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        full_response = response.data.decode('utf-8')
        '''check response size is equal to requeste size +header and empty final line'''
        self.assertEqual(len(full_response.split('\n')), size + 2)
        header = full_response.split('\n')[0].strip().split(',')
        self.assertEqual(len(fields), len(header))
        self.assertEqual(fields, header)
        # for i in range(len(fields)):


        '''check maximum request size'''
        size = 10000
        '''check size with no fields'''
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'disease': disease,
                                            'size': size,
                                            'format': 'csv',
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        full_response = response.data.decode('utf-8')
        '''check response size is equal to requeste size +header and empty final line'''
        self.assertEqual(len(full_response.split('\n')), (size + 2))

    # @unittest.skip("testAssociationScoreCap")
    def testAssociationScoreCap(self):
        response = self._make_request('/api/latest/public/association/filter',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']), 0, 'association retrieved')
        self.assertGreaterEqual(len(json_response['data']), 10, 'minimum default')
        for i in json_response['data']:
            self.assertLessEqual(i['association_score']['overall'],1)



if __name__ == "__main__":
     unittest.main()