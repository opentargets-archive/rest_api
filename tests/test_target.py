import unittest, json
import requests
import time

from flask import url_for

from app import create_app
from tests import GenericTestCase


class TargetTestCase(GenericTestCase):



    def testGetTarget(self):
        id = 'ENSG00000157764'#braf
        response= self._make_request('/api/latest/private/target/%s'%id,
                                   token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['id'],id, 'target found')



if __name__ == "__main__":
     unittest.main()