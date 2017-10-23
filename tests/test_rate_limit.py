#TODO
'''
init a local redislite
inject dummy credentials woith a row rate_limit
test maiking requests and increment headers
test exceeding the limit

drop local redis
'''

from tests import GenericTestCase


class RateLimitTestCase(GenericTestCase):


    def testRateLimitHit(self):

        status_code = 200
        req_count = 0
        token = self.get_token()
        while status_code == 200:
            req_count+=1
            response= self._make_request('/platform/public/utils/ping',
                                         rate_limit_fail=True,
                                         token = token)
            status_code = response.status_code
            if status_code == 429:
                # check custom headers are present in error
                self.assertIn('Access-Control-Allow-Origin', response.headers)
                break
            elif status_code == 200:
                # check custom headers are present in correct responses
                self.assertIn('Access-Control-Allow-Origin', response.headers)

        self.assertTrue(response.status_code == 429)
        # self.assertEqual(len(json_response['token'].split('.')), 3, 'token is in JWT format')
