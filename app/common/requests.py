__author__ = 'andreap'



class OutputDataStructure():
    source = False


class FullSourceDataStructure(OutputDataStructure):
    source = True

class SimpleSourceDataStructure(OutputDataStructure):
    source = [ "id","biological_object.about", "biological_subject.about", "evidence.evidence_codes"]

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