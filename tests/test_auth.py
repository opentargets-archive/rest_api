import unittest, json
import requests
import time

from flask import url_for

from app import create_app, AuthKey

#TODO

'''
init a local redislite
inject dummy credentials
test getting a token
test token expire
test payload is retained
drop local redis
'''



class AuthTestCase(unittest.TestCase):

    def setUp(self):

        auth_credentials = {'domain': '',
                            'reference': 'andreap@ebi.ac.uk',
                            'app_name': 'api-test',
                            'short_window_rate': '100',
                            'secret': 'YNVukca767p49Czt7jOt42U3R6t1FscD',
                            'users_allowed': 'true',
                            'long_window_rate': '600'}
        self.auth_key = AuthKey(**auth_credentials)
        self.app = create_app('testing')
        self.app.extensions['redis-user'].hmset(self.auth_key.get_key(), self.auth_key.__dict__)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.host = 'http://'+self.app_context.url_adapter.get_host('')


    def tearDown(self):
        self.app_context.pop()
        self.app.extensions['redis-user'].hdel(self.auth_key.get_key(), self.auth_key.__dict__.keys())
        self.app.extensions['redis-user'].delete(self.auth_key.get_key())

    def _get_token(self, expire = 120):
        return self.client.open('/api/latest/public/auth/request_token', data={'app_name':self.auth_key.app_name,
                                                                               'secret':self.auth_key.secret,
                                                                               'expiry': expire})


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
        while status_code == 429:
            response4 = self.client.open('/api/latest/public/auth/validate_token',
                                           headers={'Auth-Token':token})
            status_code = response4.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response4.status_code == 419,'token is expired')




if __name__ == "__main__":
     unittest.main()


