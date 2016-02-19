import unittest, json
import requests
import time

from flask import url_for

from app import create_app


class FreeTextSearchTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.host = 'http://'+self.app_context.url_adapter.get_host('')


    def tearDown(self):
        self.app_context.pop()

    def _assert_search_result(self,
                            json_response,
                            name = None,
                            full_name = None,
                            description = None,
                            min_association_number =0):
        self.assertTrue(json_response['data'])
        first_result = json_response['data'][0]['data']
        self.assertEqual(first_result['name'], name)
        if full_name is not None:
            self.assertEqual(first_result['full_name'], full_name)
        if description is not None:
            self.assertEqual(first_result['description'], description)
        self.assertGreaterEqual(first_result['association_counts']['total'], min_association_number)

    def testBraf(self):
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/search', data={'q':'braf'})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self._assert_search_result(json_response,
                                   'BRAF',
                                   'B-Raf proto-oncogene, serine/threonine kinase',
                                   'Protein kinase involved in the transduction of mitogenic signals from the cell membrane to the nucleus. May play a role in the postsynaptic responses of hippocampal neuron. Phosphorylates MAP2K1, and thereby contributes to the MAP kinase signal transduction pathway.',
                                   680)


    def testAsthma(self):
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/public/search', data={'q':'asthma'})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self._assert_search_result(json_response,
                                   'asthma',
                                   'asthma',
                                   "A bronchial disease that is characterized by chronic inflammation and narrowing of the airways, which is caused by a combination of environmental and genetic factors resulting in recurring periods of wheezing (a whistling sound while breathing), chest tightness, shortness of breath, mucus production and coughing. The symptoms appear due to a variety of triggers such as allergens, irritants, respiratory infections, weather changes, excercise, stress, reflux disease, medications, foods and emotional anxiety.",
                                   2086)


    def _assert_quicksearch_result(self,
                            json_response,
                            name = None,
                            full_name = None,
                            description = None,
                            min_association_number =0):
        self.assertTrue(json_response['data'])
        first_result = json_response['data']['besthit']['data']
        self.assertEqual(first_result['name'], name)
        if full_name is not None:
            self.assertEqual(first_result['full_name'], full_name)
        if description is not None:
            self.assertEqual(first_result['description'], description)
        self.assertGreaterEqual(first_result['association_counts']['total'], min_association_number)

    def testQuickSearchBraf(self):
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/private/quicksearch', data={'q':'braf'})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self._assert_quicksearch_result(json_response,
                                   'BRAF',
                                   'B-Raf proto-oncogene, serine/threonine kinase',
                                   'Protein kinase involved in the transduction of mitogenic signals from the cell membrane to the nucleus. May play a role in the postsynaptic responses of hippocampal neuron. Phosphorylates MAP2K1, and thereby contributes to the MAP kinase signal transduction pathway.',
                                   680)


    def testQuickSearchAsthma(self):
        status_code = 429
        while status_code == 429:
            response= self.client.open('/api/latest/private/quicksearch', data={'q':'asthma'})
            status_code = response.status_code
            if status_code == 429:
                time.sleep(10)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self._assert_quicksearch_result(json_response,
                                   'asthma',
                                   'asthma',
                                   "A bronchial disease that is characterized by chronic inflammation and narrowing of the airways, which is caused by a combination of environmental and genetic factors resulting in recurring periods of wheezing (a whistling sound while breathing), chest tightness, shortness of breath, mucus production and coughing. The symptoms appear due to a variety of triggers such as allergens, irritants, respiratory infections, weather changes, excercise, stress, reflux disease, medications, foods and emotional anxiety.",
                                   2086)








if __name__ == "__main__":
     unittest.main()