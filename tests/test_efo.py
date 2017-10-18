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
            response = self._make_request('/platform/private/disease/%s'%id, token=self._AUTO_GET_TOKEN)
            self.assertTrue(response.status_code == 200)
            json_response = json.loads(response.data.decode('utf-8'))
            for path in json_response['path_codes']:
                self.assertEqual(path[-1],id, 'disease found')

    def testPostEFO(self):

        diseases = ['EFO_0003770','EFO_0003839','EFO_0003884','EFO_0000668','EFO_0001421','EFO_0002687','EFO_0000378','EFO_0000516','EFO_1001231','HP_0001397','EFO_0001361','EFO_0001645','EFO_0000537','EFO_0000712','EFO_0000717','EFO_0003086','EFO_0005856','EFO_0000195','EFO_0002506','EFO_0003914','EFO_0000319','HP_0001824','EFO_0002617','EFO_0001066','EFO_0004264','EFO_0000660','HP_0000093','EFO_0001359','EFO_0002690','EFO_0000649','EFO_0002614','EFO_0001360','HP_0100543','EFO_0000275','EFO_0003966','EFO_0004220','EFO_0000401','EFO_0000341','EFO_0000612','HP_0002637','EFO_0003768','HP_0003124','EFO_1000657','MP_0001914','EFO_1001461','EFO_0003095','EFO_0006818','EFO_0003821','EFO_0006890','EFO_0000589','EFO_0003777','HP_0003074','EFO_0003818','EFO_0001422','EFO_0004610','EFO_0002460','EFO_0003872','EFO_1000652','EFO_0003106','HP_0001541','EFO_0001059','EFO_0001068','EFO_0003774','EFO_0006859','EFO_0003144','EFO_0006346','EFO_0004285','EFO_0000228','HP_0012115','EFO_0000764','Orphanet_71862','EFO_0000373','EFO_0000684','EFO_0000556','EFO_0004593','EFO_1001375','EFO_0000181','EFO_1001249','EFO_0005140','EFO_0005207','EFO_0005772','EFO_0000284','EFO_0003837','EFO_0000677','EFO_0000662','EFO_0000407','EFO_0005672','EFO_0004149','EFO_1001459','EFO_0004265','EFO_0000318','HP_0001945','EFO_0002087','EFO_0003843','EFO_0000096','EFO_0007328','EFO_0000650','EFO_0005952','EFO_1000637','EFO_0001065','EFO_0001073','EFO_0000464','EFO_0003785','EFO_0000278','HP_0003119','EFO_1001993','EFO_0002508','EFO_0001423','HP_0001395','EFO_0000536','EFO_0000342','EFO_0004190','EFO_0000249','EFO_0000232','EFO_0000574','EFO_0003767','EFO_0005761','EFO_0000289','EFO_0003913','EFO_0005669','EFO_0005230','EFO_0003829','EFO_0004705','HP_0001250','EFO_0004255','EFO_0005741','EFO_0003761','EFO_0000403','EFO_0001067','EFO_0000731','EFO_0000180','EFO_0000292','Orphanet_790','EFO_0005756','EFO_1001496','EFO_0005773','EFO_0005288','EFO_0003882','EFO_0000701','EFO_0000691','EFO_0003763','Orphanet_70','EFO_0001061','Orphanet_733','EFO_0006803','EFO_0000400','EFO_0002503','EFO_0000702','EFO_0004237','EFO_0000692','EFO_0002890','EFO_0000584','EFO_1001517','HP_0001919','EFO_0000253','EFO_0003885','EFO_0005221','HP_0002014','EFO_0000198','EFO_0005543','EFO_0000685','EFO_0004214','EFO_0005251','EFO_0004906','EFO_0000337','EFO_0000713','EFO_0004238','Orphanet_797','EFO_0005762','EFO_0004236','EFO_0000545','EFO_0000621','EFO_0000783','EFO_0007540','Orphanet_70589','EFO_1000014','HP_0001510','EFO_1000058','EFO_0000474','EFO_0000565','EFO_0000405','EFO_1001512','EFO_0000183','EFO_1001950','EFO_1000068','EFO_0003100','EFO_0000673','MP_0001845','EFO_0006788','EFO_0000239','EFO_0004272','HP_0000833','EFO_0000729','EFO_0005854','EFO_0001378','EFO_1000845','EFO_0000313','EFO_0000270','EFO_1001951','EFO_0000707','HP_0001943','EFO_0003890','EFO_0004269','HP_0001268','EFO_0005755','EFO_0000199','Orphanet_3389','EFO_0003781','EFO_0000768','EFO_1000581','EFO_0001060','EFO_0000294','EFO_0000637','EFO_0000389','Orphanet_98896','EFO_1001949','EFO_1001770','EFO_0003764','HP_0012594','EFO_1000999','EFO_0000666','EFO_0006343','EFO_0001069','EFO_0002422','EFO_1000985','EFO_0000538','EFO_1001494','EFO_1000954','Orphanet_791','EFO_0000196','EFO_0001668','EFO_0006834','EFO_0000588','EFO_0000508','Orphanet_946','EFO_0005414','EFO_1001121','Orphanet_68367','EFO_0001071','HP_0001873','EFO_0003779','EFO_0003907','HP_0000708','EFO_0000681','EFO_0003063','EFO_1000044','EFO_1001875','EFO_1001475','EFO_0003894','EFO_0001064','EFO_0000384','EFO_0001054','EFO_1001478','EFO_0000765','Orphanet_232','EFO_1001457','EFO_1000782','EFO_0000503','EFO_0003060','Orphanet_85453','EFO_0004244','Orphanet_98967','EFO_0005406','EFO_1000616','EFO_0003033','EFO_0002618','EFO_0004247','EFO_0001416','EFO_0000558','HP_0000545','Orphanet_685','EFO_0003030','EFO_0002893','EFO_0000178','Orphanet_183660','EFO_1001484','EFO_0004289','EFO_0003822','EFO_0004193','EFO_0003778','EFO_0003047','EFO_0003922','Orphanet_586','EFO_0004208','EFO_0005537','EFO_0000555','EFO_0004683','EFO_0000333','EFO_0004718','HP_0001548','EFO_0001072','EFO_0000339','EFO_0004274','EFO_0005549','HP_0004326','EFO_0005922','EFO_1000726','EFO_0002612','EFO_0002918','HP_0002315','EFO_0006352','EFO_1001986','EFO_0004260','EFO_1001255','EFO_1001486','EFO_1001491','Orphanet_3157','EFO_0001666','Orphanet_1478','EFO_0000203','EFO_0000272','EFO_1000025','EFO_0001062','EFO_0002686','EFO_0005593','EFO_0003870','EFO_0000549','EFO_0000349','EFO_0001358','EFO_0000430','EFO_0003917','EFO_1000478','Orphanet_54247','EFO_0004212','EFO_0000220','Orphanet_399','EFO_1001034','EFO_0006857','EFO_0000478','EFO_0005592','EFO_0004234','EFO_1000601','EFO_0001075','EFO_1000783','EFO_0003103','EFO_0004248','EFO_0002609','EFO_0001642','EFO_0004142','EFO_1001226','EFO_1001157','EFO_1001956','EFO_0005226','EFO_1001904','EFO_0004145','EFO_1000961','EFO_0000222','EFO_0003898','EFO_0000174','EFO_0000186','EFO_1001469','EFO_0005531','Orphanet_98473','EFO_0000266','EFO_1001482','EFO_0000495','EFO_0003899','EFO_1001991','EFO_0004991','EFO_0003918','EFO_1000307','EFO_0006790','EFO_0000309','Orphanet_98895','EFO_0002939','EFO_0000756','EFO_1001364','EFO_1000675','EFO_0003896','EFO_1001134','EFO_0000398','EFO_0000280','EFO_0002621','EFO_0000519','Orphanet_98938','EFO_1000355','EFO_0000095','EFO_1001955','HP_0000938','EFO_1000802','EFO_0000274','EFO_0002517','EFO_0003929','EFO_0000678','EFO_0003093','EFO_1000049','EFO_1001209','EFO_0000641','EFO_0000708','EFO_0000514','EFO_0004259','EFO_0004720','EFO_0003964','EFO_1001168','EFO_0003102','EFO_0004243','EFO_0002913','EFO_0006544','EFO_0004211','EFO_1001028','EFO_0006505','EFO_0003780','EFO_1000635','EFO_0002499','EFO_0000618','EFO_1001480','EFO_1001207','EFO_0003847','EFO_0004288','EFO_0000224','EFO_0001663','Orphanet_654','EFO_1000880','HP_0012735','EFO_1001892','EFO_1000003','EFO_0003762','EFO_0000432','EFO_0007485','EFO_0006510','EFO_0000769','EFO_0000564','Orphanet_156071','EFO_0003758','Orphanet_805','EFO_0000501','EFO_1001968','HP_0100256','EFO_1001458','EFO_0006342','Orphanet_342','EFO_0000311','EFO_0005676','EFO_1000636','EFO_0004992','EFO_0007444','EFO_0003968','EFO_1000869','EFO_0004607','HP_0000979','EFO_0004210','EFO_0000770','EFO_0005232','EFO_0000778','EFO_0004986','Orphanet_1572','Orphanet_379','EFO_0000182','Orphanet_44890','EFO_0003948','EFO_0001074','EFO_0006812','EFO_0000209','HP_0002110','EFO_0003877','EFO_1001176','Orphanet_98671','HP_0004398','EFO_0003819','EFO_0007486','EFO_0003888','EFO_0005044','Orphanet_754','EFO_1000831','EFO_1000627','EFO_0005774','EFO_1001825','EFO_1000882','EFO_0000762','EFO_1001051','EFO_1000826','Orphanet_558','EFO_0003931','Orphanet_275766','EFO_0007067','EFO_0000694','EFO_0000479','EFO_0003830','EFO_0000304','EFO_1000760','EFO_0003869','EFO_0005407','EFO_1000646','EFO_0000616','EFO_0002496','EFO_1000172','EFO_0007149','EFO_0004283','EFO_0004277','EFO_0000571','EFO_0000365','Orphanet_280569','EFO_0004911','EFO_0004242','EFO_1000028','EFO_0000706','EFO_0000676','Orphanet_538','EFO_0004698','HP_0100790','HP_0004936','EFO_0000231','HP_0002829','EFO_0005562','EFO_0004273','EFO_0004799','HP_0000989','HP_0030151','EFO_1000642','EFO_0003827','EFO_1001129','EFO_0004246','EFO_0000499','EFO_1000941','EFO_0007183','EFO_0006738','EFO_0003756','EFO_0004252','EFO_0007204','Orphanet_309005','Orphanet_322','HP_0002619','EFO_0000773','EFO_0004254','EFO_0006772','HP_0000964','HP_0000020','EFO_1001434','EFO_0003050','EFO_0005045','EFO_0000305','HP_0003072','EFO_0003833','Orphanet_101330','EFO_1000292','EFO_0003834','EFO_0002511','Orphanet_1334','EFO_0000569','EFO_0000759','EFO_0004268','Orphanet_30391','HP_0001915','EFO_0002546','EFO_0003854','EFO_0002429','EFO_0000308','EFO_0005569','EFO_0004192','Orphanet_97242','EFO_0004251','EFO_0000221','EFO_0000557','EFO_0000632','EFO_0003875','Orphanet_906','Orphanet_178','EFO_0003766','EFO_1001787','EFO_0007053','DOID_13406','EFO_0000348','EFO_0006789','EFO_1001272','EFO_1001818','Orphanet_609','EFO_1000024','EFO_1001474','EFO_0004230','EFO_0005842','EFO_0004233','Orphanet_848','EFO_0004287','Orphanet_524','EFO_0000699','Orphanet_166','EFO_0001063','EFO_1001996','EFO_1001139','Orphanet_43','EFO_0000191','EFO_0001376','EFO_1000811','Orphanet_282','EFO_1000794','Orphanet_100','EFO_1001141','EFO_0002627','EFO_1001497','EFO_0000625','Orphanet_908','EFO_1001460','Orphanet_79383','EFO_0004286','EFO_0007297','EFO_0001379','EFO_0000465','EFO_1000932','HP_0005521','EFO_1001898','EFO_1000668','EFO_0005046','EFO_0004226','EFO_1000660','Orphanet_612','EFO_1001069','EFO_0003096','Orphanet_167','EFO_0000551','HP_0011950','EFO_1001972','EFO_0003867','EFO_0004280','Orphanet_1465','EFO_0004719','EFO_0004229','EFO_0007405','EFO_1001961','EFO_0002689','EFO_0000772','HP_0002019','EFO_0003840','Orphanet_71','EFO_0005088','EFO_1000015','HP_0002840','EFO_1001373','EFO_0003099','EFO_1000784','HP_0200042','EFO_1001158','Orphanet_3261','EFO_1001001','EFO_0002756','HP_0000175','EFO_0002616','EFO_0005203','EFO_0005558','EFO_1001095','EFO_0007344','EFO_0007481','HP_0003326','EFO_0005631','EFO_0004249','EFO_0004143','EFO_0005578','EFO_0007160','EFO_1000632','EFO_0007141','Orphanet_163927','EFO_0005687','EFO_0003956','EFO_0007517','EFO_0000540','EFO_0007187','EFO_1000749','EFO_1001179','EFO_0000094','Orphanet_974','EFO_1001485','EFO_1001100','Orphanet_774','EFO_1001161','Orphanet_2478','HP_0000023','EFO_0005297','EFO_0005815','EFO_1001466','EFO_0003032','EFO_0007257','EFO_0006460','EFO_0007323','EFO_1001870','Orphanet_79364','EFO_1000041','EFO_0000326','Orphanet_1480','EFO_1001252','Orphanet_418','EFO_1001882','EFO_0002608','Orphanet_1871','EFO_0004723','Orphanet_206647','EFO_1001020','Orphanet_2442','Orphanet_2598','HP_0002018','EFO_1000727','EFO_1001927','EFO_0007427','EFO_1000989','EFO_0007205','Orphanet_388','Orphanet_811','EFO_1001394','EFO_0005878','EFO_0004267','EFO_0006318','EFO_1001062','EFO_0005950','Orphanet_2134','EFO_0004803','Orphanet_144','EFO_1001103','GO_0007568','EFO_0003928','EFO_1001436','EFO_0001070','HP_0002719','Orphanet_31112','HP_0001636','EFO_0007504','Orphanet_79201','EFO_1000653','Orphanet_79430','Orphanet_98969','EFO_1000036','EFO_1001463','EFO_0003029','EFO_0005681','EFO_0007490','EFO_1001114','EFO_0004215','Orphanet_79292','EFO_1001237','Orphanet_98853','EFO_0003959','Orphanet_909','HP_0002901','EFO_0002424','EFO_0005235','HP_0002239','EFO_0000248','EFO_1001068','Orphanet_267','EFO_0004253','Orphanet_65','Orphanet_765','HP_0003073','EFO_0004256','EFO_1000631','EFO_0007216','EFO_0003921','Orphanet_86823','EFO_0007480','EFO_0004263','EFO_0004777','Orphanet_2968','HP_0100633','Orphanet_758','HP_0002015','EFO_0004566','EFO_0003825','EFO_1001254','EFO_1000298','Orphanet_1872','EFO_0002610','EFO_0002622','Orphanet_636','EFO_0007332','EFO_0005547','EFO_0002892','EFO_1001472','EFO_0007541','EFO_0007443','EFO_1001917','EFO_0003940','EFO_0000553','EFO_0004235','EFO_0007214','EFO_0006951','EFO_0005319','EFO_0006988','EFO_1001465','HP_0001891','HP_0100537','EFO_1001311','EFO_0000225','Orphanet_229717','EFO_0003895','HP_0000118','Orphanet_84','EFO_0004266','Orphanet_64739','Orphanet_683','Orphanet_552','EFO_0003930','EFO_1001454','Orphanet_98869','EFO_1001388','Orphanet_101997','EFO_1001155','EFO_0005540','EFO_0004194','EFO_0005295','EFO_1001246','EFO_0001380','EFO_0007310','EFO_0005701','EFO_0001057','Orphanet_269','Orphanet_486','EFO_1001153','Orphanet_716','EFO_0005306','Orphanet_68380','EFO_0007364','EFO_1000630','EFO_1000634','EFO_0007299','Orphanet_655','EFO_0003782','HP_0002373','EFO_0001357','EFO_0007157','EFO_0005303','EFO_1000017','EFO_1000299','EFO_1000910','EFO_0000466','Orphanet_1037','Orphanet_91378','Orphanet_355','Orphanet_98970','EFO_0003149','Orphanet_447','EFO_0000437','EFO_0003108','EFO_1000039','Orphanet_180','EFO_1001481','EFO_1001096','EFO_1001016','EFO_1001426','HP_0000252','Orphanet_98306','Orphanet_647','EFO_0006858','EFO_0004197','EFO_1001923','EFO_1001792','EFO_0006888','Orphanet_800','Orphanet_231214','Orphanet_892','Orphanet_1652','EFO_1001248','EFO_0007185','EFO_1000956','EFO_1001346','EFO_0005240','EFO_0000279','EFO_0003876','Orphanet_528','HP_0002745','EFO_0005584','EFO_0007153','EFO_1000785','Orphanet_740','Orphanet_902','EFO_0004228','Orphanet_79277','EFO_0007326','EFO_0000640','Orphanet_817','Orphanet_183663','EFO_0005252','EFO_0005570','EFO_0007415','EFO_0005576','EFO_0004616','EFO_0007446','EFO_1000045','Orphanet_910','EFO_1000566','Orphanet_881','EFO_0000763','Orphanet_96321','EFO_1000879','Orphanet_182098','EFO_1000842','EFO_0004282','EFO_0007245','EFO_1000233','Orphanet_391665','Orphanet_54260','EFO_0007391','Orphanet_136','EFO_0003901','EFO_0007457','EFO_0004540','EFO_0005532','EFO_0005846','EFO_0007347','EFO_0006918','EFO_0003075','HP_0000103','EFO_1001312','EFO_0005296','Orphanet_3388','Orphanet_2573','EFO_0005803','EFO_1000975','Orphanet_273','EFO_0007305','Orphanet_277','EFO_1000948','EFO_1000254','Orphanet_101090','EFO_0002916','EFO_1000054','Orphanet_540','HP_0000483','Orphanet_324','HP_0011868','EFO_0000653','EFO_0004138','Orphanet_319605','HP_0000639','EFO_0004710','HP_0001657','EFO_0005224','EFO_0004895','EFO_0003097','EFO_0007229','Orphanet_792','EFO_0007330','EFO_0003891','Orphanet_183666','Orphanet_268','Orphanet_244','EFO_0006861','Orphanet_3342','EFO_1000209','EFO_0000217','EFO_1000885','EFO_1001476','EFO_0003952','Orphanet_846','EFO_0004340','EFO_0006513','Orphanet_79211','Orphanet_739','EFO_1000073','EFO_1000418','EFO_1001309']

        fields = ['label', 'code']
        response = self._make_request('/api/latest/private/disease',
                                      data=json.dumps(
                                          {'diseases': diseases, 'facets': 'true', 'fields': fields}),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        sig_labels = [bucket['key'] for bucket in json_response['facets']['significantTherapeuticAreas']['buckets']]
        print 'Groups of related diseases {}'.format(sig_labels)
        print 'Related Diseases with labels {}'.format(json_response['data'])
        self.assertGreater(len(json_response['data']), 0)
        self.assertGreater(len(sig_labels), 0)
        print json_response

    def testPostEFOWithLabelFiltering(self):

        diseases = ['EFO_0003770', 'EFO_0003839', 'EFO_0003884', 'EFO_0000668', 'EFO_0001421', 'EFO_0002687',
                    'EFO_0000378', 'EFO_0000516', 'EFO_1001231', 'HP_0001397', 'EFO_0001361', 'EFO_0001645',
                    'EFO_0000537', 'EFO_0000712', 'EFO_0000717', 'EFO_0003086', 'EFO_0005856', 'EFO_0000195',
                    'EFO_0002506', 'EFO_0003914', 'EFO_0000319', 'HP_0001824', 'EFO_0002617', 'EFO_0001066',
                    'EFO_0004264', 'EFO_0000660', 'HP_0000093', 'EFO_0001359', 'EFO_0002690', 'EFO_0000649',
                    'EFO_0002614', 'EFO_0001360', 'HP_0100543', 'EFO_0000275', 'EFO_0003966', 'EFO_0004220',
                    'EFO_0000401', 'EFO_0000341', 'EFO_0000612', 'HP_0002637', 'EFO_0003768', 'HP_0003124',
                    'EFO_1000657', 'MP_0001914', 'EFO_1001461', 'EFO_0003095', 'EFO_0006818', 'EFO_0003821',
                    'EFO_0006890', 'EFO_0000589', 'EFO_0003777', 'HP_0003074', 'EFO_0003818', 'EFO_0001422',
                    'EFO_0004610', 'EFO_0002460', 'EFO_0003872', 'EFO_1000652', 'EFO_0003106', 'HP_0001541',
                    'EFO_0001059', 'EFO_0001068', 'EFO_0003774', 'EFO_0006859', 'EFO_0003144', 'EFO_0006346',
                    'EFO_0004285', 'EFO_0000228', 'HP_0012115', 'EFO_0000764', 'Orphanet_71862', 'EFO_0000373',
                    'EFO_0000684', 'EFO_0000556', 'EFO_0004593', 'EFO_1001375', 'EFO_0000181', 'EFO_1001249',
                    'EFO_0005140', 'EFO_0005207', 'EFO_0005772', 'EFO_0000284', 'EFO_0003837', 'EFO_0000677',
                    'EFO_0000662', 'EFO_0000407', 'EFO_0005672', 'EFO_0004149', 'EFO_1001459', 'EFO_0004265',
                    'EFO_0000318', 'HP_0001945', 'EFO_0002087', 'EFO_0003843', 'EFO_0000096', 'EFO_0007328',
                    'EFO_0000650', 'EFO_0005952', 'EFO_1000637', 'EFO_0001065', 'EFO_0001073', 'EFO_0000464',
                    'EFO_0003785', 'EFO_0000278', 'HP_0003119', 'EFO_1001993', 'EFO_0002508', 'EFO_0001423',
                    'HP_0001395', 'EFO_0000536', 'EFO_0000342', 'EFO_0004190', 'EFO_0000249', 'EFO_0000232',
                    'EFO_0000574', 'EFO_0003767', 'EFO_0005761', 'EFO_0000289', 'EFO_0003913', 'EFO_0005669',
                    'EFO_0005230', 'EFO_0003829', 'EFO_0004705', 'HP_0001250', 'EFO_0004255', 'EFO_0005741',
                    'EFO_0003761', 'EFO_0000403', 'EFO_0001067', 'EFO_0000731', 'EFO_0000180', 'EFO_0000292',
                    'Orphanet_790', 'EFO_0005756', 'EFO_1001496', 'EFO_0005773', 'EFO_0005288', 'EFO_0003882',
                    'EFO_0000701', 'EFO_0000691', 'EFO_0003763', 'Orphanet_70', 'EFO_0001061', 'Orphanet_733',
                    'EFO_0006803', 'EFO_0000400', 'EFO_0002503', 'EFO_0000702', 'EFO_0004237', 'EFO_0000692',
                    'EFO_0002890', 'EFO_0000584', 'EFO_1001517', 'HP_0001919', 'EFO_0000253', 'EFO_0003885',
                    'EFO_0005221', 'HP_0002014', 'EFO_0000198', 'EFO_0005543', 'EFO_0000685', 'EFO_0004214',
                    'EFO_0005251', 'EFO_0004906', 'EFO_0000337', 'EFO_0000713', 'EFO_0004238', 'Orphanet_797',
                    'EFO_0005762', 'EFO_0004236', 'EFO_0000545', 'EFO_0000621', 'EFO_0000783', 'EFO_0007540',
                    'Orphanet_70589', 'EFO_1000014', 'HP_0001510', 'EFO_1000058', 'EFO_0000474', 'EFO_0000565',
                    'EFO_0000405', 'EFO_1001512', 'EFO_0000183', 'EFO_1001950', 'EFO_1000068', 'EFO_0003100',
                    'EFO_0000673', 'MP_0001845', 'EFO_0006788', 'EFO_0000239', 'EFO_0004272', 'HP_0000833',
                    'EFO_0000729', 'EFO_0005854', 'EFO_0001378', 'EFO_1000845', 'EFO_0000313', 'EFO_0000270',
                    'EFO_1001951', 'EFO_0000707', 'HP_0001943', 'EFO_0003890', 'EFO_0004269', 'HP_0001268',
                    'EFO_0005755', 'EFO_0000199', 'Orphanet_3389', 'EFO_0003781', 'EFO_0000768', 'EFO_1000581',
                    'EFO_0001060', 'EFO_0000294', 'EFO_0000637', 'EFO_0000389', 'Orphanet_98896', 'EFO_1001949',
                    'EFO_1001770', 'EFO_0003764', 'HP_0012594', 'EFO_1000999', 'EFO_0000666', 'EFO_0006343',
                    'EFO_0001069', 'EFO_0002422', 'EFO_1000985', 'EFO_0000538', 'EFO_1001494', 'EFO_1000954',
                    'Orphanet_791', 'EFO_0000196', 'EFO_0001668', 'EFO_0006834', 'EFO_0000588', 'EFO_0000508',
                    'Orphanet_946', 'EFO_0005414', 'EFO_1001121', 'Orphanet_68367', 'EFO_0001071', 'HP_0001873',
                    'EFO_0003779', 'EFO_0003907', 'HP_0000708', 'EFO_0000681', 'EFO_0003063', 'EFO_1000044',
                    'EFO_1001875', 'EFO_1001475', 'EFO_0003894', 'EFO_0001064', 'EFO_0000384', 'EFO_0001054',
                    'EFO_1001478', 'EFO_0000765', 'Orphanet_232', 'EFO_1001457', 'EFO_1000782', 'EFO_0000503',
                    'EFO_0003060', 'Orphanet_85453', 'EFO_0004244', 'Orphanet_98967', 'EFO_0005406', 'EFO_1000616',
                    'EFO_0003033', 'EFO_0002618', 'EFO_0004247', 'EFO_0001416', 'EFO_0000558', 'HP_0000545',
                    'Orphanet_685', 'EFO_0003030', 'EFO_0002893', 'EFO_0000178', 'Orphanet_183660', 'EFO_1001484',
                    'EFO_0004289', 'EFO_0003822', 'EFO_0004193', 'EFO_0003778', 'EFO_0003047', 'EFO_0003922',
                    'Orphanet_586', 'EFO_0004208', 'EFO_0005537', 'EFO_0000555', 'EFO_0004683', 'EFO_0000333',
                    'EFO_0004718', 'HP_0001548', 'EFO_0001072', 'EFO_0000339', 'EFO_0004274', 'EFO_0005549',
                    'HP_0004326', 'EFO_0005922', 'EFO_1000726', 'EFO_0002612', 'EFO_0002918', 'HP_0002315',
                    'EFO_0006352', 'EFO_1001986', 'EFO_0004260', 'EFO_1001255', 'EFO_1001486', 'EFO_1001491',
                    'Orphanet_3157', 'EFO_0001666', 'Orphanet_1478', 'EFO_0000203', 'EFO_0000272', 'EFO_1000025',
                    'EFO_0001062', 'EFO_0002686', 'EFO_0005593', 'EFO_0003870', 'EFO_0000549', 'EFO_0000349',
                    'EFO_0001358', 'EFO_0000430', 'EFO_0003917', 'EFO_1000478', 'Orphanet_54247', 'EFO_0004212',
                    'EFO_0000220', 'Orphanet_399', 'EFO_1001034', 'EFO_0006857', 'EFO_0000478', 'EFO_0005592',
                    'EFO_0004234', 'EFO_1000601', 'EFO_0001075', 'EFO_1000783', 'EFO_0003103', 'EFO_0004248',
                    'EFO_0002609', 'EFO_0001642', 'EFO_0004142', 'EFO_1001226', 'EFO_1001157', 'EFO_1001956',
                    'EFO_0005226', 'EFO_1001904', 'EFO_0004145', 'EFO_1000961', 'EFO_0000222', 'EFO_0003898',
                    'EFO_0000174', 'EFO_0000186', 'EFO_1001469', 'EFO_0005531', 'Orphanet_98473', 'EFO_0000266',
                    'EFO_1001482', 'EFO_0000495', 'EFO_0003899', 'EFO_1001991', 'EFO_0004991', 'EFO_0003918',
                    'EFO_1000307', 'EFO_0006790', 'EFO_0000309', 'Orphanet_98895', 'EFO_0002939', 'EFO_0000756',
                    'EFO_1001364', 'EFO_1000675', 'EFO_0003896', 'EFO_1001134', 'EFO_0000398', 'EFO_0000280',
                    'EFO_0002621', 'EFO_0000519', 'Orphanet_98938', 'EFO_1000355', 'EFO_0000095', 'EFO_1001955',
                    'HP_0000938', 'EFO_1000802', 'EFO_0000274', 'EFO_0002517', 'EFO_0003929', 'EFO_0000678',
                    'EFO_0003093', 'EFO_1000049', 'EFO_1001209', 'EFO_0000641', 'EFO_0000708', 'EFO_0000514',
                    'EFO_0004259', 'EFO_0004720', 'EFO_0003964', 'EFO_1001168', 'EFO_0003102', 'EFO_0004243',
                    'EFO_0002913', 'EFO_0006544', 'EFO_0004211', 'EFO_1001028', 'EFO_0006505', 'EFO_0003780',
                    'EFO_1000635', 'EFO_0002499', 'EFO_0000618', 'EFO_1001480', 'EFO_1001207', 'EFO_0003847',
                    'EFO_0004288', 'EFO_0000224', 'EFO_0001663', 'Orphanet_654', 'EFO_1000880', 'HP_0012735',
                    'EFO_1001892', 'EFO_1000003', 'EFO_0003762', 'EFO_0000432', 'EFO_0007485', 'EFO_0006510',
                    'EFO_0000769', 'EFO_0000564', 'Orphanet_156071', 'EFO_0003758', 'Orphanet_805', 'EFO_0000501',
                    'EFO_1001968', 'HP_0100256', 'EFO_1001458', 'EFO_0006342', 'Orphanet_342', 'EFO_0000311',
                    'EFO_0005676', 'EFO_1000636', 'EFO_0004992', 'EFO_0007444', 'EFO_0003968', 'EFO_1000869',
                    'EFO_0004607', 'HP_0000979', 'EFO_0004210', 'EFO_0000770', 'EFO_0005232', 'EFO_0000778',
                    'EFO_0004986', 'Orphanet_1572', 'Orphanet_379', 'EFO_0000182', 'Orphanet_44890', 'EFO_0003948',
                    'EFO_0001074', 'EFO_0006812', 'EFO_0000209', 'HP_0002110', 'EFO_0003877', 'EFO_1001176',
                    'Orphanet_98671', 'HP_0004398', 'EFO_0003819', 'EFO_0007486', 'EFO_0003888', 'EFO_0005044',
                    'Orphanet_754', 'EFO_1000831', 'EFO_1000627', 'EFO_0005774', 'EFO_1001825', 'EFO_1000882',
                    'EFO_0000762', 'EFO_1001051', 'EFO_1000826', 'Orphanet_558', 'EFO_0003931', 'Orphanet_275766',
                    'EFO_0007067', 'EFO_0000694', 'EFO_0000479', 'EFO_0003830', 'EFO_0000304', 'EFO_1000760',
                    'EFO_0003869', 'EFO_0005407', 'EFO_1000646', 'EFO_0000616', 'EFO_0002496', 'EFO_1000172',
                    'EFO_0007149', 'EFO_0004283', 'EFO_0004277', 'EFO_0000571', 'EFO_0000365', 'Orphanet_280569',
                    'EFO_0004911', 'EFO_0004242', 'EFO_1000028', 'EFO_0000706', 'EFO_0000676', 'Orphanet_538',
                    'EFO_0004698', 'HP_0100790', 'HP_0004936', 'EFO_0000231', 'HP_0002829', 'EFO_0005562',
                    'EFO_0004273', 'EFO_0004799', 'HP_0000989', 'HP_0030151', 'EFO_1000642', 'EFO_0003827',
                    'EFO_1001129', 'EFO_0004246', 'EFO_0000499', 'EFO_1000941', 'EFO_0007183', 'EFO_0006738',
                    'EFO_0003756', 'EFO_0004252', 'EFO_0007204', 'Orphanet_309005', 'Orphanet_322', 'HP_0002619',
                    'EFO_0000773', 'EFO_0004254', 'EFO_0006772', 'HP_0000964', 'HP_0000020', 'EFO_1001434',
                    'EFO_0003050', 'EFO_0005045', 'EFO_0000305', 'HP_0003072', 'EFO_0003833', 'Orphanet_101330',
                    'EFO_1000292', 'EFO_0003834', 'EFO_0002511', 'Orphanet_1334', 'EFO_0000569', 'EFO_0000759',
                    'EFO_0004268', 'Orphanet_30391', 'HP_0001915', 'EFO_0002546', 'EFO_0003854', 'EFO_0002429',
                    'EFO_0000308', 'EFO_0005569', 'EFO_0004192', 'Orphanet_97242', 'EFO_0004251', 'EFO_0000221',
                    'EFO_0000557', 'EFO_0000632', 'EFO_0003875', 'Orphanet_906', 'Orphanet_178', 'EFO_0003766',
                    'EFO_1001787', 'EFO_0007053', 'DOID_13406', 'EFO_0000348', 'EFO_0006789', 'EFO_1001272',
                    'EFO_1001818', 'Orphanet_609', 'EFO_1000024', 'EFO_1001474', 'EFO_0004230', 'EFO_0005842',
                    'EFO_0004233', 'Orphanet_848', 'EFO_0004287', 'Orphanet_524', 'EFO_0000699', 'Orphanet_166',
                    'EFO_0001063', 'EFO_1001996', 'EFO_1001139', 'Orphanet_43', 'EFO_0000191', 'EFO_0001376',
                    'EFO_1000811', 'Orphanet_282', 'EFO_1000794', 'Orphanet_100', 'EFO_1001141', 'EFO_0002627',
                    'EFO_1001497', 'EFO_0000625', 'Orphanet_908', 'EFO_1001460', 'Orphanet_79383', 'EFO_0004286',
                    'EFO_0007297', 'EFO_0001379', 'EFO_0000465', 'EFO_1000932', 'HP_0005521', 'EFO_1001898',
                    'EFO_1000668', 'EFO_0005046', 'EFO_0004226', 'EFO_1000660', 'Orphanet_612', 'EFO_1001069',
                    'EFO_0003096', 'Orphanet_167', 'EFO_0000551', 'HP_0011950', 'EFO_1001972', 'EFO_0003867',
                    'EFO_0004280', 'Orphanet_1465', 'EFO_0004719', 'EFO_0004229', 'EFO_0007405', 'EFO_1001961',
                    'EFO_0002689', 'EFO_0000772', 'HP_0002019', 'EFO_0003840', 'Orphanet_71', 'EFO_0005088',
                    'EFO_1000015', 'HP_0002840', 'EFO_1001373', 'EFO_0003099', 'EFO_1000784', 'HP_0200042',
                    'EFO_1001158', 'Orphanet_3261', 'EFO_1001001', 'EFO_0002756', 'HP_0000175', 'EFO_0002616',
                    'EFO_0005203', 'EFO_0005558', 'EFO_1001095', 'EFO_0007344', 'EFO_0007481', 'HP_0003326',
                    'EFO_0005631', 'EFO_0004249', 'EFO_0004143', 'EFO_0005578', 'EFO_0007160', 'EFO_1000632',
                    'EFO_0007141', 'Orphanet_163927', 'EFO_0005687', 'EFO_0003956', 'EFO_0007517', 'EFO_0000540',
                    'EFO_0007187', 'EFO_1000749', 'EFO_1001179', 'EFO_0000094', 'Orphanet_974', 'EFO_1001485',
                    'EFO_1001100', 'Orphanet_774', 'EFO_1001161', 'Orphanet_2478', 'HP_0000023', 'EFO_0005297',
                    'EFO_0005815', 'EFO_1001466', 'EFO_0003032', 'EFO_0007257', 'EFO_0006460', 'EFO_0007323',
                    'EFO_1001870', 'Orphanet_79364', 'EFO_1000041', 'EFO_0000326', 'Orphanet_1480', 'EFO_1001252',
                    'Orphanet_418', 'EFO_1001882', 'EFO_0002608', 'Orphanet_1871', 'EFO_0004723', 'Orphanet_206647',
                    'EFO_1001020', 'Orphanet_2442', 'Orphanet_2598', 'HP_0002018', 'EFO_1000727', 'EFO_1001927',
                    'EFO_0007427', 'EFO_1000989', 'EFO_0007205', 'Orphanet_388', 'Orphanet_811', 'EFO_1001394',
                    'EFO_0005878', 'EFO_0004267', 'EFO_0006318', 'EFO_1001062', 'EFO_0005950', 'Orphanet_2134',
                    'EFO_0004803', 'Orphanet_144', 'EFO_1001103', 'GO_0007568', 'EFO_0003928', 'EFO_1001436',
                    'EFO_0001070', 'HP_0002719', 'Orphanet_31112', 'HP_0001636', 'EFO_0007504', 'Orphanet_79201',
                    'EFO_1000653', 'Orphanet_79430', 'Orphanet_98969', 'EFO_1000036', 'EFO_1001463', 'EFO_0003029',
                    'EFO_0005681', 'EFO_0007490', 'EFO_1001114', 'EFO_0004215', 'Orphanet_79292', 'EFO_1001237',
                    'Orphanet_98853', 'EFO_0003959', 'Orphanet_909', 'HP_0002901', 'EFO_0002424', 'EFO_0005235',
                    'HP_0002239', 'EFO_0000248', 'EFO_1001068', 'Orphanet_267', 'EFO_0004253', 'Orphanet_65',
                    'Orphanet_765', 'HP_0003073', 'EFO_0004256', 'EFO_1000631', 'EFO_0007216', 'EFO_0003921',
                    'Orphanet_86823', 'EFO_0007480', 'EFO_0004263', 'EFO_0004777', 'Orphanet_2968', 'HP_0100633',
                    'Orphanet_758', 'HP_0002015', 'EFO_0004566', 'EFO_0003825', 'EFO_1001254', 'EFO_1000298',
                    'Orphanet_1872', 'EFO_0002610', 'EFO_0002622', 'Orphanet_636', 'EFO_0007332', 'EFO_0005547',
                    'EFO_0002892', 'EFO_1001472', 'EFO_0007541', 'EFO_0007443', 'EFO_1001917', 'EFO_0003940',
                    'EFO_0000553', 'EFO_0004235', 'EFO_0007214', 'EFO_0006951', 'EFO_0005319', 'EFO_0006988',
                    'EFO_1001465', 'HP_0001891', 'HP_0100537', 'EFO_1001311', 'EFO_0000225', 'Orphanet_229717',
                    'EFO_0003895', 'HP_0000118', 'Orphanet_84', 'EFO_0004266', 'Orphanet_64739', 'Orphanet_683',
                    'Orphanet_552', 'EFO_0003930', 'EFO_1001454', 'Orphanet_98869', 'EFO_1001388', 'Orphanet_101997',
                    'EFO_1001155', 'EFO_0005540', 'EFO_0004194', 'EFO_0005295', 'EFO_1001246', 'EFO_0001380',
                    'EFO_0007310', 'EFO_0005701', 'EFO_0001057', 'Orphanet_269', 'Orphanet_486', 'EFO_1001153',
                    'Orphanet_716', 'EFO_0005306', 'Orphanet_68380', 'EFO_0007364', 'EFO_1000630', 'EFO_1000634',
                    'EFO_0007299', 'Orphanet_655', 'EFO_0003782', 'HP_0002373', 'EFO_0001357', 'EFO_0007157',
                    'EFO_0005303', 'EFO_1000017', 'EFO_1000299', 'EFO_1000910', 'EFO_0000466', 'Orphanet_1037',
                    'Orphanet_91378', 'Orphanet_355', 'Orphanet_98970', 'EFO_0003149', 'Orphanet_447', 'EFO_0000437',
                    'EFO_0003108', 'EFO_1000039', 'Orphanet_180', 'EFO_1001481', 'EFO_1001096', 'EFO_1001016',
                    'EFO_1001426', 'HP_0000252', 'Orphanet_98306', 'Orphanet_647', 'EFO_0006858', 'EFO_0004197',
                    'EFO_1001923', 'EFO_1001792', 'EFO_0006888', 'Orphanet_800', 'Orphanet_231214', 'Orphanet_892',
                    'Orphanet_1652', 'EFO_1001248', 'EFO_0007185', 'EFO_1000956', 'EFO_1001346', 'EFO_0005240',
                    'EFO_0000279', 'EFO_0003876', 'Orphanet_528', 'HP_0002745', 'EFO_0005584', 'EFO_0007153',
                    'EFO_1000785', 'Orphanet_740', 'Orphanet_902', 'EFO_0004228', 'Orphanet_79277', 'EFO_0007326',
                    'EFO_0000640', 'Orphanet_817', 'Orphanet_183663', 'EFO_0005252', 'EFO_0005570', 'EFO_0007415',
                    'EFO_0005576', 'EFO_0004616', 'EFO_0007446', 'EFO_1000045', 'Orphanet_910', 'EFO_1000566',
                    'Orphanet_881', 'EFO_0000763', 'Orphanet_96321', 'EFO_1000879', 'Orphanet_182098', 'EFO_1000842',
                    'EFO_0004282', 'EFO_0007245', 'EFO_1000233', 'Orphanet_391665', 'Orphanet_54260', 'EFO_0007391',
                    'Orphanet_136', 'EFO_0003901', 'EFO_0007457', 'EFO_0004540', 'EFO_0005532', 'EFO_0005846',
                    'EFO_0007347', 'EFO_0006918', 'EFO_0003075', 'HP_0000103', 'EFO_1001312', 'EFO_0005296',
                    'Orphanet_3388', 'Orphanet_2573', 'EFO_0005803', 'EFO_1000975', 'Orphanet_273', 'EFO_0007305',
                    'Orphanet_277', 'EFO_1000948', 'EFO_1000254', 'Orphanet_101090', 'EFO_0002916', 'EFO_1000054',
                    'Orphanet_540', 'HP_0000483', 'Orphanet_324', 'HP_0011868', 'EFO_0000653', 'EFO_0004138',
                    'Orphanet_319605', 'HP_0000639', 'EFO_0004710', 'HP_0001657', 'EFO_0005224', 'EFO_0004895',
                    'EFO_0003097', 'EFO_0007229', 'Orphanet_792', 'EFO_0007330', 'EFO_0003891', 'Orphanet_183666',
                    'Orphanet_268', 'Orphanet_244', 'EFO_0006861', 'Orphanet_3342', 'EFO_1000209', 'EFO_0000217',
                    'EFO_1000885', 'EFO_1001476', 'EFO_0003952', 'Orphanet_846', 'EFO_0004340', 'EFO_0006513',
                    'Orphanet_79211', 'Orphanet_739', 'EFO_1000073', 'EFO_1000418', 'EFO_1001309']

        fields = ['label', 'code']
        response = self._make_request('/api/latest/private/disease',
                                      data=json.dumps(
                                          {'diseases': diseases, 'facets': 'true', 'path_label': 'autoimmune disease',
                                           'fields': fields}),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        sig_labels = [bucket['key'] for bucket in json_response['facets']['significantTherapeuticAreas']['buckets']]
        print 'Groups of related diseases {}'.format(sig_labels)
        print 'Related Diseases  - after selecting specific path_label {}'.format(json_response['data'])
        self.assertGreater(len(json_response['data']), 0)
        self.assertGreater(len(sig_labels), 0)

    def testPostEFOwithRelations(self):

        disease = 'EFO_0001365'
        related_diseases_res = self._make_request('/api/latest/private/relation/disease/' + disease,
                                                  data={'size':1000},
                                                  token=self._AUTO_GET_TOKEN)
        json_response = json.loads(related_diseases_res.data.decode('utf-8'))
        related_diseases = [ d['object']['id'] for d in json_response['data']]
        print 'Related Diseases {}'.format(related_diseases)
        fields = ['label','code']
        response = self._make_request('/api/latest/private/disease',
                                        data = json.dumps({'diseases': related_diseases,'facets': 'true','fields':fields,'size':0}),
                                        content_type = 'application/json',
                                        method = 'POST',
                                        token = self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)

        json_response = json.loads(response.data.decode('utf-8'))
        sig_labels =[bucket['key'] for bucket in json_response['facets']['significantTherapeuticAreas']['buckets']]
        print 'Groups of related diseases {}'.format(sig_labels)
        print 'Related Diseases with labels {}'.format(json_response['data'])
        self.assertEqual(len(json_response['data']), 0)
        self.assertGreater(len(sig_labels), 0)
        print json_response


    def testPostEFORelationsWithLabelFiltering(self):

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
        self.assertGreater(len(json_response['data']), 0)
        self.assertGreater(len(sig_labels), 0)


if __name__ == "__main__":
     unittest.main()