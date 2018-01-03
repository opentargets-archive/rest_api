import ujson as json
import unittest
from tests import GenericTestCase
import pytest
from config import Config
pytestmark = pytest.mark.skipif(
    not Config.ELASTICSEARCH_URL,
    reason="needs ES, pass url as ENV var: ELASTICSEARCH_URL"
)

class RelationTestCase(GenericTestCase):

    def testRelationGet(self):
        target = 'ENSG00000157764'
        response = self._make_request('/platform/private/relation',
                                      data={'subject': target,
                                            'size': 1},
                                      token=self._AUTO_GET_TOKEN)
        print response.data
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(json_response['data']),1, 'relation retrieved')
        self.assertEqual(json_response['data'][0]['subject']['id'], target)


    def testRelationTargetGet(self):
        target = 'ENSG00000157764'
        response = self._make_request('/platform/private/relation/target/'+target,
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'relation retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['subject']['id'], target)

    def testRelationDiseaseGet(self):
        disease = 'EFO_0000311'
        response = self._make_request('/platform/private/relation/disease/' + disease,
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']), 1, 'relation retrieved')
        self.assertGreaterEqual(len(json_response['data']), 10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['subject']['id'], disease)

    def testPostEFOwithRelations(self):

        disease = 'EFO_0001365'
        related_diseases_res = self._make_request('/platform/private/relation/disease/' + disease,
                                                  data={'size':1000},
                                                  token=self._AUTO_GET_TOKEN)
        json_response = json.loads(related_diseases_res.data.decode('utf-8'))
        related_diseases = [ d['object']['id'] for d in json_response['data']]
        # print 'Related Diseases {}'.format(related_diseases)
        fields = ['label','code']
        response = self._make_request('/platform/private/disease',
                                        data = json.dumps({'diseases': related_diseases,
                                                           'facets': 'true',
                                                           'fields':fields,
                                                           'size':0}),
                                        content_type = 'application/json',
                                        method = 'POST',
                                        token = self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        sig_labels =[bucket['key'] for bucket in json_response['facets']['significant_therapeutic_areas']['buckets']]
        # print 'Groups of related diseases {}'.format(sig_labels)
        # print 'Related Diseases with labels {}'.format(json_response['data'])
        self.assertEqual(len(json_response['data']), 0)
        self.assertGreater(len(sig_labels), 0)
        self.assertIn('neoplasm', sig_labels)




    def testPostRelationandTargetFetching(self):
        target = 'ENSG00000142192'
        related_targets_res = self._make_request('/platform/private/relation/target/' + target,
                                                  data={'size': 1000},
                                                  token=self._AUTO_GET_TOKEN)
        json_response = json.loads(related_targets_res.data.decode('utf-8'))
        related_targets = [d['object']['id'] for d in json_response['data']]
        fields = ['id', 'approved_name', 'approved_symbol']
        response = self._make_request('/platform/private/target',
                                      data=json.dumps(
                                          {'id': related_targets, 'facets': 'true', 'fields':fields,'size':0}),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        sig_terms = [bucket['key'] for bucket in json_response['facets']['significant_go_terms']['buckets']]
        self.assertEqual(len(json_response['data']), 0)
        self.assertGreater(len(sig_terms), 0)

    def testPostRelationTargetsWithFacetFiltering(self):
        target = 'ENSG00000157764'
        related_targets_res = self._make_request('/platform/private/relation/target/' + target,
                                                  data={'size': 1000},
                                                  token=self._AUTO_GET_TOKEN)
        json_response = json.loads(related_targets_res.data.decode('utf-8'))
        related_targets = [d['object']['id'] for d in json_response['data']]
        fields = ['id','approved_name','approved_symbol']
        response = self._make_request('/platform/private/target',
                                      data=json.dumps(
                                          {'id': related_targets, 'facets': 'true', 'fields':fields,'go_term':'GO:0008284'}),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        sig_terms = [bucket['key'] for bucket in json_response['facets']['significant_go_terms']['buckets']]
        self.assertGreater(len(json_response['data']), 0)
        self.assertGreater(len(sig_terms), 0)



if __name__ == "__main__":
    unittest.main()
