import unittest, json
import requests
import time

from flask import url_for

from app import create_app
from tests import GenericTestCase


class TargetTestCase(GenericTestCase):



    def testGetTarget(self):
        id = 'ENSG00000157764'#braf
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/private/target/%s'%id)
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['id'],id, 'target found')



if __name__ == "__main__":
     unittest.main()