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

    def testPostTargets(self):
        targets = ['ENSG00000133703','ENSG00000121879','ENSG00000128052','ENSG00000146648','ENSG00000165731','ENSG00000213281','ENSG00000174775','ENSG00000141510','ENSG00000171862','ENSG00000102755','ENSG00000171094','ENSG00000039068','ENSG00000134853','ENSG00000037280','ENSG00000109670','ENSG00000113721','ENSG00000169032','ENSG00000148400','ENSG00000122025','ENSG00000157404','ENSG00000141736','ENSG00000164362','ENSG00000139687','ENSG00000168036','ENSG00000117713','ENSG00000168610','ENSG00000149311','ENSG00000142208','ENSG00000198793','ENSG00000096384','ENSG00000106462','ENSG00000120217','ENSG00000097007','ENSG00000095002','ENSG00000100644','ENSG00000116062','ENSG00000196712','ENSG00000136997','ENSG00000147889','ENSG00000181555','ENSG00000064012','ENSG00000138413','ENSG00000139618','ENSG00000178568','ENSG00000177084','ENSG00000171848','ENSG00000065361','ENSG00000137267','ENSG00000176014','ENSG00000066468','ENSG00000167325','ENSG00000197122','ENSG00000055609','ENSG00000135679','ENSG00000184937','ENSG00000119772','ENSG00000131747','ENSG00000127824','ENSG00000188229','ENSG00000167552','ENSG00000104833','ENSG00000121966','ENSG00000141646','ENSG00000127616','ENSG00000075886','ENSG00000167553','ENSG00000081237','ENSG00000077782','ENSG00000261456','ENSG00000160867','ENSG00000196230','ENSG00000068078','ENSG00000145675','ENSG00000152086','ENSG00000012048','ENSG00000123416','ENSG00000258947','ENSG00000182866','ENSG00000176890','ENSG00000179295','ENSG00000005339','ENSG00000133216','ENSG00000134250','ENSG00000132155','ENSG00000163599','ENSG00000101162','ENSG00000198400','ENSG00000183765','ENSG00000163513','ENSG00000116016','ENSG00000062822','ENSG00000132646','ENSG00000076242','ENSG00000137285','ENSG00000118046','ENSG00000105810','ENSG00000048392','ENSG00000162434','ENSG00000112715','ENSG00000167548','ENSG00000198900','ENSG00000082898','ENSG00000085224','ENSG00000183337','ENSG00000110092','ENSG00000101868','ENSG00000171720','ENSG00000083857','ENSG00000168702','ENSG00000182054','ENSG00000096968','ENSG00000134982','ENSG00000141027','ENSG00000114861','ENSG00000134086','ENSG00000100393','ENSG00000147050','ENSG00000119535','ENSG00000088832','ENSG00000123473','ENSG00000079432','ENSG00000026508','ENSG00000143799','ENSG00000116478','ENSG00000169083','ENSG00000136826','ENSG00000104365','ENSG00000166710','ENSG00000197299','ENSG00000105976','ENSG00000115414','ENSG00000182578','ENSG00000131759','ENSG00000156970','ENSG00000118058','ENSG00000103197','ENSG00000186575','ENSG00000092820','ENSG00000087245','ENSG00000126934','ENSG00000101972','ENSG00000140464','ENSG00000188389','ENSG00000135446','ENSG00000087460','ENSG00000049618','ENSG00000186716','ENSG00000196591','ENSG00000047936','ENSG00000124762','ENSG00000094631','ENSG00000169429','ENSG00000168769','ENSG00000087586','ENSG00000228716','ENSG00000100697','ENSG00000185499','ENSG00000107562','ENSG00000175387','ENSG00000120156','ENSG00000099956','ENSG00000162733','ENSG00000142627','ENSG00000189079','ENSG00000026025','ENSG00000107485','ENSG00000140538','ENSG00000140836','ENSG00000150907','ENSG00000185920','ENSG00000163930','ENSG00000113916','ENSG00000104884','ENSG00000240065','ENSG00000159216','ENSG00000157168','ENSG00000073282','ENSG00000091831','ENSG00000133895','ENSG00000139083','ENSG00000140443','ENSG00000083799','ENSG00000019991','ENSG00000165025','ENSG00000132170','ENSG00000171791','ENSG00000179218','ENSG00000116044','ENSG00000131981','ENSG00000122861','ENSG00000101115','ENSG00000166851','ENSG00000105329','ENSG00000163939','ENSG00000181449','ENSG00000184634','ENSG00000010671','ENSG00000105974','ENSG00000105639','ENSG00000137673','ENSG00000122512','ENSG00000044524','ENSG00000169398','ENSG00000166888','ENSG00000166949','ENSG00000181163','ENSG00000073756','ENSG00000133392','ENSG00000169604','ENSG00000111276','ENSG00000100985','ENSG00000165699','ENSG00000125618','ENSG00000102265','ENSG00000204264','ENSG00000109471','ENSG00000051382','ENSG00000111424','ENSG00000118785','ENSG00000102882','ENSG00000171456','ENSG00000085563','ENSG00000138685','ENSG00000104419','ENSG00000165671','ENSG00000104320','ENSG00000149948','ENSG00000105221','ENSG00000135100','ENSG00000118503','ENSG00000130816','ENSG00000075618','ENSG00000178691','ENSG00000182944','ENSG00000196159','ENSG00000147257','ENSG00000146674','ENSG00000105568','ENSG00000057657','ENSG00000105388','ENSG00000134371','ENSG00000136244','ENSG00000272398','ENSG00000100292','ENSG00000165556','ENSG00000174059','ENSG00000144476','ENSG00000175595','ENSG00000085276']
        fields = ['id', 'approved_name', 'approved_symbol']
        response = self._make_request('/api/latest/private/target',
                                      data=json.dumps(
                                          {'id': targets, 'facets': 'true', 'fields':fields}),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        print json_response

    def testPostTargetsWithFacetFiltering(self):
        targets = ['ENSG00000133703', 'ENSG00000121879', 'ENSG00000128052', 'ENSG00000146648', 'ENSG00000165731',
                   'ENSG00000213281', 'ENSG00000174775', 'ENSG00000141510', 'ENSG00000171862', 'ENSG00000102755',
                   'ENSG00000171094', 'ENSG00000039068', 'ENSG00000134853', 'ENSG00000037280', 'ENSG00000109670',
                   'ENSG00000113721', 'ENSG00000169032', 'ENSG00000148400', 'ENSG00000122025', 'ENSG00000157404',
                   'ENSG00000141736', 'ENSG00000164362', 'ENSG00000139687', 'ENSG00000168036', 'ENSG00000117713',
                   'ENSG00000168610', 'ENSG00000149311', 'ENSG00000142208', 'ENSG00000198793', 'ENSG00000096384',
                   'ENSG00000106462', 'ENSG00000120217', 'ENSG00000097007', 'ENSG00000095002', 'ENSG00000100644',
                   'ENSG00000116062', 'ENSG00000196712', 'ENSG00000136997', 'ENSG00000147889', 'ENSG00000181555',
                   'ENSG00000064012', 'ENSG00000138413', 'ENSG00000139618', 'ENSG00000178568', 'ENSG00000177084',
                   'ENSG00000171848', 'ENSG00000065361', 'ENSG00000137267', 'ENSG00000176014', 'ENSG00000066468',
                   'ENSG00000167325', 'ENSG00000197122', 'ENSG00000055609', 'ENSG00000135679', 'ENSG00000184937',
                   'ENSG00000119772', 'ENSG00000131747', 'ENSG00000127824', 'ENSG00000188229', 'ENSG00000167552',
                   'ENSG00000104833', 'ENSG00000121966', 'ENSG00000141646', 'ENSG00000127616', 'ENSG00000075886',
                   'ENSG00000167553', 'ENSG00000081237', 'ENSG00000077782', 'ENSG00000261456', 'ENSG00000160867',
                   'ENSG00000196230', 'ENSG00000068078', 'ENSG00000145675', 'ENSG00000152086', 'ENSG00000012048',
                   'ENSG00000123416', 'ENSG00000258947', 'ENSG00000182866', 'ENSG00000176890', 'ENSG00000179295',
                   'ENSG00000005339', 'ENSG00000133216', 'ENSG00000134250', 'ENSG00000132155', 'ENSG00000163599',
                   'ENSG00000101162', 'ENSG00000198400', 'ENSG00000183765', 'ENSG00000163513', 'ENSG00000116016',
                   'ENSG00000062822', 'ENSG00000132646', 'ENSG00000076242', 'ENSG00000137285', 'ENSG00000118046',
                   'ENSG00000105810', 'ENSG00000048392', 'ENSG00000162434', 'ENSG00000112715', 'ENSG00000167548',
                   'ENSG00000198900', 'ENSG00000082898', 'ENSG00000085224', 'ENSG00000183337', 'ENSG00000110092',
                   'ENSG00000101868', 'ENSG00000171720', 'ENSG00000083857', 'ENSG00000168702', 'ENSG00000182054',
                   'ENSG00000096968', 'ENSG00000134982', 'ENSG00000141027', 'ENSG00000114861', 'ENSG00000134086',
                   'ENSG00000100393', 'ENSG00000147050', 'ENSG00000119535', 'ENSG00000088832', 'ENSG00000123473',
                   'ENSG00000079432', 'ENSG00000026508', 'ENSG00000143799', 'ENSG00000116478', 'ENSG00000169083',
                   'ENSG00000136826', 'ENSG00000104365', 'ENSG00000166710', 'ENSG00000197299', 'ENSG00000105976',
                   'ENSG00000115414', 'ENSG00000182578', 'ENSG00000131759', 'ENSG00000156970', 'ENSG00000118058',
                   'ENSG00000103197', 'ENSG00000186575', 'ENSG00000092820', 'ENSG00000087245', 'ENSG00000126934',
                   'ENSG00000101972', 'ENSG00000140464', 'ENSG00000188389', 'ENSG00000135446', 'ENSG00000087460',
                   'ENSG00000049618', 'ENSG00000186716', 'ENSG00000196591', 'ENSG00000047936', 'ENSG00000124762',
                   'ENSG00000094631', 'ENSG00000169429', 'ENSG00000168769', 'ENSG00000087586', 'ENSG00000228716',
                   'ENSG00000100697', 'ENSG00000185499', 'ENSG00000107562', 'ENSG00000175387', 'ENSG00000120156',
                   'ENSG00000099956', 'ENSG00000162733', 'ENSG00000142627', 'ENSG00000189079', 'ENSG00000026025',
                   'ENSG00000107485', 'ENSG00000140538', 'ENSG00000140836', 'ENSG00000150907', 'ENSG00000185920',
                   'ENSG00000163930', 'ENSG00000113916', 'ENSG00000104884', 'ENSG00000240065', 'ENSG00000159216',
                   'ENSG00000157168', 'ENSG00000073282', 'ENSG00000091831', 'ENSG00000133895', 'ENSG00000139083',
                   'ENSG00000140443', 'ENSG00000083799', 'ENSG00000019991', 'ENSG00000165025', 'ENSG00000132170',
                   'ENSG00000171791', 'ENSG00000179218', 'ENSG00000116044', 'ENSG00000131981', 'ENSG00000122861',
                   'ENSG00000101115', 'ENSG00000166851', 'ENSG00000105329', 'ENSG00000163939', 'ENSG00000181449',
                   'ENSG00000184634', 'ENSG00000010671', 'ENSG00000105974', 'ENSG00000105639', 'ENSG00000137673',
                   'ENSG00000122512', 'ENSG00000044524', 'ENSG00000169398', 'ENSG00000166888', 'ENSG00000166949',
                   'ENSG00000181163', 'ENSG00000073756', 'ENSG00000133392', 'ENSG00000169604', 'ENSG00000111276',
                   'ENSG00000100985', 'ENSG00000165699', 'ENSG00000125618', 'ENSG00000102265', 'ENSG00000204264',
                   'ENSG00000109471', 'ENSG00000051382', 'ENSG00000111424', 'ENSG00000118785', 'ENSG00000102882',
                   'ENSG00000171456', 'ENSG00000085563', 'ENSG00000138685', 'ENSG00000104419', 'ENSG00000165671',
                   'ENSG00000104320', 'ENSG00000149948', 'ENSG00000105221', 'ENSG00000135100', 'ENSG00000118503',
                   'ENSG00000130816', 'ENSG00000075618', 'ENSG00000178691', 'ENSG00000182944', 'ENSG00000196159',
                   'ENSG00000147257', 'ENSG00000146674', 'ENSG00000105568', 'ENSG00000057657', 'ENSG00000105388',
                   'ENSG00000134371', 'ENSG00000136244', 'ENSG00000272398', 'ENSG00000100292', 'ENSG00000165556',
                   'ENSG00000174059', 'ENSG00000144476', 'ENSG00000175595', 'ENSG00000085276']

        fields = ['id','approved_name','approved_symbol']
        response = self._make_request('/api/latest/private/target',
                                      data=json.dumps(
                                          {'id': targets, 'facets': 'true', 'fields':fields,'go_term':'GO:0014066'}),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        print json_response

    def testPostRelationandTargetFetching(self):
        target = 'ENSG00000157764'
        related_targets_res = self._make_request('/api/latest/private/relation/target/' + target,
                                                  data={'size': 1000},
                                                  token=self._AUTO_GET_TOKEN)
        json_response = json.loads(related_targets_res.data.decode('utf-8'))
        related_targets = [d['object']['id'] for d in json_response['data']]
        fields = ['id', 'approved_name', 'approved_symbol']
        response = self._make_request('/api/latest/private/target',
                                      data=json.dumps(
                                          {'id': related_targets, 'facets': 'true', 'fields':fields}),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        print json_response

    def testPostRelationTargetsWithFacetFiltering(self):
        target = 'ENSG00000157764'
        related_targets_res = self._make_request('/api/latest/private/relation/target/' + target,
                                                  data={'size': 1000},
                                                  token=self._AUTO_GET_TOKEN)
        json_response = json.loads(related_targets_res.data.decode('utf-8'))
        related_targets = [d['object']['id'] for d in json_response['data']]
        fields = ['id','approved_name','approved_symbol']
        response = self._make_request('/api/latest/private/target',
                                      data=json.dumps(
                                          {'id': related_targets, 'facets': 'true', 'fields':fields,'go_term':'GO:0008284'}),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        print json_response



if __name__ == "__main__":
     unittest.main()