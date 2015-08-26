__author__ = 'andreap'

import json

class OutputDataStructure():
    source = False


class FullSourceDataStructure(OutputDataStructure):
    source = {"exclude": [ "_private*" ]}

class SimpleSourceDataStructure(OutputDataStructure):
    source =  {"include": [ "id",
                           "disease.id",
                           "disease.properties.*",
                           "target.id",
                           "evidence.evidence_codes",
                           "sourceID",
                           "type",
                           "scores.association_score"],
                "exclude": [ "_private*" ]}

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

class GeneAndDiseaseDataStructure(OutputDataStructure):
    source = ShortGeneDataStructure.source + DiseaseDataStructure.source


class CustomDataStructure(OutputDataStructure):
    source =  {"include": [ ],
                "exclude": [ "_private*" ]}


class ScoreDataStructure(OutputDataStructure):
    source =  {"include": ["sourceID",
                           "scores",
                           "type",
                           "target.id",
                           "target.gene_info.symbol",
                           "disease.efo_info.label",
                           "disease.id"],
                "exclude": [ "_private*" ]}

class OutputDataStructureOptions():
    DEFAULT = 'default'
    FULL = 'full'
    SIMPLE = 'simple'
    COUNT = 'count'
    IDS = 'ids'
    GENE = 'gene'
    DISEASE = 'disease'
    GENE_AND_DISEASE = 'gene_and_disease'
    CUSTOM = 'custom'
    TREE = 'tree'
    FLAT = 'flat'
    SCORE = 'score'


    options = {
        FULL: FullSourceDataStructure.source,
        SIMPLE: SimpleSourceDataStructure.source,
        IDS: IdsSourceDataStructure.source,
        GENE: ShortGeneDataStructure.source,
        DISEASE: DiseaseDataStructure.source,
        GENE_AND_DISEASE: GeneAndDiseaseDataStructure.source,
        COUNT: OutputDataStructure.source,
        SCORE: ScoreDataStructure.source,
        CUSTOM: CustomDataStructure.source,
    }

    @classmethod
    def getSource(cls,structure):
        if structure in cls.options:
            return  cls.options[structure]
        else:
            return OutputDataStructure.source


def json_type(data):
    try:
        return json.loads(data)
    except:
        raise ValueError('Malformed JSON')