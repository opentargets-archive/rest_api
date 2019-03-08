import ConfigParser
import ast
import logging
import os
import random
import string
import sys
from collections import defaultdict
from functools import partial
from logging import getLogger
from envparse import env

from pythonjsonlogger import jsonlogger
from app.common.scoring_conf import ScoringMethods

basedir = os.path.abspath(os.path.dirname(__file__))

__author__ = 'andreap'


def init_from_file(filename):
    cfg = ConfigParser.ConfigParser()
    if cfg.read(filename):
        return cfg
    else:
        return None


def prefix_or_custom_idx(prefix, name, ini, suffix=''):
    section_name = 'indexes'

    idx_name = ini.get(section_name, name) \
        if ini and \
           ini.has_option(section_name, name) \
        else prefix + '_' + name

    from_envar = env('OPENTARGETS_ES_' + name.upper(), default=None)
    idx_name = from_envar if from_envar else idx_name

    return idx_name + suffix


class Config:

    ## [read from an .env file, if there]
    env.read_envfile()

    ## the API version number comes from the VERSION file as single point of truth
    env.read_envfile('VERSION')
    API_VERSION = env('API_VERSION', cast=str)
    API_VERSION_MINOR = env('API_VERSION_MINOR', cast=str)

    ## [key configurations]
    ELASTICSEARCH_URL = env('ELASTICSEARCH_URL', default='')
    # TODO - would be better to throw an error instead of falling back to a default if this parameter is not set.
    DATA_VERSION = env('OPENTARGETS_DATA_VERSION', default='18.08')
    # tagged version from expression_hierarchy repository must have same DATA_VERSION tag
    ES_TISSUE_MAP_URL = 'https://raw.githubusercontent.com/opentargets/expression_hierarchy/{0}/process/map_with_efos.json'
    ES_TISSUE_MAP = None
    ## logic to point to custom indices in ES
    ES_CUSTOM_IDXS_FILENAME = basedir + os.path.sep + 'es_custom_idxs.ini'
    ES_CUSTOM_IDXS = ast.literal_eval(env('OPENTARGETS_ES_CUSTOM_IDXS',default='False'))

    ES_CUSTOM_IDXS_INI = init_from_file(ES_CUSTOM_IDXS_FILENAME) \
        if ES_CUSTOM_IDXS else None

    ## indices to point to in ES
    ES_PREFIX = partial(prefix_or_custom_idx,
                        prefix=DATA_VERSION,
                        ini=ES_CUSTOM_IDXS_INI)

    ELASTICSEARCH_DATA_INDEX_NAME = ES_PREFIX(name='evidence-data', suffix='*')
    ELASTICSEARCH_DATA_DOC_NAME = 'evidencestring'
    ELASTICSEARCH_EFO_LABEL_INDEX_NAME = ES_PREFIX(name='efo-data')
    ELASTICSEARCH_EFO_LABEL_DOC_NAME = 'efo'
    ELASTICSEARCH_ECO_INDEX_NAME = ES_PREFIX(name='eco-data')
    ELASTICSEARCH_ECO_DOC_NAME = 'eco'
    ELASTICSEARCH_GENE_NAME_INDEX_NAME = ES_PREFIX(name='gene-data')
    ELASTICSEARCH_GENE_NAME_DOC_NAME = 'genedata'
    ELASTICSEARCH_EXPRESSION_INDEX_NAME = ES_PREFIX(name='expression-data')
    ELASTICSEARCH_EXPRESSION_DOC_NAME = 'expression'
    ELASTICSEARCH_REACTOME_INDEX_NAME = ES_PREFIX(name='reactome-data')
    ELASTICSEARCH_REACTOME_REACTION_DOC_NAME = 'reactome-reaction'
    ELASTICSEARCH_DATA_ASSOCIATION_INDEX_NAME = ES_PREFIX(name='association-data')
    ELASTICSEARCH_DATA_ASSOCIATION_DOC_NAME = 'association'
    ELASTICSEARCH_DATA_SEARCH_INDEX_NAME = ES_PREFIX(name='search-data')
    ELASTICSEARCH_DATA_SEARCH_DOC_NAME = 'search-object'
    ELASTICSEARCH_DATA_RELATION_INDEX_NAME = ES_PREFIX(name='relation-data')
    ELASTICSEARCH_DATA_RELATION_DOC_NAME = 'relation'
    ELASTICSEARCH_LOG_EVENT_INDEX_NAME = '!eventlog'

    DEBUG = env('API_DEBUG', cast=bool, default=False)
    TESTING = False
    PROFILE = False
    SECRET_KEY = env('SECRET_KEY', default=''.join(
        random.SystemRandom().choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(32)))

    '''datatype configuration'''
    DATATYPES = defaultdict(lambda: "other")
    DATATYPES['rna_expression'] = ['expression_atlas', ]
    DATATYPES['genetic_association'] = ['uniprot', 'gwas_catalog', 'phewas_catalog', 'twentythreeandme', 'eva',
                                        'uniprot_literature', 'gene2phenotype', 'genomics_england']
    DATATYPES['affected_pathway'] = ['reactome', 'slapenrich', 'progeny', 'sysbio']
    DATATYPES['animal_model'] = ['phenodigm', ]
    DATATYPES['somatic_mutation'] = ['cancer_gene_census', 'eva_somatic', 'intogen', 'uniprot_somatic']
    DATATYPES['known_drug'] = ['chembl', ]
    DATATYPES['literature'] = ['europepmc']
    DATATYPE_ORDERED = ['genetic_association', 'somatic_mutation', 'known_drug', 'rna_expression', 'affected_pathway',
                        'animal_model', 'literature']
    # DATATYPES['protein_expression'] = ['hpa']

    # Allow addition of custom datatypes from environment variable
    # Environment variable must be named CUSTOM_DATASOURCE
    # Format is new_source:type e.g. genomics_england_tiering:genetic_association
    # Multiple custom data sources of the same type can be passed as a comma-separated list
    env_var = env('CUSTOM_DATASOURCE', default='')
    if env_var:
        for source_and_type in env_var.split(','):
            source, datatype = source_and_type.split(':')
            if datatype not in DATATYPES:
                print "Cannot add env_var as %s is not a recognised datatype" % datatype
            else:
                DATATYPES[datatype].append(source)
                print "Added %s to list of %s data sources, list is now " % (source, datatype), DATATYPES[datatype]

    DATASOURCE_SCORING_METHOD = defaultdict(lambda: ScoringMethods.SUM)
    # DATASOURCE_SCORING_METHOD['phenodigm'] = ScoringMethods.MAX

    PROXY_SETTINGS = {'allowed_targets': {'ensembl': 'https://rest.ensembl.org/',
                                          'gxa': 'https://www.ebi.ac.uk/gxa/',
                                          'pdbe': 'https://www.ebi.ac.uk/pdbe/',
                                          'epmc': 'http://www.ebi.ac.uk/europepmc/',
                                          },
                      'allowed_domains': ['www.ebi.ac.uk'],
                      'allowed_request_domains': ['targetvalidation.org', 'alpha.targetvalidation.org',
                                                  'beta.targetvalidation.org', 'localhost', '127.0.0.1'],
                      }
    REDIS_SERVER_PATH = env('REDIS_SERVER_PATH', default='/tmp/api_redis.db')

    SECRET_PATH = env('SECRET_PATH', default='app/authconf/')
    SECRET_IP_RESOLVER_FILE = env('SECRET_IP_RESOLVER_FILE', default='ip_list.csv')
    IP_RESOLVER_LIST_PATH = os.path.join(SECRET_PATH, SECRET_IP_RESOLVER_FILE)

    NO_CACHE_PARAMS = 'no_cache'

    MIXPANEL_TOKEN = env('MIXPANEL_TOKEN', default=None)

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    # default settings
    DEBUG = True
    APP_CACHE_EXPIRY_TIMEOUT = 60

    @classmethod
    def init_app(cls, app):
        file_handler = logging.FileHandler('output.log')
        file_handler.setLevel(logging.DEBUG)
        jsonformatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        file_handler.setFormatter(jsonformatter)

        loggers = [app.logger,
                   getLogger('elasticsearch'),
                   getLogger('redislite')]

        for logger in loggers:
            logger.addHandler(file_handler)

        Config.init_app(app)


class TestingConfig(Config):
    TESTING = True
    APP_CACHE_EXPIRY_TIMEOUT = 60
    SERVER_NAME = 'localhost:5000'


class ProductionConfig(Config):
    APP_CACHE_EXPIRY_TIMEOUT = 60 * 60 * 6  # 6 hours

    @classmethod
    def init_app(cls, app):
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setLevel(logging.WARN)
        jsonformatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        console_handler.setFormatter(jsonformatter)

        loggers = [app.logger,
                   getLogger('elasticsearch'),
                   getLogger('redislite')]

        # Sadly, this does not work:
        # wlog = getLogger('werkzeug')
        # # log.setLevel(logging.ERROR)
        # wlog.disabled = True

        for logger in loggers:
            logger.addHandler(console_handler)
            logger.setLevel(logging.WARN)

        Config.init_app(app)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
