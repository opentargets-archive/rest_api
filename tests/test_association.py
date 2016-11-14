import ujson as json
import unittest

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
                                      data={'target':target, 'facets':True, 'no_cache':True},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['data'][0]['target']['id'], target)
        self.assertIsNotNone(json_response['facets'])

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


    def testAssociationFilterOrder(self):

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

    def testAssociationFilterTargetEnrichmentGet(self):
        target = ["ENSG00000073756", "ENSG00000095303", "ENSG00000280151", "ENSG00000108219", "ENSG00000198369",
                  "ENSG00000105401", "ENSG00000134882", "ENSG00000104998", "ENSG00000181915", "ENSG00000119919",
                  "ENSG00000105397", "ENSG00000178623", "ENSG00000107968", "ENSG00000133195", "ENSG00000171522",
                  "ENSG00000116288", "ENSG00000169508", "ENSG00000143365", "ENSG00000095110", "ENSG00000109787",
                  "ENSG00000179344", "ENSG00000153064", "ENSG00000108094", "ENSG00000116833", "ENSG00000151151",
                  "ENSG00000111537", "ENSG00000114859", "ENSG00000012779", "ENSG00000169220", "ENSG00000103375",
                  "ENSG00000189067", "ENSG00000108423", "ENSG00000133703", "ENSG00000138031", "ENSG00000178828",
                  "ENSG00000197114", "ENSG00000130592", "ENSG00000100368", "ENSG00000164308", "ENSG00000111424",
                  "ENSG00000108688", "ENSG00000181634", "ENSG00000164512", "ENSG00000182256", "ENSG00000113327",
                  "ENSG00000163285", "ENSG00000079263", "ENSG00000115232", "ENSG00000100311", "ENSG00000143622"]
#         target = '''ENSG00000120907
# ENSG00000170214
# ENSG00000171873
# ENSG00000150594
# ENSG00000163288
# ENSG00000102287
# ENSG00000145863
# ENSG00000166736
# ENSG00000125384
# ENSG00000112038
# ENSG00000138039
# ENSG00000109158
# ENSG00000170820
# ENSG00000268089
# ENSG00000186297
# ENSG00000112964
# ENSG00000095303
# ENSG00000117601
# ENSG00000160951
# ENSG00000073756
# ENSG00000094755
# ENSG00000011677
# ENSG00000187730
# ENSG00000166206
# ENSG00000164270
# ENSG00000228716
# ENSG00000149295
# ENSG00000180914
# ENSG00000022355
# ENSG00000050628
# ENSG00000082175
# ENSG00000091831
# ENSG00000184160
# ENSG00000145864
# ENSG00000163285
# ENSG00000274286
# ENSG00000113327
# ENSG00000182256
# ENSG00000151834
# ENSG00000111424
# ENSG00000012504
# ENSG00000153253
# ENSG00000169432
# ENSG00000171522
# ENSG00000185313
# ENSG00000136546
# ENSG00000196876
# ENSG00000168356
# ENSG00000183873
# ENSG00000144285
# ENSG00000007314
# ENSG00000136531
# ENSG00000137869
# ENSG00000169313
# ENSG00000105605
# ENSG00000075429
# ENSG00000130433
# ENSG00000142408
# ENSG00000141837
# ENSG00000100346
# ENSG00000067191
# ENSG00000108878
# ENSG00000007402
# ENSG00000081248
# ENSG00000166862
# ENSG00000102001
# ENSG00000157388
# ENSG00000165995
# ENSG00000151067
# ENSG00000153956
# ENSG00000157445
# ENSG00000006283
# ENSG00000151062
# ENSG00000196557
# ENSG00000182389
# ENSG00000167535
# ENSG00000148408
# ENSG00000075461
# ENSG00000198216
# ENSG00000006116'''.split()
        response = self._make_request('/api/latest/public/association/filter',
                                      data={'target': target, 'facets': True},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']), 2, 'association retrieved')
        self.assertTrue('facets' in json_response)
        self.assertTrue('targets_enrichment' in json_response['facets'])
        enrichment_data = json_response['facets']['targets_enrichment']['buckets']
        self.assertGreater(len(enrichment_data), 0)
        all_fine = len(enrichment_data)

        for bucket in enrichment_data:
            disease_id = bucket['key']
            disease_response = self._make_request('/api/latest/public/association/filter',
                                                  data={'disease': [disease_id], 'size': 0},
                                                  token=self._AUTO_GET_TOKEN)
            json_disease_response = json.loads(disease_response.data.decode('utf-8'))
            total = json_disease_response['total']
            print bucket['score'], bucket['bg_count'], total

            try:
                self.assertAlmostEqual(bucket['bg_count'], total, delta=int(round(total/5)),
                                       msg="Wrong background count %s: bg_count = %i, real = %i" % (disease_id,
                                                                                                    bucket['bg_count'],
                                                                                                    total))
            except AssertionError as e:
                print e
                all_fine -=1
        print len(enrichment_data) - all_fine, 'errors'
        self.assertIs(all_fine, len(enrichment_data))




if __name__ == "__main__":
     unittest.main()