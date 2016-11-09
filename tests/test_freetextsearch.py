import json
import unittest
from tests import GenericTestCase

GENE_SYMBOL_LIST = ['A1BG',
                   'A1CF',
                   'A2M',
                   'A2ML1',
                   'A3GALT2',
                   'A4GALT',
                   'A4GNT',
                   'AAAS',
                   'AACS',
                   'AADAC',
                   'AADACL2',
                   'AADACL3',
                   'AADACL4',
                   'AADAT',
                   'AAED1',
                   'AAGAB',
                   'AAK1',
                   'AAMDC',
                   'AAMP',
                   'AANAT',
                   'AAR2',
                   'AARD',
                   'AARS',
                   'AARS2',
                   'AARSD1',
                   'AASDH',
                   'AASDHPPT',
                   'AASS',
                   'AATF',
                   'AATK',
                   'ABAT',
                   'ABCA1',
                   'ABCA2',
                   'ABCA3',
                   'ABCA4',
                   'ABCA5',
                   'ABCA6',
                   'ABCA7',
                   'ABCA8',
                   'ABCA9',
                   'ABCA10',
                   'ABCA12',
                   'ABCA13',
                   'ABCB1',
                   'ABCB4',
                   'ABCB5',
                   'ABCB6',
                   'ABCB7',
                   'ABCB8',
                   'ABCB9',
                   'ABCB10',
                   'ABCB11',
                   'ABCC1',
                   'ABCC2',
                   'ABCC3',
                   'ABCC4',
                   'ABCC5',
                   'ABCC6',
                   'ABCC8',
                   'ABCC9',
                   'ABCC10',
                   'ABCC11',
                   'ABCC12',
                   'ABCD1',
                   'ABCD2',
                   'ABCD3',
                   'ABCD4',
                   'ABCE1',
                   'ABCF1',
                   'ABCF2',
                   'ABCF3',
                   'ABCG1',
                   'ABCG2',
                   'ABCG4',
                   'ABCG5',
                   'ABCG8',
                   'ABHD1',
                   'ABHD2',
                   'ABHD3',
                   'ABHD4',
                   'ABHD5',
                   'ABHD6',
                   'ABHD8',
                   'ABHD10',
                   'ABHD11',
                   'ABHD12',
                   'ABHD12B',
                   'ABHD13',
                   'ABHD14A',
                   'ABHD14B',
                   'ABHD15',
                   'ABHD16A',
                   'ABHD16B',
                   'ABHD17A',
                   'ABHD17B',
                   'ABHD17C',
                   'ABHD18',
                   'ABI1',
                   'ABI2',
                   'ABI3',
                   'ABI3BP',
                   'ABL1',
                   'ABL2',
                   'ABLIM1',
                   'ABLIM2',
                   'ABLIM3',
                   'ABO',
                   'ABR',
                   'ABRA',
                   'ABRACL',
                   'ABT1',
                   'ABTB1',
                   'ABTB2',
                   'ACAA1',
                   'ACAA2',
                   'ACACA',
                   'ACACB',
                   'ACAD8',
                   'ACAD9',
                   'ACAD10',
                   'ACAD11',
                   'ACADL',
                   'ACADM',
                   'ACADS',
                   'ACADSB',
                   'ACADVL',
                   'ACAN',
                   'ACAP1',
                   'ACAP2',
                   'ACAP3',
                   'ACAT1',
                   'ACAT2',
                   'ACBD3',
                   'ACBD4',
                   'ACBD5',
                   'ACBD6',
                   'ACBD7',
                   'ACCS',
                   'ACCSL',
                   'ACD',
                   'ACE',
                   'ACE2',
                   'ACER1',
                   'ACER2',
                   'ACER3',
                   'ACHE',
                   'ACIN1',
                   'ACKR1',
                   'ACKR2',
                   'ACKR3',
                   'ACKR4',
                   'ACLY',
                   'ACMSD',
                   'ACO1',
                   'ACO2',
                   'ACOD1',
                   'ACOT1',
                   'ACOT2',
                   'ACOT4',
                   'ACOT6',
                   'ACOT7',
                   'ACOT8',
                   'ACOT9',
                   'ACOT11',
                   'ACOT12',
                   'ACOT13',
                   'ACOX1',
                   'ACOX2',
                   'ACOX3',
                   'ACOXL',
                   'ACP1',
                   'ACP2',
                   'ACP5',
                   'ACP6',
                   'ACP7',
                   'ACPP',
                   'ACPT',
                   'ACR',
                   'ACRBP',
                   'ACRV1',
                   'ACSBG1',
                   'ACSBG2',
                   'ACSF2',
                   'ACSF3',
                   'ACSL1',
                   'ACSL3',
                   'ACSL4',
                   'ACSL5',
                   'ACSL6',
                   'ACSM1',
                   'ACSM2A',
                   'ACSM2B',
                   'ACSM3',
                   'ACSM4',
                   'ACSM5',
                   'ACSM6',
                   'ACSS1',
                   'ACSS2',
                   'ACSS3',
                   'ACTA1',
                   'ACTA2',
                   'ACTB',
                   'ACTBL2',
                   'ACTC1',
                   'ACTG1',
                   'ACTG2',
                   'ACTL6A',
                   'ACTL6B',
                   'ACTL7A',
                   'ACTL7B',
                   'ACTL8',
                   'ACTL9',
                   'ACTL10',
                   'ACTN1',
                   'ACTN2',
                   'ACTN3',
                   'ACTN4',
                   'ACTR1A',
                   'ACTR1B',
                   'ACTR2',
                   'ACTR3',
                   'ACTR3B',
                   'ACTR3C',
                   'ACTR5',
                   'ACTR6',
                   'ACTR8',
                   'ACTR10',
                   'ACTRT1',
                   'ACTRT2',
                   'ACTRT3',
                   'ACVR1',
                   'ACVR1B',
                   'ACVR1C',
                   'ACVR2A',
                   'ACVR2B',
                   'ACVRL1',
                   'ACY1',
                   'ACY3',
                   'ACYP1',
                   'ACYP2',
                   'ADA',
                   'ADAD1',
                   'ADAD2',
                   'ADAL',
                   'ADAM2',
                   'ADAM7',
                   'ADAM8',
                   'ADAM9',
                   'ADAM10',
                   'ADAM11',
                   'ADAM12',
                   'ADAM15',
                   'ADAM17',
                   'ADAM18',
                   'ADAM19',
                   'ADAM20',
                   'ADAM21',
                   'ADAM22',
                   'ADAM23',
                   'ADAM28',
                   'ADAM29',
                   'ADAM30',
                   'ADAM32',
                   'ADAM33',
                   'ADAMDEC1',
                   'ADAMTS1',
                   'ADAMTS2',
                   'ADAMTS3',
                   'ADAMTS4',
                   'ADAMTS5',
                   'ADAMTS6',
                   'ADAMTS7',
                   'ADAMTS8',
                   'ADAMTS9',
                   'ADAMTS10',
                   'ADAMTS12',
                   'ADAMTS13',
                   'ADAMTS14',
                   'ADAMTS15',
                   'ADAMTS16',
                   'ADAMTS17',
                   'ADAMTS18',
                   'ADAMTS19',
                   'ADAMTS20',
                   'ADAMTSL1',
                   'ADAMTSL2',
                   'ADAMTSL3',
                   'ADAMTSL4',
                   'ADAMTSL5',
                   'ADAP1',
                   'ADAP2',
                   'ADAR',
                   'ADARB1',
                   'ADARB2',
                   'ADAT1',
                   'ADAT2',
                   'ADAT3',
                   'ADCK1',
                   'ADCK2',
                   'ADCK5',
                   'ADCY1',
                   'ADCY2',
                   'ADCY3',
                   'ADCY4',
                   'ADCY5',
                   'ADCY6',
                   'ADCY7',
                   'ADCY8',
                   'ADCY9',
                   'ADCY10',
                   'ADCYAP1',
                   'ADCYAP1R1',
                   'ADD1',
                   'ADD2',
                   'ADD3',
                   'ADGB',
                   'ADGRA1',
                   'ADGRA2',
                   'ADGRA3',
                   'ADGRB1',
                   'ADGRB2',
                   'ADGRB3',
                   'ADGRD1',
                   'ADGRD2',
                   'ADGRE1',
                   'ADGRE2',
                   'ADGRE3',
                   'ADGRE5',
                   'ADGRF1',
                   'ADGRF2',
                   'ADGRF3',
                   'ADGRF4',
                   'ADGRF5',
                   'ADGRG1',
                   'ADGRG2',
                   'ADGRG3',
                   'ADGRG4',
                   'ADGRG5',
                   'ADGRG6',
                   'ADGRG7',
                   'ADGRL1',
                   'ADGRL2',
                   'ADGRL3',
                   'ADGRL4',
                   'ADGRV1',
                   'ADH1A',
                   'ADH1B',
                   'ADH1C',
                   'ADH4',
                   'ADH5',
                   'ADH6',
                   'ADH7',
                   'ADHFE1',
                   'ADI1',
                   'ADIG',
                   'ADIPOQ',
                   'ADIPOR1',
                   'ADIPOR2',
                   'ADIRF',
                   'ADK',
                   'ADM',
                   'ADM2',
                   'ADM5',
                   'ADNP',
                   'ADNP2',
                   'ADO',
                   'ADORA1',
                   'ADORA2A',
                   'ADORA2B',
                   'ADORA3',
                   'ADPGK',
                   'ADPRH',
                   'ADPRHL1',
                   'ADPRHL2',
                   'ADPRM',
                   'ADRA1A',
                   'ADRA1B',
                   'ADRA1D',
                   'ADRA2A',
                   'ADRA2B',
                   'ADRA2C',
                   'ADRB1',
                   'ADRB2',
                   'ADRB3',
                   'ADRM1',
                   'ADSL',
                   'ADSS',
                   'ADSSL1',
                   'ADTRP',
                   'AEBP1',
                   'AEBP2',
                   'AEN',
                   'AES',
                   'AFAP1',
                   'AFAP1L1',
                   'AFAP1L2',
                   'AFDN',
                   'AFF1',
                   'AFF2',
                   'AFF3',
                   'AFF4',
                   'AFG3L2',
                   'AFM',
                   'AFMID',
                   'AFP',
                   'AFTPH',
                   'AGA',
                   'AGAP1',
                   'AGAP2',
                   'AGAP3',
                   'AGAP4',
                   'AGAP5',
                   'AGAP6',
                   'AGAP9',
                   'AGBL1',
                   'AGBL2',
                   'AGBL3',
                   'AGBL4',
                   'AGBL5',
                   'AGER',
                   'AGFG1',
                   'AGFG2',
                   'AGGF1',
                   'AGK',
                   'AGL',
                   'AGMAT',
                   'AGMO',
                   'AGO1',
                   'AGO2',
                   'AGO3',
                   'AGO4',
                   'AGPAT1',
                   'AGPAT2',
                   'AGPAT3',
                   'AGPAT4',
                   'AGPAT5',
                   'AGPS',
                   'AGR2',
                   'AGR3',
                   'AGRN',
                   'AGRP',
                   'AGT',
                   'AGTPBP1',
                   'AGTR1',
                   'AGTR2',
                   'AGTRAP',
                   'AGXT',
                   'AGXT2',
                   'AHCTF1',
                   'AHCY',
                   'AHCYL1',
                   'AHCYL2',
                   'AHDC1',
                   'AHI1',
                   'AHNAK',
                   'AHNAK2',
                   'AHR',
                   'AHRR',
                   'AHSA1',
                   'AHSA2',
                   'AHSG',
                   'AHSP',
                   'AICDA',
                   'AIDA',
                   'AIF1',
                   'AIF1L',
                   'AIFM1',
                   'AIFM2',
                   'AIFM3',
                   'AIG1',
                   'AIM1',
                   'AIM1L',
                   'AIM2',
                   'AIMP1',
                   'AIMP2',
                   'AIP',
                   'AIPL1',
                   'AIRE',
                   'AJAP1',
                   'AJUBA',
                   'AK1',
                   'AK2',
                   'AK3',
                   'AK4',
                   'AK5',
                   'AK6',
                   'AK7',
                   'AK8',
                   'AK9',
                   'AKAIN1',
                   'AKAP1',
                   'AKAP2',
                   'AKAP3',
                   'AKAP4',
                   'AKAP5',
                   'AKAP6',
                   'AKAP7',
                   'AKAP8',
                   'AKAP8L',
                   'AKAP9']

