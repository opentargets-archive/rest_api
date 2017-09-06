#TODO
'''
init a local redislite
inject dummy credentials woith a row rate_limit
test maiking requests and increment headers
test exceeding the limit

drop local redis
'''
import json

from tests import GenericTestCase


class RateLimitTestCase(GenericTestCase):


    def testRateLimitHit(self):

        status_code = 200
        req_count = 0
        token = self.get_token()
        while status_code == 200:
            req_count+=1
            response= self._make_request('/api/latest/public/utils/ping',
                                         rate_limit_fail=True,
                                         token = token)
            status_code = response.status_code
            #check custom headers are present in both 200 and 429 responsese
            self.assertIn('Access-Control-Allow-Origin', response['headers'])
            if status_code == 429:
                break

        self.assertTrue(response.status_code == 429)
        # self.assertEqual(len(json_response['token'].split('.')), 3, 'token is in JWT format')
