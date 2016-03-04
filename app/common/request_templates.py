from app.common.scoring_conf import ScoringMethods

__author__ = 'andreap'

import json

class OutputDataStructure():
    source = False


class FullSourceDataStructure(OutputDataStructure):
    source = {"exclude": [ "_private*",
                           "private*"]}

class SimpleSourceDataStructure(OutputDataStructure):
    source =  {"include": [ "id",
                           "disease.id",
                           "disease.properties.*",
                           "target.id",
                           "evidence.evidence_codes",
                           "sourceID",
                           "type",
                           "scores.association_score"],
                "exclude": [ "_private*" ,
                           "private*"]}

class IdsSourceDataStructure(OutputDataStructure):
    source = ["id"]


class ShortGeneDataStructure(OutputDataStructure):
    source = [ "id",
               "approved_symbol",
               "approved_name",
               "biotype",
               "uniprot_function",
               "uniprot_similarity",]

class DiseaseDataStructure(OutputDataStructure):
    source = [ "code",
               "label",
               "path",
               "definition",
               "synonyms"]
class GeneAndDiseaseIDDataStructure(OutputDataStructure):
    source = [ "target.id",
               "disease.id",
               "_private.efo_codes",
               ]

class GeneAndDiseaseDataStructure(OutputDataStructure):
    source = ShortGeneDataStructure.source + DiseaseDataStructure.source


class CustomDataStructure(OutputDataStructure):
    source =  {"include": [ ],
                "exclude": [ "_private*" ,
                           "private*"],
               }


class ScoreDataStructure(OutputDataStructure):
    source =  {"include": ["target.id",
                           "target.gene_info.symbol",
                           "target.gene_info.name",
                           "disease.id",
                           "disease.efo_info.label",
                           "disease.efo_info.therapeutic_area",
                           "disease.efo_info.path",
                           "is_direct",
                           "evidence_count",
                           "id",
                           ],}

class ScoreDataStructureHarmonicSum(OutputDataStructure):
    source =  {"include": ScoreDataStructure.source["include"]+["harmonic-sum*"],}

class ScoreDataStructureMax(OutputDataStructure):
    source =  {"include": ScoreDataStructure.source["include"]+["sum*"],}

class ScoreDataStructureSum(OutputDataStructure):
    source =  {"include": ScoreDataStructure.source["include"]+["max*"],}

class SourceDataStructureOptions():
    DEFAULT = 'default'
    FULL = 'full'
    SIMPLE = 'simple'
    COUNT = 'count'
    IDS = 'ids'
    GENE = 'gene'
    DISEASE = 'disease'
    GENE_AND_DISEASE = 'gene_and_disease'
    GENE_AND_DISEASE_ID = 'gene_and_disease_id'
    CUSTOM = 'custom'
    SCORE = 'score'
    SCORE_SUM = ScoringMethods.SUM
    SCORE_MAX = ScoringMethods.MAX
    SCORE_HARMONIC_SUM = ScoringMethods.HARMONIC_SUM


    options = {
        DEFAULT: FullSourceDataStructure.source,
        FULL: FullSourceDataStructure.source,
        SIMPLE: SimpleSourceDataStructure.source,
        IDS: IdsSourceDataStructure.source,
        GENE: ShortGeneDataStructure.source,
        DISEASE: DiseaseDataStructure.source,
        GENE_AND_DISEASE: GeneAndDiseaseDataStructure.source,
        GENE_AND_DISEASE_ID: GeneAndDiseaseIDDataStructure.source,
        COUNT: OutputDataStructure.source,
        SCORE: ScoreDataStructure.source,
        SCORE_SUM: ScoreDataStructureSum.source,
        SCORE_MAX: ScoreDataStructureMax.source,
        SCORE_HARMONIC_SUM: ScoreDataStructureHarmonicSum.source,
        CUSTOM: CustomDataStructure.source,
    }

    @classmethod
    def getSource(cls,structure):
        if structure in cls.options:
            return  cls.options[structure]
        else:
            return OutputDataStructure.source


class OutputStructureOptions():
    TREE = 'tree'
    FLAT = 'flat'

def json_type(data):
    try:
        return json.loads(data)
    except:
        raise ValueError('Malformed JSON')


class FilterTypes():
    DATASOURCE = 'datasource'
    DATATYPE = 'datatype'
    ASSOCIATION_SCORE_MIN = 'scorevalue_min'
    ASSOCIATION_SCORE_MAX = 'scorevalue_max'
    SCORE_RANGE = 'scorevalue_range'
    PATHWAY = 'pathway'
    GO = 'go'
    UNIPROT_KW = 'uniprotkw'



class AssociationSortOptions:
    OVERALL = 'overall'

class EvidenceSortOptions:
    SCORE = 'scores.association_score'
