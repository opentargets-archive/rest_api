import json
from pprint import pprint

import time

from tests import GenericTestCase


class AssociationTestCase(GenericTestCase):

    def testAssociationTargetsEnrichmentPost(self):

        '''first call'''
        start_time = time.time()
        response = self._make_request('/api/latest/private/enrichment/targets',
                                      data={'target': self.IBD_GENES,
                                            'method': 'POST',
                                            'no_cache': True
                                            },
                                      token=self._AUTO_GET_TOKEN)
        first_time = time.time()-start_time
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        # pprint(json_response)
        self.assertIn('data', json_response)

        print 'enriched diseases', json_response['total']
        '''check cache works'''
        start_time = time.time()
        response = self._make_request('/api/latest/private/enrichment/targets',
                                      data={'target': self.IBD_GENES,
                                            'method': 'POST',
                                            'no_cache': True
                                            },
                                      token=self._AUTO_GET_TOKEN)
        second_time = time.time() - start_time
        print 'times: ', first_time, second_time
        self.assertLess(second_time, first_time)

        '''check size works'''
        start_time = time.time()
        size = 100
        size_response = self._make_request('/api/latest/private/enrichment/targets',
                                      data={'target': self.IBD_GENES,
                                            'size':size,
                                            'method': 'POST',
                                            'no_cache': True
                                            },
                                      token=self._AUTO_GET_TOKEN)
        size_response_time = time.time() - start_time
        self.assertLess(size_response_time, first_time)
        json_response_size = json.loads(size_response.data.decode('utf-8'))
        self.assertEqual(len(json_response_size['data']), size)

        '''check from works'''
        start_time = time.time()
        from_ = 50
        from_response = self._make_request('/api/latest/private/enrichment/targets',
                                      data={'target': self.IBD_GENES,
                                            'from':from_,
                                            'method': 'POST',
                                            'no_cache': True
                                            },
                                      token=self._AUTO_GET_TOKEN)
        from_response_time = time.time() - start_time
        self.assertLess(from_response_time, first_time)
        json_response_from = json.loads(from_response.data.decode('utf-8'))
        self.assertEqual(json_response_from['data'][0], json_response_size['data'][from_])
        '''check sort works'''
        start_time = time.time()
        size = 100
        sort_response = self._make_request('/api/latest/private/enrichment/targets',
                                           data={'target': self.IBD_GENES,
                                                 'size': size,
                                                 'method': 'POST',
                                                 'no_cache': True,
                                                 'sort': 'enrichment.score'
                                                 },
                                           token=self._AUTO_GET_TOKEN)
        size_response_time = time.time() - start_time
        self.assertLess(size_response_time, first_time)
        json_response_sort = json.loads(sort_response.data.decode('utf-8'))
        for i in range(len(json_response_sort['data'])-1):
            self.assertLessEqual(json_response_sort['data'][i]['enrichment']['score'],
                                    json_response_sort['data'][i+1]['enrichment']['score'])

        self.assertEqual(len(json_response_size['data']), size)
        '''check lower pvalue filter works'''
        start_time = time.time()
        pvalue = 1e-20
        pvalue_response = self._make_request('/api/latest/private/enrichment/targets',
                                           data={'target': self.IBD_GENES,
                                                 'size': 10000,
                                                 'pvalue': pvalue,
                                                 'method': 'POST',
                                                 'no_cache': True
                                                 },
                                           token=self._AUTO_GET_TOKEN)
        pvalue_response_time = time.time() - start_time
        self.assertLess(pvalue_response_time, first_time)
        json_response_pvalue = json.loads(pvalue_response.data.decode('utf-8'))
        self.assertLess(json_response_pvalue['total'],json_response['total'])
        for i in json_response_pvalue['data']:
            self.assertLessEqual(i['enrichment']['score'],pvalue)
        '''check higher pvalue filter works'''
        start_time = time.time()
        pvalue = 1
        pvalue_response = self._make_request('/api/latest/private/enrichment/targets',
                                             data={'target': self.IBD_GENES,
                                                   'size': 10000,
                                                   'pvalue': pvalue,
                                                   'method': 'POST',
                                                   'no_cache': True
                                                   },
                                             token=self._AUTO_GET_TOKEN)
        pvalue_response_time = time.time() - start_time
        self.assertLess(pvalue_response_time, first_time)
        json_response_pvalue = json.loads(pvalue_response.data.decode('utf-8'))
        self.assertGreater(json_response_pvalue['total'], json_response['total'])
        for i in json_response_pvalue['data']:
            self.assertLessEqual(i['enrichment']['score'], pvalue)

    def testAssociationTargetEnrichmentGet(self):

        response = self._make_request('/api/latest/private/enrichment/targets',
                                      data={'target': self.IBD_GENES,
                                            },
                                      token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))

        self.assertIn('data', json_response)

        self.assertIsNotNone(json_response['data'])




    IBD_GENES =  ["ENSG00000073756", "ENSG00000095303", "ENSG00000280151", "ENSG00000108219", "ENSG00000198369",
                  "ENSG00000105401", "ENSG00000134882", "ENSG00000104998", "ENSG00000181915", "ENSG00000119919",
                  "ENSG00000105397", "ENSG00000178623", "ENSG00000107968", "ENSG00000133195", "ENSG00000171522",
                  "ENSG00000116288", "ENSG00000169508", "ENSG00000143365", "ENSG00000095110", "ENSG00000109787",
                  "ENSG00000179344", "ENSG00000153064", "ENSG00000108094", "ENSG00000116833", "ENSG00000151151",
                  "ENSG00000111537", "ENSG00000114859", "ENSG00000012779", "ENSG00000169220", "ENSG00000103375",
                  "ENSG00000189067", "ENSG00000108423", "ENSG00000133703", "ENSG00000138031", "ENSG00000178828",
                  "ENSG00000197114", "ENSG00000130592", "ENSG00000100368", "ENSG00000164308", "ENSG00000111424",
                  "ENSG00000108688", "ENSG00000181634", "ENSG00000164512", "ENSG00000182256", "ENSG00000113327",
                  "ENSG00000163285", "ENSG00000079263", "ENSG00000115232", "ENSG00000100311", "ENSG00000143622"]

    LUNG_CANCER_FIRST_100 = ['ENSG00000146648', 'ENSG00000157764', 'ENSG00000165731', 'ENSG00000171094', 'ENSG00000128052', 'ENSG00000141736', 'ENSG00000177084', 'ENSG00000112715', 'ENSG00000171848', 'ENSG00000176890', 'ENSG00000167325', 'ENSG00000037280', 'ENSG00000065361', 'ENSG00000258947', 'ENSG00000102755', 'ENSG00000178568', 'ENSG00000228716', 'ENSG00000101162', 'ENSG00000048392', 'ENSG00000176014', 'ENSG00000167552', 'ENSG00000137285', 'ENSG00000105976', 'ENSG00000188389', 'ENSG00000142319', 'ENSG00000196230', 'ENSG00000137267', 'ENSG00000062822', 'ENSG00000160752', 'ENSG00000167553', 'ENSG00000188229', 'ENSG00000159131', 'ENSG00000152086', 'ENSG00000104833', 'ENSG00000127824', 'ENSG00000123416', 'ENSG00000261456', 'ENSG00000101868', 'ENSG00000075886', 'ENSG00000120156', 'ENSG00000101213', 'ENSG00000134853', 'ENSG00000106123', 'ENSG00000197122', 'ENSG00000142627', 'ENSG00000073756', 'ENSG00000133216', 'ENSG00000182580', 'ENSG00000146904', 'ENSG00000044524', 'ENSG00000116106', 'ENSG00000135333', 'ENSG00000154928', 'ENSG00000196411', 'ENSG00000145242', 'ENSG00000070886', 'ENSG00000183317', 'ENSG00000080224', 'ENSG00000169083', 'ENSG00000157404', 'ENSG00000113721', 'ENSG00000141510', 'ENSG00000122025', 'ENSG00000182578', 'ENSG00000147889', 'ENSG00000118046', 'ENSG00000171862', 'ENSG00000135446', 'ENSG00000133703', 'ENSG00000105810', 'ENSG00000121879', 'ENSG00000160867', 'ENSG00000047936', 'ENSG00000110395', 'ENSG00000137776', 'ENSG00000115353', 'ENSG00000095303', 'ENSG00000117601', 'ENSG00000149311', 'ENSG00000168036', 'ENSG00000173821', 'ENSG00000127616', 'ENSG00000134250', 'ENSG00000104517', 'ENSG00000196712', 'ENSG00000085276', 'ENSG00000158715', 'ENSG00000065526', 'ENSG00000097007', 'ENSG00000068078', 'ENSG00000169032', 'ENSG00000156076', 'ENSG00000157765', 'ENSG00000126934', 'ENSG00000113263', 'ENSG00000101825', 'ENSG00000100644', 'ENSG00000143924', 'ENSG00000119866', 'ENSG00000127329']


