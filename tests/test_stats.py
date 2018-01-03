import unittest, json
from tests import GenericTestCase

import pytest
from config import Config
pytestmark = pytest.mark.skipif(
    not Config.ELASTICSEARCH_URL,
    reason="needs ES, pass url as ENV var: ELASTICSEARCH_URL"
)

class StatsTestCase(GenericTestCase):


    def testStats(self):
        response= self._make_request('/platform/public/utils/stats',
                                   token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreater(json_response['evidencestrings']['total'],0, 'evidence stats found')
        self.assertGreater(json_response['associations']['total'],0, 'assocaiations stats found')
        self.assertGreater(json_response['targets']['total'],0, 'targets stats found')
        self.assertGreater(json_response['diseases']['total'],0, 'diseases stats found')



if __name__ == "__main__":
     unittest.main()