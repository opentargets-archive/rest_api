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


TEST_MART_410='''rnu6-280p
y_rna
rp11-222g7.2
clostridiales-1
rp11-654c22.2
rp11-315f22.1
rp11-399e6.1
abba01000934.1
rnu1-62p
ac093802.1
rp11-654c22.1
rp11-399e6.2
dppa2p2
sertad4-as1
rna5sp136
rp11-399e6.4
rybp
foxo6
inpp5d
obp2b
sertad4
slc16a1
st13p19
rp4-667h12.4
lcn1p1
akr7a2p1
rp11-31f15.2
lcn1p2
kat6b
hhat
surf6
rps6ka1
ndufa10
rp11-380j14.1
rp11-380j14.4
znf445
padi1
med22
rnu5a-8p
rp5-879k22.1
znf852
padi3
rn7sl32p
ei24p3
rp11-944l7.6
mir3972
padi4
rp11-244n20.7
mir1976
rn7sl679p
zkscan7
rnu7-29p
rp11-492m19.3
snou13
ac004824.2
rp4-785j1.1
rpl7a
padi6
rp11-77g23.2
rp1-20b21.4
rcc2
snord24
snord36b
snord36a
snord36c
rp11-944l7.4
znf660
mpripp1
surf1
atg16l1
znf197
surf2
znf197-as1
znf35
surf4
rp11-348p10.2
socs5p3
znf502
znf501
kiaa1143
stkld1
rexo4
scarna5
scarna6
kif15
sag
rp11-400n9.1
tmem42
tgm4
dgkd
adamts13
rp11-272d20.2
zdhhc3
cacfd1
slc2a6
abo
bcl7a
ac156455.1
rp5-845o24.8
ctbp2p1
rp11-341d18.2
abc13-47488600e17.1
nalcn-as1
pramef11
linc00411
fam230c
al356585.2
ggt4p
mlxip
rp11-341d18.5
pramef30p
setd8p1
hnrnpcl1
rp11-341d18.6
bcl2l14
rasa3
pramef2
pramef4
pramef10
rasa3-it1
pramef7
rnu6-1072p
pramef29p
ac156455.2
igkv5-2
pramef6
rp11-267j23.4
mir1244-4
foxr1
pramef28p
pramef27
metazoa_srp
rp11-110i1.12
pramef25
lrp6
hnrnpcl3
pramef34p
pramef35p
ccdc84
hnrnpcl2
pramef36p
rp13-221m14.2
pramef26
hnrnpcl4
pramef9
pramef13
pramef18
pramef31p
rpl23ap64
rp11-110i1.11
pramef5
rp11-110i1.5
pramef32p
rnu6-771p
rp11-77g23.5
rps25
pramef8
rp11-267j23.1
dupd1
rnu6-545p
rp11-757g14.3
rnu6-318p
mansc1
pramef15
rpl23ap66
loh12cr2
pramef33p
borcs5
pramef19
rp11-253i19.4
dusp16
trappc4
rp11-253i19.3
rp11-158n24.1
rp11-110i1.6
leutx
llnlr-268e12.1
dyrk1b
mir6719
hyou1
fbl
prr13p5
psmc4
znf546
ctc-471f3.5
znf780b
ac005614.5
rp11-110i1.14
rp11-110i1.13
znf780a
vps11
ac005614.3
fcgbp
hmbs
slc37a4
atad1
cfl1p1
ctif
rn7sl78p
rp11-380g5.2
ndufb11p1
rp11-380g5.3
rp1-91n13.1
snord74
med6p1
klln
af146191.4
pten
frg1
fat3
rp11-426j5.3
mir4743
rp11-426j5.2
rp11-46d1.2
rp11-484l8.1
pgam1p9
rp11-675m1.2
map4k1
igkv7-3
pgbd4p5
dpp6
igkv2-4
igkv1-5
igkv1-6
igkv3-7
igkv1-8
igkv1-9
igkv2-10
igkv3-11
igkv1-12
igkv1-13
igkv2-14
igkv3-15
igkv1-16
igkv1-17
igkv2-18
igkv2-19
igkv3-20
igkv6-21
igkv1-22
igkv2-23
igkv2-24
igkv3-25
igkv2-26
rp11-421k23.1
igkv1-27
ibtk
igkv2-28
igkv2-29
magi1
igkv2-30
igkv3-31
igkv1-32
igkv1-33
igkv3-34
igkv1-35
igkv2-36
igkv1-37
igkv2-38
igkv1-39
igkv2-40
ac245015.1
ctb-186g2.1
eif3k
rnu6-130p
rp3-492p14.2
tpbg
actn4
slc25a26
rnu6-787p
rn7sl482p
ctb-186g2.4
ctd-2540f13.2
lgals7b
lgals7
rnu6-140p
lgals4
lrig1
ech1
ac104534.3
ac104534.2
hnrnpl
ac008982.2
rinl
ctc-360g5.6
sirt2
nfkbib
ccer2
sars2
ctc-360g5.8
mrps12
ctc-360g5.9
fbxo17
fbxo27
capn12
rp11-143j24.1
ctd-2022h16.3
ctd-2022h16.1
rn7sl673p
dnm1p28
ulk4p3
u8
rn7sl469p
dnm1p30
mgat4c
rp11-932o9.3
dkfzp434l187
rnu6-409p
rp11-261b23.1
rp11-35j10.5
rnu6-17p
rp11-811j10.1
rp11-624a21.1
rp11-494m8.4
rp11-932o9.10
acr
muc6
rp11-932o9.7
rp11-932o9.9
rp11-494m8.1
rn7sl628p
rp11-932o9.8
or5p2
or5p3
ulk4p2
or5e1p
rnu6-943p
ac002056.5
or10a6
ac002056.3
rp13-870h17.3
or10a3
dnm1p50
nlrp10
rpl23ap82
rp11-202h2.1
golga8q
rp11-324h9.1
muc5ac
mllt10p2
ac255361.1
eif3f
af146191.8
rn7sl796p
tubb7p
ac026150.8
rna5sp174
rp11-632k20.2
rna5sp175
dux4l9
rp11-382b18.5
rarres2p4
rn7sl286p
dux4l8
rpl23ap84
abc7-42391500h16.4
ct476828.22
ndufa6
ct476828.15
ct476828.8
ct476828.7
ct476828.4
ct476828.2
ct476828.10
ct476828.16
ct476828.3
ct476828.23
ct476828.24
scg5
ct476828.14
rp1-257i20.14
ct476828.5
ola1p1
rp4-669p10.16
rp4-669p10.20
cyp2d8p
tcf20
rp11-1000b6.2
rp11-758n13.1
ac254560.1
grem1
golga8j
ac254952.1
arhgap11b
golga8n
arhgap11a
cyp2d6
rp4-669p10.19
ac208162.1
ac254995.1
rn7skp178
ac007679.1
ac007679.3
rp11-382d8.5
cpeb2-as1
rp5-1057j7.1
rp11-25h12.1
linc01355
rp11-19c24.1
csn2
rp11-97c18.1
prss21
phactr1
stath
tbce
hnrnpr
ac063956.2
ac254788.1
htn3
hydin
'''.split('\n')

