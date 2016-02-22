import unittest, json
import requests
import time

from flask import url_for

from app import create_app


class StatsTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.host = 'http://'+self.app_context.url_adapter.get_host('')


    def tearDown(self):
        self.app_context.pop()


    def testStats(self):
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/utils/stats')
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreater(json_response['evidencestrings']['total'],0, 'evidence stats found')
        self.assertGreater(json_response['associations']['total'],0, 'assocaiations stats found')
        self.assertGreater(json_response['targets']['total'],0, 'targets stats found')
        self.assertGreater(json_response['diseases']['total'],0, 'diseases stats found')



if __name__ == "__main__":
     unittest.main()