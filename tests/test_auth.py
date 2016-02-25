import unittest, json
import requests
import time

from flask import url_for

from app import create_app
from app.common.auth import AuthKey
from tests import GenericTestCase

'''
init a local redislite
inject dummy credentials
test getting a token
test token expire
test payload is retained
drop local redis
'''



class AuthTestCase(GenericTestCase):


    def testTokenGeneration(self):

        response = self._make_token_request()
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(json_response['token'].split('.')), 3, 'token is in JWT format')

    def testTokenIsValid(self):

        response= self._make_token_request(expire=1)
        self.assertTrue(response.status_code == 200)
        token = self.get_token(1)
        '''test valid token'''
        response = self._make_request('/api/latest/public/auth/validate_token',
                                      headers={'Auth-Token':token})
        self.assertTrue(response.status_code == 200,'token is validated')
        '''test tampered token'''
        response = self._make_request('/api/latest/public/auth/validate_token',
                                      headers={'Auth-Token':token+'tampered'})
        self.assertTrue(response.status_code == 401,'token is invalid')
        '''test expied token'''
        time.sleep(3)
        response = self._make_request('/api/latest/public/auth/validate_token',
                                      headers={'Auth-Token':token})
        self.assertTrue(response.status_code == 419,'token is expired')




if __name__ == "__main__":
     unittest.main()