class FreeTextSearchTestCase(GenericTestCase):


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

    #@unittest.skip("testBraf")
    def testBraf(self):

        response= self._make_request('/api/latest/public/search',
                                     data={'q':'braf'},
                                     token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self._assert_search_result(json_response,
                                   'BRAF',
                                   'B-Raf proto-oncogene, serine/threonine kinase',
                                   'Protein kinase involved in the transduction of mitogenic signals from the cell membrane to the nucleus. May play a role in the postsynaptic responses of hippocampal neuron. Phosphorylates MAP2K1, and thereby contributes to the MAP kinase signal transduction pathway.',
                                   680)
        
    #@unittest.skip("testSearchFields")
    def testSearchFields(self):

        response= self._make_request('/api/latest/public/search',
                                     data={'q':'braf', 'fields':['id', 'approved_symbol'], 'size':1},
                                     token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(json_response['data']), 1)
        self.assertEqual(json_response['data'][0]['highlight'], '')
        self.assertEqual(json_response['data'][0]['id'], 'ENSG00000157764')
        
        first_result = json_response['data'][0]['data']
        self.assertEqual(len(first_result), 2)
        self.assertEqual(first_result['approved_symbol'], 'BRAF')
        self.assertEqual(first_result['id'], 'ENSG00000157764')
        

    
    #@unittest.skip("testSearchFieldsWithHighlight")
    def testSearchFieldsWithHighlight(self):

        response= self._make_request('/api/latest/public/search',
                                     data={'q':'braf', 'fields':['id', 'approved_symbol', 'highlight']},
                                     token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['data'][0]['highlight'] is not '')
        theHighlight = json_response['data'][0]['highlight']
        
        self.assertEqual(len(theHighlight), 11)
        
        self.assertEqual(json_response['data'][0]['id'], 'ENSG00000157764')
        
        first_result = json_response['data'][0]['data']
        self.assertEqual(len(first_result), 2)
        self.assertEqual(first_result['approved_symbol'], 'BRAF')
        self.assertEqual(first_result['id'], 'ENSG00000157764')
        
    #@unittest.skip("testBestHitSearchFieldsNoFilter")    
    def testBestHitSearchFieldsNoFilter(self):
        response= self._make_request('/api/latest/private/besthitsearch',
                                    data={'q':['braf', 'nr3c1', 'Rpl18a', 'rippa', 'ENSG00000157764', 'eff']},                                  
                                    token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        
        self.assertEqual(len(json_response['data']), 6)
         
        braf_data = json_response['data'][0]
        # self.assertEqual( braf_data['highlight'], '')
        self.assertEqual( braf_data['id'], 'ENSG00000157764')
        self.assertEqual(braf_data['q'], 'braf')
 
        first_result_braf =braf_data['data']
        self.assertNotEqual(len(first_result_braf), 2) #should have more fields since we are not restricting
        self.assertEqual(first_result_braf['approved_symbol'], 'BRAF')
        self.assertEqual(first_result_braf['id'], 'ENSG00000157764')
         
        nr3c1_data = json_response['data'][1]
        # self.assertEqual( nr3c1_data['highlight'], '')
        self.assertEqual( nr3c1_data['id'], 'ENSG00000113580')
         
        first_result_nr3c1 =nr3c1_data['data']
        self.assertNotEqual(len(first_result_nr3c1), 2)
        self.assertEqual(first_result_nr3c1['approved_symbol'], 'NR3C1')
        self.assertEqual(first_result_nr3c1['id'], 'ENSG00000113580')
         
        #test fuzzy result
        fuzzy_result = json_response['data'][2]
        self.assertEqual(fuzzy_result['q'], 'Rpl18a')
        fuzzy_result_data = fuzzy_result['data']
        self.assertNotEqual(fuzzy_result_data['approved_symbol'], 'RPL18A')
 
        #test empty result
        empty_result = json_response['data'][3]
        self.assertEqual(empty_result['q'], 'rippa')
        self.assertEqual(empty_result['id'], None)
         
        #test  when query is ENS ID
        ens_data = json_response['data'][4]
        # self.assertEqual( ens_data['highlight'], '')
        self.assertEqual( ens_data['id'], 'ENSG00000157764')
        self.assertEqual(ens_data['q'], 'ENSG00000157764')
 
        first_result_ens =ens_data['data']
        self.assertNotEqual(len(first_result_ens), 2)
        self.assertEqual(first_result_ens['approved_symbol'], 'BRAF')
        self.assertEqual(first_result_ens['id'], 'ENSG00000157764')
        
        #test eff which can be desease or target depending on how search is done
        eff_data = json_response['data'][5]
        self.assertEqual(eff_data['q'], 'eff')
        self.assertEqual(eff_data['exact'], False)
        self.assertGreaterEqual(len(eff_data['data']),15) #no restrictions on returned fields
        

    #@unittest.skip(" testBestHitSearchFieldsTarget")
    def testBestHitSearchFieldsTarget(self):
        response= self._make_request('/api/latest/private/besthitsearch',
                                    data={'q':['braf', 'nr3c1', 'Rpl18a', 'rippa', 'ENSG00000157764', 'eff'],
                                           'filter':'target'},
                                    token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        
        self.assertEqual(len(json_response['data']),6)
        
        braf_data = json_response['data'][0]
        # self.assertEqual( braf_data['highlight'], '')
        self.assertEqual( braf_data['id'], 'ENSG00000157764')
        self.assertEqual( braf_data['q'], 'braf')
        self.assertEqual( braf_data['exact'], True)

        first_result_braf =braf_data['data']
        self.assertEqual(first_result_braf['approved_symbol'], 'BRAF')

        nr3c1_data = json_response['data'][1]
        # self.assertEqual( nr3c1_data['highlight'], '')
        self.assertEqual( nr3c1_data['id'], 'ENSG00000113580')
        self.assertEqual( nr3c1_data['exact'], True)
        
        first_result_nr3c1 =nr3c1_data['data']
        self.assertEqual(len(first_result_nr3c1), 1)
        self.assertEqual(first_result_nr3c1['approved_symbol'], 'NR3C1')

        #test fuzzy result
        fuzzy_result = json_response['data'][2]
        self.assertEqual(fuzzy_result['q'], 'Rpl18a')
        fuzzy_result_data = fuzzy_result['data']
        self.assertNotEqual(fuzzy_result_data['approved_symbol'], 'RPL18A')

        #test empty result
        empty_result = json_response['data'][3]
        self.assertEqual(empty_result['q'], 'rippa')
        self.assertEqual(empty_result['id'], None)
        
        #test  when query is ENS ID
        ens_data = json_response['data'][4]
        # self.assertEqual( ens_data['highlight'], '')
        self.assertEqual( ens_data['id'], 'ENSG00000157764')
        self.assertEqual( ens_data['q'], 'ENSG00000157764')
        self.assertEqual( ens_data['exact'], True)

        first_result_ens =ens_data['data']
        self.assertEqual(len(first_result_ens), 1)
        self.assertEqual(first_result_ens['approved_symbol'], 'BRAF')

        eff_data = json_response['data'][5]
        self.assertEqual(eff_data['q'], 'eff')
        self.assertEqual(eff_data['exact'], False)
        self.assertEqual(len(eff_data['data']),1) #should only get name and id
        self.assertEqual(eff_data['data']['approved_symbol'],'UBE2D3')
          
    
        
    #@unittest.skip(" testBestHitSearchFieldsDisease")
    def testBestHitSearchFieldsDisease(self):
        response= self._make_request('/api/latest/private/besthitsearch',
                                    data={'q':['braf', 'nr3c1', 'Rpl18a', 'rippa', 'ENSG00000157764', 'eff'], 'filter':'disease'},
                                    token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        
        self.assertEqual(len(json_response['data']), 6)
        
        braf_data = json_response['data'][0]#should get nothing for target when searching for diseases
        self.assertEqual( braf_data['id'], None)
        self.assertEqual(braf_data['q'], 'braf')

        nr3c1_data = json_response['data'][1]
        self.assertEqual(nr3c1_data['q'], 'nr3c1')
        self.assertEqual( nr3c1_data['id'], None)
        
        #test fuzzy result
        fuzzy_result = json_response['data'][2]
        self.assertEqual(fuzzy_result['q'], 'Rpl18a')
        self.assertEqual( fuzzy_result['id'], None)

        #test empty result
        empty_result = json_response['data'][3]
        self.assertEqual(empty_result['q'], 'rippa') #good there is not a disease with my name! ;-)
        self.assertEqual(empty_result['id'], None)
        
        #test  when query is ENS ID
        ens_data = json_response['data'][4]
        self.assertEqual( ens_data['id'], None)
        self.assertEqual( ens_data['q'], 'ENSG00000157764')
        
        #test eff which can be desease or target depending on how search is done
        eff_data = json_response['data'][5]
        self.assertEqual(eff_data['q'], 'eff')
        self.assertEqual(eff_data['exact'], False)
        # self.assertEqual(len(eff_data['data']),2) #should only get name and id
        self.assertEqual(eff_data['data']['name'],'insulin resistance')
        
    
    ##@unittest.skip("testBestHitSearchFieldsPostTarget")    
    def testBestHitSearchFieldsPostTarget(self):
        
        #passing some dummy fields 'fields':['field1', 'field2'] just to show 
        #that they are going to be overwritten and data will have only two
        # fields: approved_symbol and id
        response= self._make_request('/api/latest/private/besthitsearch',
                                     data=json.dumps({
                                            'q':['braf', 'nr3c1', 'Rpl18a', 'rippa', 'ENSG00000157764', 'eff'], 
                                            'fields':['field1', 'field2'], 
                                            'filter':'target'}),
                                     content_type='application/json',
                                     method='POST',
                                     token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        
        self.assertEqual(len(json_response['data']), 6)
        
        braf_data = json_response['data'][0]
        # self.assertEqual( braf_data['highlight'], '')
        self.assertEqual( braf_data['id'], 'ENSG00000157764')
        self.assertEqual( braf_data['exact'], True)
        
        first_result_braf =braf_data['data']
        self.assertEqual(len(first_result_braf), 1)
        self.assertEqual(first_result_braf['approved_symbol'], 'BRAF')
        
        
        nr3c1_data = json_response['data'][1]
        # self.assertEqual( nr3c1_data['highlight'], '')
        self.assertEqual( nr3c1_data['id'], 'ENSG00000113580')
        self.assertEqual( nr3c1_data['exact'], True)

        first_result_nr3c1 =nr3c1_data['data']
        self.assertEqual(len(first_result_nr3c1), 1)
        self.assertEqual(first_result_nr3c1['approved_symbol'], 'NR3C1')
        
        
        #test fuzzy result
        fuzzy_result = json_response['data'][2]
        self.assertEqual(fuzzy_result['q'], 'Rpl18a')
        self.assertEqual(fuzzy_result['exact'], False)

        fuzzy_result_data = fuzzy_result['data']
        self.assertNotEqual(fuzzy_result_data['approved_symbol'], 'RPL18A')


        #test empty result
        empty_result = json_response['data'][3]
        self.assertEqual(empty_result['q'], 'rippa')
        self.assertEqual(empty_result['id'], None)
        
        #test  when query is ENS ID
        ens_data = json_response['data'][4]
        # self.assertEqual( ens_data['highlight'], '')
        self.assertEqual( ens_data['id'], 'ENSG00000157764')
        self.assertEqual( ens_data['q'], 'ENSG00000157764')
        self.assertEqual( ens_data['exact'], True)
        
        first_result_ens =ens_data['data']
        self.assertEqual(len(first_result_ens), 1)
        self.assertEqual(first_result_ens['approved_symbol'], 'BRAF')
    
        
        eff_data = json_response['data'][5]
        self.assertEqual(eff_data['q'], 'eff')
        self.assertEqual(eff_data['exact'], False)
        self.assertEqual(len(eff_data['data']),1) #should only get name and id
        self.assertEqual(eff_data['data']['approved_symbol'],'UBE2D3')

    def testBestHitSearchExactMatchManyTargetPost(self):
        targets = GENE_SYMBOL_LIST
        response = self._make_request('/api/latest/private/besthitsearch',
                                      data=json.dumps({
                                          'q': targets,
                                          'filter': 'target',
                                          'no_cache': True}),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))

        self.assertEqual(len(json_response['data']), len(targets))

        for result in json_response['data']:
            self.assertIsNotNone(result)


    #@unittest.skip("testAsthma")
    def testAsthma(self):
        response= self._make_request('/api/latest/public/search',
                                     data={'q':'asthma'},
                                     token=self._AUTO_GET_TOKEN)

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
        self.assertIsNotNone(json_response['data']['besthit'])
        first_result = json_response['data']['besthit']['data']
        self.assertEqual(first_result['name'], name)
        if full_name is not None:
            self.assertEqual(first_result['full_name'], full_name)
        if description is not None:
            self.assertEqual(first_result['description'], description)
        self.assertGreaterEqual(first_result['association_counts']['total'], min_association_number)

    #@unittest.skip("testQuickSearchBraf")
    def testQuickSearchBraf(self):
        response= self._make_request('/api/latest/private/quicksearch',
                                     data={'q':'braf'},
                                     token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self._assert_quicksearch_result(json_response,
                                   'BRAF',
                                   'B-Raf proto-oncogene, serine/threonine kinase',
                                   'Protein kinase involved in the transduction of mitogenic signals from the cell'
                                   ' membrane to the nucleus. May play a role in the postsynaptic responses of '
                                   'hippocampal neuron. Phosphorylates MAP2K1, and thereby contributes to the MAP '
                                   'kinase signal transduction pathway.',
                                   680)

    #@unittest.skip("testQuickSearchBrafOrtholog")
    def testQuickSearchBrafOrtholog(self):
        '''lin-45 is a braf ortholog in c.elegans'''
        response= self._make_request('/api/latest/private/quicksearch',
                                     data={'q':'lin-45'},
                                     token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self._assert_quicksearch_result(json_response,
                                   'BRAF',
                                   'B-Raf proto-oncogene, serine/threonine kinase',
                                   'Protein kinase involved in the transduction of mitogenic signals from the cell'
                                   ' membrane to the nucleus. May play a role in the postsynaptic responses of '
                                   'hippocampal neuron. Phosphorylates MAP2K1, and thereby contributes to the MAP '
                                   'kinase signal transduction pathway.',
                                   680)

    #@unittest.skip("testQuickSearchBrafOrtholog_misp")
    def testQuickSearchBrafOrtholog_misp(self):
        '''lin-45 is a braf ortholog in c.elegans, but 50% percent of people willuse lin45
        '''
        response= self._make_request('/api/latest/private/quicksearch',
                                     data={'q':'lin-45'},
                                     token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self._assert_quicksearch_result(json_response,
                                   'BRAF',
                                   'B-Raf proto-oncogene, serine/threonine kinase',
                                   'Protein kinase involved in the transduction of mitogenic signals from the cell'
                                   ' membrane to the nucleus. May play a role in the postsynaptic responses of '
                                   'hippocampal neuron. Phosphorylates MAP2K1, and thereby contributes to the MAP '
                                   'kinase signal transduction pathway.',
                                   680)
        
        
    #@unittest.skip("testQuickSearchAsthma")
    def testQuickSearchAsthma(self):

        response= self._make_request('/api/latest/private/quicksearch',
                                     data={'q':'asthma'},
                                     token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self._assert_quicksearch_result(json_response,
                                   'asthma',
                                   'asthma',
                                   "A bronchial disease that is characterized by chronic inflammation and narrowing of "
                                   "the airways, which is caused by a combination of environmental and genetic factors "
                                   "resulting in recurring periods of wheezing (a whistling sound while breathing), "
                                   "chest tightness, shortness of breath, mucus production and coughing. The symptoms "
                                   "appear due to a variety of triggers such as allergens, irritants, respiratory "
                                   "infections, weather changes, excercise, stress, reflux disease, medications, "
                                   "foods and emotional anxiety.",
                                   2086)

    #@unittest.skip("testQuickSearchCancer")
    def testQuickSearchCancer(self):

        response = self._make_request('/api/latest/private/quicksearch',
                                      data={'q': 'cancer'},
                                      token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self._assert_quicksearch_result(json_response,
                                        'cancer',
                                        'cancer',
                                        "A malignant neoplasm in which new abnormal tissue grow by excessive cellular "
                                        "division and proliferation more rapidly than normal and continues to grow "
                                        "after the stimuli that initiated the new growth cease.",
                                        20000)
    
    @unittest.skip("testAutocomplete")
    def testAutocomplete(self):
        response= self._make_request('/api/latest/private/autocomplete',
                                     data={'q':'ast'},
                                     token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        print json_response




if __name__ == "__main__":
     unittest.main()
