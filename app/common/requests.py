__author__ = 'andreap'



class OutputDataStructure():
    source = False


class FullSourceDataStructure(OutputDataStructure):
    source = True

class SimpleSourceDataStructure(OutputDataStructure):
    #TODO: cahnge it with update structure
    source = [ "biological_object.about", "biological_subject.about", "provenance.date_asserted"]


class OutputDataStructureOptions():
    FULL = 'full'
    SIMPLE = 'simple'
    COUNT = 'count'

    @classmethod
    def getSource(cls,structure):
        if structure == cls.FULL:
            return FullSourceDataStructure.source
        elif structure == cls.SIMPLE:
            return SimpleSourceDataStructure.source
        else:
            return OutputDataStructure.source