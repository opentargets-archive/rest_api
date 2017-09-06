import unittest, json
import requests
import time

from flask import url_for

from app import create_app
from tests import GenericTestCase

import pytest
pytestmark = pytest.mark.skipif(
    not pytest.config.getoption("--es"),
    reason="needs ES; use --es option to run"
)

class EFOTestCase(GenericTestCase):


    def testGetEFO(self):
        ids = ['EFO_0000311',#cancer
               'EFO_0000270', #asthma
               'EFO_0004591',#child onset asthma
               ]
        for id in ids:
            response = self._make_request('/v'+str(api_version)+'/platform/private/disease/%s'%id, token=self._AUTO_GET_TOKEN)
            self.assertTrue(response.status_code == 200)
            json_response = json.loads(response.data.decode('utf-8'))
            for path in json_response['path_codes']:
                self.assertEqual(path[-1],id, 'disease found')



if __name__ == "__main__":
     unittest.main()