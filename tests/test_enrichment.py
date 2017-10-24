import json
import time
from tests import GenericTestCase

import pytest
from config import Config
from tests.target_lists import IBD_GENES

pytestmark = pytest.mark.skipif(
    not Config.ELASTICSEARCH_URL,
    reason="needs ES, pass url as ENV var: ELASTICSEARCH_URL"
)

class AssociationTestCase(GenericTestCase):

    def testAssociationTargetsEnrichmentPost(self):

        '''first call'''
        start_time = time.time()
        response = self._make_request('/platform/private/enrichment/targets',
                                      data={'target': self.IBD_GENES,
                                            'method': 'POST',
                                            'no_cache': True
                                            },
                                      token=self._AUTO_GET_TOKEN)
        first_time = time.time()-start_time
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        # pprint(json_response)
        last_score = 1
        for target in json_response['data'][0]['targets']:
            self.assertGreaterEqual(last_score, target['association_score']['overall'])
            last_score = target['association_score']['overall']
        self.assertIn('data', json_response)

        print 'enriched diseases', json_response['total']
        '''check cache works'''
        start_time = time.time()
        response = self._make_request('/platform/private/enrichment/targets',
                                      data={'target': IBD_GENES,
                                            'method': 'POST',
                                            'no_cache': True
                                            },
                                      token=self._AUTO_GET_TOKEN)
        second_time = time.time() - start_time
        print 'times: ', first_time, second_time
        self.assertLess(second_time, first_time)

        '''check size works'''
        size = 100
        size_response = self._make_request('/platform/private/enrichment/targets',
                                      data={'target': IBD_GENES,
                                            'size':size,
                                            'method': 'POST',
                                            'no_cache': True
                                            },
                                      token=self._AUTO_GET_TOKEN)
        json_response_size = json.loads(size_response.data.decode('utf-8'))
        self.assertEqual(len(json_response_size['data']), size)

        '''check from works'''
        from_ = 50
        from_response = self._make_request('/platform/private/enrichment/targets',
                                      data={'target': IBD_GENES,
                                            'from':from_,
                                            'method': 'POST',
                                            'no_cache': True
                                            },
                                      token=self._AUTO_GET_TOKEN)
        json_response_from = json.loads(from_response.data.decode('utf-8'))
        self.assertEqual(json_response_from['data'][0], json_response_size['data'][from_])
        '''check sort works'''
        size = 100
        sort_response = self._make_request('/platform/private/enrichment/targets',
                                           data={'target': IBD_GENES,
                                                 'size': size,
                                                 'method': 'POST',
                                                 'no_cache': True,
                                                 'sort': 'enrichment.score'
                                                 },
                                           token=self._AUTO_GET_TOKEN)
        json_response_sort = json.loads(sort_response.data.decode('utf-8'))
        for i in range(len(json_response_sort['data'])-1):
            self.assertLessEqual(json_response_sort['data'][i]['enrichment']['score'],
                                    json_response_sort['data'][i+1]['enrichment']['score'])

        self.assertEqual(len(json_response_size['data']), size)
        '''check lower pvalue filter works'''
        pvalue = 1e-20
        pvalue_response = self._make_request('/platform/private/enrichment/targets',
                                           data={'target': IBD_GENES,
                                                 'size': 10000,
                                                 'pvalue': pvalue,
                                                 'method': 'POST',
                                                 'no_cache': True
                                                 },
                                           token=self._AUTO_GET_TOKEN)
        json_response_pvalue = json.loads(pvalue_response.data.decode('utf-8'))
        self.assertLess(json_response_pvalue['total'],json_response['total'])
        for i in json_response_pvalue['data']:
            self.assertLessEqual(i['enrichment']['score'],pvalue)
        '''check higher pvalue filter works'''
        pvalue = 1
        pvalue_response = self._make_request('/platform/private/enrichment/targets',
                                             data={'target': IBD_GENES,
                                                   'size': 10000,
                                                   'pvalue': pvalue,
                                                   'method': 'POST',
                                                   'no_cache': True
                                                   },
                                             token=self._AUTO_GET_TOKEN)
        json_response_pvalue = json.loads(pvalue_response.data.decode('utf-8'))
        self.assertGreater(json_response_pvalue['total'], json_response['total'])
        for i in json_response_pvalue['data']:
            self.assertLessEqual(i['enrichment']['score'], pvalue)

    def testAssociationTargetEnrichmentGet(self):

        response = self._make_request('/platform/private/enrichment/targets',
                                      data={'target': IBD_GENES,
                                            },
                                      token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))

        self.assertIn('data', json_response)

        self.assertIsNotNone(json_response['data'])




