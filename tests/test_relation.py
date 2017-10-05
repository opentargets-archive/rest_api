import ujson as json
import unittest
from pprint import pprint

from app import create_app
from app.common.request_templates import FilterTypes
from tests import GenericTestCase


import pytest
pytestmark = pytest.mark.skipif(
    not pytest.config.getoption("--es"),
    reason="needs ES; use --es option to run"
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


if __name__ == "__main__":
    unittest.main()
