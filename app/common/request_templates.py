import copy

from app.common.scoring_conf import ScoringMethods

__author__ = 'andreap'

import json

class OutputDataStructure():
    source = False


class FullSourceDataStructure(OutputDataStructure):
    source = {"excludes": [ "_private*",
                           "private*"]}

class SimpleSourceDataStructure(OutputDataStructure):
    source =  {"includes": [ "id",
                            "disease.id",
                            "disease.efo_info.label",
                            "target.id",
                            "target.gene_info.symbol",
                            "sourceID",
                            "type",
                            "scores.association_score",
                            # "disease.efo_info.therapeutic_area.codes",
                            "association_score.overall",
                            "association_score.datatype*",
                            ],
                "excludes": [ "_private*" ,
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
    source =  {"includes": [],
                "excludes": [ "_private*" ,
                           "private*"],
               }


class ScoreDataStructure(OutputDataStructure):
    source = {"includes": ["target.id",
                           "target.gene_info.symbol",
                           "target.gene_info.name",
                           "target.tractability",
                           "disease.id",
                           "disease.efo_info.label",
                           "disease.efo_info.therapeutic_area",
                           "disease.efo_info.path",
                           "is_direct",
                           "evidence_count*",
                           "association_score*",
                           "id"],
              "excludes": ["_private*",
                           "private*"]
              }



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
        CUSTOM: CustomDataStructure.source,
    }

    @classmethod
    def getSource(cls,structure, params = None):
        if structure in cls.options:
            return cls._inject_association_score_implementation(cls.options[structure], params)
        return OutputDataStructure.source

    @classmethod
    def _inject_association_score_implementation(cls,source, params):
        source=copy.deepcopy(source)
        if params is not None:
            if isinstance(source, dict) and ('includes' in source):
                if params.fields:
                    source['includes'].extend(params.fields)
                    source['includes'] = list(set(source['includes']))
                for i,field in enumerate(source['includes']):
                    if field.startswith('association_score'):
                        source['includes'][i]= source['includes'][i].replace('association_score',params.association_score_method)
        return source


class FilterTypes():
    DATASOURCE = 'datasource'
    DATATYPE = 'datatype'
    ASSOCIATION_SCORE_MIN = 'scorevalue_min'
    ASSOCIATION_SCORE_MAX = 'scorevalue_max'
    RNA_EXPRESSION_LEVEL = 'rna_expression_level'
    RNA_EXPRESSION_TISSUE = 'rna_expression_tissue'
    ZSCORE_EXPRESSION_LEVEL = 'zscore_expression_level'
    ZSCORE_EXPRESSION_TISSUE = 'zscore_expression_tissue'
    PROTEIN_EXPRESSION_LEVEL = 'protein_expression_level'
    PROTEIN_EXPRESSION_TISSUE = 'protein_expression_tissue'
    SCORE_RANGE = 'scorevalue_range'
    PATHWAY = 'pathway'
    GO = 'go'
    UNIPROT_KW = 'uniprotkw'
    TARGET = 'target'
    DISEASE = 'disease'
    ECO = 'eco'
    IS_DIRECT = 'direct'
    THERAPEUTIC_AREA = 'therapeutic_area'
    TARGETS_ENRICHMENT = 'targets_enrichment'
    TARGET_CLASS = 'target_class'
    TRACTABILITY = 'tractability'


class AssociationSortOptions:
    OVERALL = 'overall'


class EvidenceSortOptions:
    SCORE = 'scores.association_score'
