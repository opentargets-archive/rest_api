import json
import unittest

import time
import uuid

from app import create_app
from app.common.auth import AuthKey

__author__ = 'andreap'


class GenericTestCase(unittest.TestCase):
    _AUTO_GET_TOKEN='auto'

    def setUp(self):

        auth_credentials = {'domain': '',
                            'reference': 'andreap@ebi.ac.uk',
                            'app_name': 'api-test',
                            'short_window_rate': '10000',
                            'secret': 'YNVukca767p49Czt7jOt42U3R6t1FscD',
                            'users_allowed': 'true',
                            'long_window_rate': '600000'}
        self.auth_key = AuthKey(**auth_credentials)
        self.app = create_app('testing')
        self.app.extensions['redis-user'].hmset(self.auth_key.get_key(), self.auth_key.__dict__)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.host = 'http://'+self.app_context.url_adapter.get_host('')
        self.token = None
        self.update_token()


    def tearDown(self):
        self.app_context.pop()
        self.app.extensions['redis-user'].hdel(self.auth_key.get_key(), self.auth_key.__dict__.keys())
        self.app.extensions['redis-user'].delete(self.auth_key.get_key())

    def _make_token_request(self, expire = 10*60):
        return self._make_request('/api/latest/public/auth/request_token',data={'app_name':self.auth_key.app_name,
                                                                               'secret':self.auth_key.secret,
                                                                                'uid': str(uuid.uuid4()),
                                                                                'password': 'test',
                                                                               'expiry': expire},
                                  headers =dict(Authorization="Basic Y3R0djpkajhtaXhpamswNGpwZGc="))

    def get_token(self, expire = 10*60):
        return json.loads(self._make_token_request(expire).data.decode('utf-8'))['token']

    def _make_request(self,
                      path,
                      data = {},
                      method = "GET",
                      token = None,
                      headers = None,
                      rate_limit_fail = False,
                      **kwargs):
        params = dict(method = method)
        params['data'] = data
        # params['data']['nocache']=True
        if headers is not None:
            params['headers'] = headers
        if token is not None:
            if token == self._AUTO_GET_TOKEN:
                self.update_token()
                token = self.token
            if 'headers' not in params:
                params['headers']={}
            params['headers']['Auth-Token']=token
        params.update(**kwargs)

        if not rate_limit_fail:
            status_code = 429
            while status_code == 429:
                response = self.client.open(path,**params)
                status_code = response.status_code
                print status_code
                if status_code == 429:
                    time.sleep(10)
        else:
            response = self.client.open(path,**params)
        return response

    def update_token(self):
        if self.token:
            token_valid_response = self._make_request('/api/latest/public/auth/validate_token',
                                                       headers={'Auth-Token':self.token})
            if token_valid_response.status == 200:
                return
            if token_valid_response.status == 419:
                pass
        self.token = self.get_token()