TEST_GPCR = '''ACKR1
ACKR2
ACKR3
ACKR4
ADCYAP1R1
ADGRA1
ADGRA2
ADGRA3
ADGRB1
ADGRB2
ADGRB3
ADGRD1
ADGRD2
ADGRE1
ADGRE2
ADGRE3
ADGRE4P
ADGRE5
ADGRF1
ADGRF2
ADGRF3
ADGRF4
ADGRF5
ADGRG1
ADGRG2
ADGRG3
ADGRG4
ADGRG5
ADGRG6
ADGRG7
ADGRL1
ADGRL2
ADGRL3
ADGRL4
ADGRV1
ADORA1
ADORA2A
ADORA2B
ADORA3
ADRA1A
ADRA1B
ADRA1D
ADRA2A
ADRA2B
ADRA2C
ADRB1
ADRB2
ADRB3
AGTR1
AGTR2
APLNR
AVPR1A
AVPR1B
AVPR2
BDKRB1
BDKRB2
BRS3
BRS3
C3AR1
C5AR1
C5AR2
CALCR
CALCRL
CASR
CCKAR
CCKBR
CCR1
CCR10
CCR2
CCR3
CCR4
CCR5
CCR6
CCR7
CCR8
CCR9
CCRL2
CELSR1
CELSR2
CELSR3
CHRM1
CHRM2
CHRM3
CHRM4
CHRM5
CMKLR1
CNR1
CNR2
CRHR1
CRHR2
CX3CR1
CXCR1
CXCR2
CXCR3
CXCR4
CXCR5
CXCR6
CYSLTR1
CYSLTR2
DRD1
DRD2
DRD3
DRD4
DRD5
EDNRA
EDNRB
F2R
F2RL1
F2RL2
F2RL3
FFAR1
FFAR2
FFAR3
FFAR4
FPR1
FPR2
FPR2
FPR3
FSHR
FZD1
FZD10
FZD2
FZD3
FZD4
FZD5
FZD6
FZD7
FZD8
FZD9
GABBR1
GABBR2
GALR1
GALR2
GALR3
GCGR
GHRHR
GHSR
GIPR
GLP1R
GLP2R
GNRHR
GNRHR2
GPBAR1
GPER1
GPR1
GPR101
GPR107
GPR119
GPR119
GPR12
GPR132
GPR135
GPR137
GPR139
GPR141
GPR142
GPR143
GPR146
GPR148
GPR149
GPR15
GPR150
GPR151
GPR152
GPR153
GPR156
GPR157
GPR158
GPR160
GPR161
GPR162
GPR17
GPR171
GPR173
GPR174
GPR176
GPR179
GPR18
GPR18
GPR182
GPR183
GPR19
GPR20
GPR21
GPR22
GPR25
GPR26
GPR27
GPR3
GPR31
GPR32
GPR33
GPR34
GPR35
GPR37
GPR37L1
GPR39
GPR4
GPR42
GPR42
GPR45
GPR50
GPR52
GPR55
GPR55
GPR6
GPR61
GPR62
GPR63
GPR65
GPR68
GPR75
GPR78
GPR79
GPR82
GPR83
GPR84
GPR85
GPR87
GPR88
GPRC5A
GPRC5B
GPRC5C
GPRC5D
GPRC6A
GRM1
GRM2
GRM3
GRM4
GRM5
GRM6
GRM7
GRM8
GRPR
HCAR1
HCAR2
HCAR3
HCRTR1
HCRTR2
HRH1
HRH2
HRH3
HRH4
HTR1A
HTR1B
HTR1D
HTR1E
HTR1F
HTR2A
HTR2B
HTR2C
HTR4
HTR5A
HTR5BP
HTR6
HTR7
KISS1R
LGR4
LGR5
LGR6
LHCGR
LPAR1
LPAR2
LPAR3
LPAR4
LPAR5
LPAR6
LTB4R
LTB4R2
MAS1
MAS1L
MC1R
MC2R
MC3R
MC4R
MC5R
MCHR1
MCHR2
MLNR
MRGPRD
MRGPRE
MRGPRF
MRGPRG
MRGPRX1
MRGPRX2
MRGPRX3
MRGPRX4
MTNR1A
MTNR1B
NMBR
NMUR1
NMUR2
NPBWR1
NPBWR2
NPFFR1
NPFFR2
NPSR1
NPY1R
NPY2R
NPY4R
NPY5R
NPY6R
NTSR1
NTSR2
OPN3
OPN4
OPN5
OPRD1
OPRK1
OPRL1
OPRM1
OR51E1
OXER1
OXGR1
OXTR
P2RY1
P2RY10
P2RY11
P2RY12
P2RY13
P2RY14
P2RY2
P2RY4
P2RY6
P2RY8
PRLHR
PROKR1
PROKR2
PTAFR
PTGDR
PTGDR2
PTGER1
PTGER2
PTGER3
PTGER4
PTGFR
PTGIR
PTH1R
PTH2R
QRFPR
RXFP1
RXFP2
RXFP3
RXFP4
S1PR1
S1PR2
S1PR3
S1PR4
S1PR5
SCTR
SMO
SSTR1
SSTR2
SSTR3
SSTR4
SSTR5
SUCNR1
TAAR1
TAAR2
TAAR3
TAAR4P
TAAR5
TAAR6
TAAR8
TAAR9
TACR1
TACR2
TACR3
TAS1R1
TAS1R2
TAS1R3
TAS2R1
TAS2R10
TAS2R13
TAS2R14
TAS2R16
TAS2R19
TAS2R20
TAS2R3
TAS2R30
TAS2R31
TAS2R38
TAS2R39
TAS2R4
TAS2R40
TAS2R41
TAS2R42
TAS2R43
TAS2R45
TAS2R46
TAS2R5
TAS2R50
TAS2R60
TAS2R7
TAS2R8
TAS2R9
TBXA2R
TPRA1
TRHR
TSHR
UTS2R
VIPR1
VIPR2
XCR1'''.split('\n')

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

    def testBestHitSearchExactMatchMart410TargetPost(self):
        targets = TEST_MART_410
        response = self._make_request('/api/latest/private/besthitsearch',
                                      data=json.dumps({
                                          'q': targets,
                                          'filter': 'target',
                                          'no_cache': True,
                                      },),
                                      content_type='application/json',
                                      method='POST',
                                      token=self._AUTO_GET_TOKEN)

        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))

        self.assertEqual(len(json_response['data']), len(targets))

        for result in json_response['data']:
            self.assertIsNotNone(result)

    def testBestHitSearchExactMatchGPCRTargetPost(self):
        targets = TEST_GPCR
        response = self._make_request('/api/latest/private/besthitsearch',
                                      data=json.dumps({
                                          'q': targets,
                                          'filter': 'target',
                                          'no_cache': True,
                                      }, ),
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
