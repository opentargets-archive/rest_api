import json
import logging
import unittest

import time
import uuid

from app import create_app
from envparse import env
import flask_restful as restful

__author__ = 'andreap'


class GenericTestCase(unittest.TestCase):
    _AUTO_GET_TOKEN='auto'
    env.read_envfile('VERSION')
    API_VERSION = env.str('API_VERSION')

    @classmethod
    def setUpClass(cls):
        auth_credentials = {'domain': '',
                            'reference': 'andreap@ebi.ac.uk',
                            'app_name': 'api-test',
                            'short_window_rate': '10000',
                            'secret': 'YNVukca767p49Czt7jOt42U3R6t1FscD',
                            'users_allowed': 'true',
                            'long_window_rate': '6000000'}
        cls.app = create_app('testing')
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        cls.client = cls.app.test_client()
        cls.host = 'http://' + cls.app_context.url_adapter.get_host('')

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def setUp(self):
        self.token = None
        self.update_token()

    def _make_token_request(self, expire = 10*60):
        return self._make_request('/platform/public/auth/request_token',data={'uid': str(uuid.uuid4()),
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
                      rate_limit_fail = True,
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
        return self.client.open('/v' + self.API_VERSION + path,**params)

    def update_token(self):
        if self.token:
            token_valid_response = self._make_request('/platform/public/auth/validate_token',
                                                       headers={'Auth-Token':self.token})
            if token_valid_response.status_code == 200:
                return
            if token_valid_response.status_code == 419:
                pass
        self.token = self.get_token()
