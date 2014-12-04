
__author__ = 'andreap'

import ujson as json

class OutputDataStructure():
    source = False


class FullSourceDataStructure(OutputDataStructure):
    source = True

class SimpleSourceDataStructure(OutputDataStructure):
    source = [ "id",
               "biological_object.about",
               "biological_object.properties.*",
               "biological_subject.about",
               "biological_subject.gene_info",
               "evidence.evidence_codes",
               "evidence.provenance_type.database.id",
               "evidence.association_score.probability.value"]

class IdsSourceDataStructure(OutputDataStructure):
    source = [ "id"]

class OutputDataStructureOptions():
    FULL = 'full'
    SIMPLE = 'simple'
    COUNT = 'count'
    IDS = 'ids'

    @classmethod
    def getSource(cls,structure):
        if structure == cls.FULL:
            return FullSourceDataStructure.source
        elif structure == cls.SIMPLE:
            return SimpleSourceDataStructure.source
        elif structure == cls.IDS:
            return IdsSourceDataStructure.source
        else:
            return OutputDataStructure.source


def json_type(data):
    try:
        return json.loads(data)
    except:
        raise ValueError('Malformed JSON')