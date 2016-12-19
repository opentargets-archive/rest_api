import unittest, json
from pprint import pprint

import requests
import time

from flask import url_for

from app import create_app
from tests import GenericTestCase
import grequests


class EvidenceTestCase(GenericTestCase):



    def testEvidenceByID(self):
        id = 'e1704ccbf8f2874000c5beb0ec84c2b8'
        response = self._make_request('/api/latest/public/evidence',
                                      data={'id':id},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['data'][0]['id'],id, 'evidence found')



    def testEvidenceFilterNone(self):
        response = self._make_request('/api/latest/public/evidence/filter',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')

    def testEvidenceFilterTargetGet(self):
        target = 'ENSG00000157764'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'target':target},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['target']['id'], target)

    def testEvidenceFilterTargetPost(self):
        target = 'ENSG00000157764'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({'target':[target]}),
                                      content_type='application/json',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['target']['id'], target)

    def testEvidenceFilterTargetPost2(self):
        target = 'ENSG00000157764'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({"target": ["ENSG00000157764"], "size": 1000, "datasource": ["uniprot", "eva"]}),
                                      content_type='application/json',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']), 1, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']), 10, 'minimum default returned')
        self.assertEqual(json_response['data'][0]['target']['id'], target)



    def testEvidenceFilterDiseaseGet(self):
        disease = 'EFO_0000311'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'disease':disease,
                                            'direct':True,},
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        efo_code_found = False
        for path in json_response['data'][0]['disease']['efo_info']['path']:
            if disease in path:
                efo_code_found = True
                break
        self.assertTrue(efo_code_found)

    def testEvidenceFilterDiseasePost(self):
        disease = 'EFO_0000311'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data=json.dumps({'disease':[disease],
                                                        'direct':True,
                                                        }),
                                      content_type='application/json',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
        self.assertGreaterEqual(len(json_response['data']),10, 'minimum default returned')
        efo_code_found = False
        for path in json_response['data'][0]['disease']['efo_info']['path']:
            if disease in path:
                efo_code_found = True
                break
        self.assertTrue(efo_code_found)

    # def testEvidenceFilterDirect(self):
    #     disease = 'EFO_0000311'
    #     'indirect call'
    #     response = self._make_request('/api/latest/public/evidence/filter',
    #                                   data={'disease':disease,
    #                                         'direct':False,
    #                                         'fields':['disease.efo_info.path',
    #                                                 'disease.id'
    #                                                 ],
    #                                         'size':10},
    #                                   token=self._AUTO_GET_TOKEN)
    #     self.assertTrue(response.status_code == 200)
    #     json_response = json.loads(response.data.decode('utf-8'))
    #     self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
    #     indirect_found = False
    #     for i in range(len(json_response['data'])):
    #         entry_disease_id = json_response['data'][i]['disease']['id']
    #         paths = json_response['data'][i]['disease']['efo_info']['path']
    #         all_codes = []
    #         for p in paths:
    #             all_codes.extend(p)
    #         if entry_disease_id != disease:
    #             self.assertIn(disease, all_codes,'disease in path')
    #             indirect_found = True
    #     self.assertTrue(indirect_found, 'indirect evidence found')
    #     'direct call'
    #     response = self._make_request('/api/latest/public/evidence/filter',
    #                                   data={'disease':disease,
    #                                         'direct':True,
    #                                         'fields':['disease.efo_info.path',
    #                                                 'disease.id'
    #                                                 ],
    #                                         'size':100},
    #                                   token=self._AUTO_GET_TOKEN)
    #     self.assertTrue(response.status_code == 200)
    #     json_response = json.loads(response.data.decode('utf-8'))
    #     self.assertGreaterEqual(len(json_response['data']),1, 'evidence retrieved')
    #     for i in range(len(json_response['data'])):
    #         entry_disease_id = json_response['data'][i]['disease']['id']
    #         self.assertEqual(entry_disease_id, disease, 'evidence is direct')

    def testEvidenceFilterScore(self):
        disease = 'EFO_0000311'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'disease':disease,
                                            'size': 0,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        full_json_response = json.loads(response.data.decode('utf-8'))
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'disease':disease,
                                            'scorevalue_min': 0.2,
                                            'scorevalue_max': 0.9,
                                            'size':0,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        filtered_json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreater(filtered_json_response['total'],0)
        self.assertGreater(full_json_response['total'],filtered_json_response['total'])

        target = 'ENSG00000157764'
        max_score = 0.8
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'target': target,
                                            'scorevalue_max': max_score,
                                            'size': 1,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreater(filtered_json_response['total'], 0)
        self.assertLessEqual(json_response['data'][0]['scores']['association_score'], max_score)

        target = 'ENSG00000157764'
        min_score = 1
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'target': target,
                                            'scorevalue_min': min_score,
                                            'size': 1,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertGreater(filtered_json_response['total'], 0)
        self.assertEqual(json_response['data'][0]['scores']['association_score'], min_score)

    def testEvidenceFilterSortByField(self):
        disease = 'EFO_0000311'
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'size': 10,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        default_json_response = json.loads(response.data.decode('utf-8'))
        sorted_scores = [d['scores']['association_score'] for d in default_json_response['data']]
        for i in range(len(sorted_scores) - 1):
            self.assertLessEqual(sorted_scores[i + 1],
                                    sorted_scores[i],
                                    )
        response = self._make_request('/api/latest/public/evidence/filter',
                                      data={'disease':disease,
                                            'direct':True,
                                            'sort': 'target.id',
                                            'size':1,
                                            },
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        reordered_json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(default_json_response['total'],reordered_json_response['total'])
        self.assertNotEqual(default_json_response['data'][0]['id'],
                            reordered_json_response['data'][0]['id'])



    # def testEvidenceWebAppCalls(self):
    #     web_app_calls = [
    #         # '/api/latest/public/auth/request_token?app_name=cttv-web-app&secret=2J23T20O31UyepRj7754pEA2osMOYfFK',
    #         '/api/latest/public/association/filter?target=ENSG00000101144&disease=EFO_0001444&facets=false&scorevalue_min=0',
    #         '/api/latest/private/target/ENSG00000101144',
    #         '/api/latest/private/disease/EFO_0001444',
    #         '/api/latest/public/evidence/filter?target=ENSG00000101144&disease=EFO_0001444&size=1000&datasource=gwas_catalog&fields=disease&fields=evidence&fields=variant&fields=target&fields=sourceID&fields=access_level&expandefo=true',
    #         '/api/latest/public/evidence/filter?target=ENSG00000101144&disease=EFO_0001444&size=1000&datasource=cancer_gene_census&datasource=eva_somatic&fields=disease.efo_info&fields=evidence.evidence_codes_info&fields=evidence.urls&fields=evidence.known_mutations&fields=evidence.provenance_type&fields=evidence.known_mutations&fields=access_level&fields=unique_association_fields.mutation_type&expandefo=true',
    #         '/api/latest/public/evidence/filter?target=ENSG00000101144&disease=EFO_0001444&size=1000&datasource=uniprot&datasource=eva&datasource=uniprot_literature&fields=disease.efo_info&fields=evidence&fields=variant&fields=type&fields=access_level&expandefo=true',
    #         '/api/latest/public/evidence/filter?target=ENSG00000101144&disease=EFO_0001444&size=1000&datasource=phenodigm&fields=disease&fields=evidence&fields=scores&fields=access_level&expandefo=true',
    #         '/api/latest/public/evidence/filter?target=ENSG00000101144&disease=EFO_0001444&size=1000&datasource=expression_atlas&fields=disease&fields=evidence&fields=target&fields=access_level&expandefo=true',
    #         '/api/latest/public/evidence/filter?target=ENSG00000101144&disease=EFO_0001444&size=1000&datasource=reactome&fields=target&fields=disease&fields=evidence&fields=access_level&expandefo=true',
    #         '/api/latest/public/evidence/filter?target=ENSG00000101144&disease=EFO_0001444&size=200&datasource=europepmc&expandefo=true',
    #         '/api/latest/private/disease/EFO_0001444',
    #         '/api/latest/public/evidence/filter?size=1000&datasource=chembl&fields=disease.efo_info&fields=drug&fields=evidence&fields=target&fields=access_level&target=ENSG00000101144&disease=EFO_0001444&expandefo=true']
    #
    #     for i in range(1):
    #         rs = (grequests.get('http://localhost:8008'+u) for u in web_app_calls)
    #         print grequests.map(rs)
    #
    #         # for call in web_app_calls:
    #         #     data = dict()
    #         #     params = None
    #         #     if '?' in call:
    #         #         endpoint, params = call.split('?')
    #         #     else:
    #         #         endpoint = call
    #         #     if params:
    #         #         params = params.split('&')
    #         #         for p in params:
    #         #             k,v =p.split('=')
    #         #             if k not in data:
    #         #                 data[k]=[]
    #         #             data[k].append(v)
    #         #     response = self._make_request(endpoint,
    #         #                                   data=data,
    #         #                                   token=self._AUTO_GET_TOKEN)
    #         #     self.assertEqual(response.status_code,200)



if __name__ == "__main__":
     unittest.main()