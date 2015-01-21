
__author__ = 'andreap'

import ujson as json

class OutputDataStructure():
    source = False


class FullSourceDataStructure(OutputDataStructure):
    source = {"exclude": [ "_private.*" ]}

class SimpleSourceDataStructure(OutputDataStructure):
    source =  {"include": [ "id",
                           "biological_object.about",
                           "biological_object.properties.*",
                           "biological_subject.about",
                           "biological_subject.gene_info",
                           "evidence.evidence_codes",
                           "evidence.provenance_type.database.id",
                           "evidence.association_score.probability.value"],
                "exclude": [ "_private.*" ]}

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


class OutputDataStructureOptions():
    FULL = 'full'
    SIMPLE = 'simple'
    COUNT = 'count'
    IDS = 'ids'
    GENE = 'gene'
    DISEASE = 'disease'
    GENE_AND_DISEASE = 'gene_and_disease'

    @classmethod
    def getSource(cls,structure):
        if structure == cls.FULL:
            return FullSourceDataStructure.source
        elif structure == cls.SIMPLE:
            return SimpleSourceDataStructure.source
        elif structure == cls.IDS:
            return IdsSourceDataStructure.source
        elif structure == cls.GENE:
            return ShortGeneDataStructure.source
        elif structure == cls.DISEASE:
            return DiseaseDataStructure.source
        elif structure == cls.GENE_AND_DISEASE:
            return GeneAndDiseaseDataStructure.source
        else:
            return OutputDataStructure.source


def json_type(data):
    try:
        return json.loads(data)
    except:
        raise ValueError('Malformed JSON')