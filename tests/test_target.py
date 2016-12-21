import unittest, json
import requests
import time

from flask import url_for

from app import create_app
from tests import GenericTestCase


class TargetTestCase(GenericTestCase):



    def testGetTarget(self):
        id = 'ENSG00000157764'#braf
        response= self._make_request('/api/latest/private/target/%s'%id,
                                     data={'no_cache': 'True'},
                                   token=self._AUTO_GET_TOKEN,
                                     )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['id'], id, 'target found')


    def testGetMultipleTargets(self):
        ids = ['ENSG00000157764', 'ENSG00000162594', 'ENSG00000167207']
        response = self._make_request('/api/latest/private/target',
                                      data={'no-cache': 'True',
                                            'id':ids},
                                      token=self._AUTO_GET_TOKEN,
                                      )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(len(json_response['data']) == 3)

        # get the targets
        ids_in_resp = [rec['ensembl_gene_id'] for rec in json_response['data']]
        self.assertTrue(set(ids) == set(ids_in_resp))


    def testGetFieldsFromTargets(self):
        ids = ['ENSG00000157764', 'ENSG00000162594', 'ENSG00000167207']
        fields = ['ensembl_gene_id', 'pubmed_ids', 'go']
        response = self._make_request('/api/latest/private/target',
                                      data={'no-cache': 'True',
                                            'fields': fields,
                                            'id': ids},
                                      token=self._AUTO_GET_TOKEN,
                                      )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(len(json_response['data']) == 3)

        def assert_field (rec):
            self.assertTrue('go' in rec)
            self.assertTrue('ensembl_gene_id' in rec)
            self.assertTrue('pubmed_ids' in rec)

        map(assert_field, json_response['data'])

        def assert_number_of_fields (rec):
            self.assertTrue(len(rec) == 3)

        map(assert_number_of_fields, json_response['data'])

if __name__ == "__main__":
     unittest.main()