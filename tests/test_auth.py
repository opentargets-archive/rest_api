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

        status_code = 429
        while status_code == 429:
            response= self._get_token()
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(json_response['token'].split('.')), 3, 'token is in JWT format')

    def testTokenIsValid(self):

        status_code = 429
        while status_code == 429:
            response= self._get_token(expire=1)
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        token = json.loads(response.data.decode('utf-8'))['token']
        '''test valid token'''
        status_code = 429
        while status_code == 429:
            response2= self.client.open('/api/latest/public/auth/validate_token',
                                           headers={'Auth-Token':token})
            status_code = response2.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response2.status_code == 200,'token is validated')
        '''test tampered token'''
        status_code = 429
        while status_code == 429:
            response3= self.client.open('/api/latest/public/auth/validate_token',
                                           headers={'Auth-Token':token+'tampered'})
            status_code = response3.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response3.status_code == 401,'token is invalid')
        '''test expied token'''
        status_code = 429
        time.sleep(3)
        print self.app.debug
        while status_code == 429:
            response4 = self.client.open('/api/latest/public/auth/validate_token',
                                           headers={'Auth-Token':token})
            status_code = response4.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response4.status_code == 419,'token is expired')




if __name__ == "__main__":
     unittest.main()


