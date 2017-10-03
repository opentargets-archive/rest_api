import unittest, json
import requests
import time

from flask import url_for

from app import create_app
from tests import GenericTestCase

import pytest
pytestmark = pytest.mark.skipif(
    not pytest.config.getoption("--es"),
    reason="needs ES; use --es option to run"
)

class EFOTestCase(GenericTestCase):


    def testGetEFO(self):
        ids = ['EFO_0000311',#cancer
               'EFO_0000270', #asthma
               'EFO_0004591',#child onset asthma
               ]
        for id in ids:
            response = self._make_request('/api/latest/private/disease/%s'%id, token=self._AUTO_GET_TOKEN)
            self.assertTrue(response.status_code == 200)
            json_response = json.loads(response.data.decode('utf-8'))
            for path in json_response['path_codes']:
                self.assertEqual(path[-1],id, 'disease found')


    def testPostEFO(self):

        disease = 'EFO_0001365'
        related_diseases_res = self._make_request('/api/latest/private/relation/disease/' + disease,
                                                  data={'size':1000},
                                                  token=self._AUTO_GET_TOKEN)
        json_response = json.loads(related_diseases_res.data.decode('utf-8'))
        related_diseases = [ d['object']['id'] for d in json_response['data']]
        print 'Related Diseases {}'.format(related_diseases)
        fields = ['label','code']
        response = self._make_request('/api/latest/private/disease',
                                        data = json.dumps({'diseases': related_diseases,'facets': 'true','fields':fields}),
                                        content_type = 'application/json',
                                        method = 'POST',
                                        token = self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        sig_labels =[bucket['key'] for bucket in json_response['facets']['significantTherapeuticAreas']['buckets']]
        print 'Groups of related diseases {}'.format(sig_labels)
        print 'Related Diseases with labels {}'.format(json_response['data'])

        print json_response


    def testPostEFOWithLabelFiltering(self):

        disease = 'EFO_0000311'
        related_diseases_res = self._make_request('/api/latest/private/relation/disease/' + disease,
                                                  data={'size': 1000},
                                                  token=self._AUTO_GET_TOKEN)
        json_response = json.loads(related_diseases_res.data.decode('utf-8'))
        related_diseases = [d['object']['id'] for d in json_response['data']]
        fields = ['label', 'code']
        response = self._make_request('/api/latest/private/disease',
                                      data=json.dumps({'diseases': related_diseases, 'facets': 'true', 'path_label':'epithelial',
                                                       'fields':fields}),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        sig_labels = [bucket['key'] for bucket in json_response['facets']['significantTherapeuticAreas']['buckets']]
        print 'Groups of related diseases {}'.format(sig_labels)
        print 'Related Diseases  - after selecting specific path_label {}'.format(json_response['data'])


if __name__ == "__main__":
     unittest.main()