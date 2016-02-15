# __author__ = 'andreap'
#
# import unittest
# import requests
#
# class FlaskrTestCase(unittest.TestCase):
#     LOCAL="http://localhost:5000/"
#     REMOTE="https://beta.targetvalidation.org/"
#
#     def setUp(self):
#         pass
#         # self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
#         # flaskr.app.config['TESTING'] = True
#         # self.app = flaskr.app.test_client()
#         # flaskr.init_db()
#
#     def tearDown(self):
#         pass
#
#     def test_simple_search(self):
#         local_r = requests.get(self.LOCAL+"api/latest/search?q=braf")
#         remote_r = requests.get(self.REMOTE+"api/latest/search?q=braf")
#         self.assertResponseOK(local_r, remote_r)
#
#         self.maxDiff = None
#         local = local_r.json()['data']
#         remote = remote_r.json()['data']
#         self.assertListEqual(local,
#                              remote)
#         # for i,e in enumerate(local):
#         #     self.assertDictEqual(local[i],remote[i])
#
#     def test_simple_target_associations(self):
#         local_r = requests.get(self.LOCAL+"api/latest/association/filter?target=ENSG00000096968&datastructure=flat&expandefo=true&filterbyscorevalue_min=0.0&filterbyscorevalue_max=1.0")
#         remote_r = requests.get(self.REMOTE+"api/latest/association/filter?target=ENSG00000096968&datastructure=flat&expandefo=true&filterbyscorevalue_min=0.0&filterbyscorevalue_max=1.0")
#         self.assertResponseOK(local_r, remote_r)
#         self.assertAssociationResultEqual(local_r,remote_r )
#
#     # def test_simple_disease_associations(self):
#     #     local_r = requests.get(self.LOCAL+"api/latest/association?disease=EFO_0000270")
#     #     remote_r = requests.get(self.REMOTE+"api/latest/association?disease=EFO_0000270")
#     #     self.assertResponseOK(local_r, remote_r)
#     #     self.assertAssociationResultEqual(local_r,remote_r )
#
#
#     def assertAssociationResultEqual(self, local_r, remote_r):
#         self.assertResponseOK(local_r,remote_r)
#         self.maxDiff = None
#         local_j = local_r.json()
#         remote_j = remote_r.json()
#         local_total = local_j['total']
#         remote_total = remote_j['total']
#         self.assertAlmostEquals(local_total,remote_total)
#         local_data = local_j['data']
#         remote_data = remote_j['data']
#         self.assertListEqual(local_data,
#                              remote_data)
#         local_facets = local_j['facets']
#         remote_facets = remote_j['facets']
#         self.assertListEqual(local_facets,
#                              remote_facets)
#         # for i,e in enumerate(local):
#         #     self.assertDictEqual(local[i],remote[i])
#
#     def assertResponseOK(self, local_r, remote_r):
#         self.assertEquals(local_r.status_code, 200)
#         self.assertEquals(remote_r.status_code, 200)
# if __name__ == '__main__':
#     unittest.main()