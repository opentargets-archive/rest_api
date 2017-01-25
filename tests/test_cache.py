import decimal
import unittest
import ujson as json
import requests
import time

from flask import url_for

from app import create_app
from config import Config
from tests import GenericTestCase


class InternalCacheTestCase(GenericTestCase):



    def testAssociationCacheWorks(self):
        start_time = time.time()
        response = self._make_request('/api/latest/public/search',
                                      data={'q':'neoplasm',
                                            'size': 100},
                                      token=self._AUTO_GET_TOKEN)
        first_time = time.time() - start_time
        self.assertTrue(response.status_code == 200)
        start_time = time.time()
        response = self._make_request('/api/latest/public/search',
                                      data={'q':'neoplasm',
                                            'size': 100},
                                      token=self._AUTO_GET_TOKEN)
        second_time = time.time() - start_time
        self.assertTrue(response.status_code == 200)
        self.assertGreater(first_time, second_time)
        print 'cache speedup: %1.2f times'%(first_time/second_time)
        start_time = time.time()
        response = self._make_request('/api/latest/public/search',
                                      data={'q': 'neoplasm',
                                            'size': 100,
                                            Config.NO_CACHE_PARAMS:True},
                                      token=self._AUTO_GET_TOKEN)
        third_time = time.time() - start_time
        self.assertTrue(response.status_code == 200)
        self.assertGreater(third_time, second_time)




if __name__ == "__main__":
     unittest.main()