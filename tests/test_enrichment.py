import json
from pprint import pprint

import time

from tests import GenericTestCase


class AssociationTestCase(GenericTestCase):

    def testAssociationTargetsEnrichmentNone(self):
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
        start_time = time.time()
        response = self._make_request('/api/latest/private/enrichment/targets',
                                      data={'target': target,
                                            'method': 'POST',
                                            'no_cache': True
                                            },
                                      token=self._AUTO_GET_TOKEN)
        print 'time: ', time.time()-start_time
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        pprint(json_response)
        self.assertIn('data', json_response)
        self.assertTrue(len(json_response['data']) == 0)


    def testAssociationTargetEnrichmentGet(self):
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
        response = self._make_request('/api/latest/private/enrichment/targets',
                                      data={'target': target,
                                            'targets_enrichment': "simple",
                                            'no_cache': True
                                            },
                                      token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))

        self.assertIn('data', json_response)

        self.assertIsNotNone(json_response['data'])

        min_score = 0
        for disease in json_response['data']:
            self.assertIsNotNone(disease['score'])
            score = disease['score']
            self.assertGreaterEqual(score, min_score)
            min_score = score
            self.assertIsNotNone(disease['counts'])
            self.assertIsNotNone(disease['label'])