import unittest, json
import requests
import time

from flask import url_for

from app import create_app
from tests import GenericTestCase


class StatsTestCase(GenericTestCase):


    def testStats(self):
        response= self._make_request('/api/latest/public/utils/stats',
                                   token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreater(json_response['evidencestrings']['total'],0, 'evidence stats found')
        self.assertGreater(json_response['associations']['total'],0, 'assocaiations stats found')
        self.assertGreater(json_response['targets']['total'],0, 'targets stats found')
        self.assertGreater(json_response['diseases']['total'],0, 'diseases stats found')



if __name__ == "__main__":
     unittest.main()