import csv
import random
import string
from collections import defaultdict

#from app.common.auth import AuthKey
from app.common.scoring_conf import ScoringMethods

__author__ = 'andreap'




import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DATA_VERSION = os.getenv('OPENTARGETS_DATA_VERSION', '16.12')
    ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    ELASTICSEARCH_DATA_INDEX_NAME = DATA_VERSION+'_evidence-data*'
    ELASTICSEARCH_DATA_DOC_NAME = 'evidencestring'
    ELASTICSEARCH_EFO_LABEL_INDEX_NAME = DATA_VERSION+'_efo-data'
    ELASTICSEARCH_EFO_LABEL_DOC_NAME = 'efo'
    ELASTICSEARCH_ECO_INDEX_NAME = DATA_VERSION+'_eco-data'
    ELASTICSEARCH_ECO_DOC_NAME = 'eco'
    ELASTICSEARCH_GENE_NAME_INDEX_NAME = DATA_VERSION+'_gene-data'
    ELASTICSEARCH_GENE_NAME_DOC_NAME = 'genedata'
    ELASTICSEARCH_EXPRESSION_INDEX_NAME = DATA_VERSION+'_expression-data'
    ELASTICSEARCH_EXPRESSION_DOC_NAME = 'expression'
    ELASTICSEARCH_REACTOME_INDEX_NAME = DATA_VERSION+'_reactome-data'
    ELASTICSEARCH_REACTOME_REACTION_DOC_NAME = 'reactome-reaction'
    ELASTICSEARCH_DATA_ASSOCIATION_INDEX_NAME = DATA_VERSION+'_association-data'
    ELASTICSEARCH_DATA_ASSOCIATION_DOC_NAME = 'association'
    ELASTICSEARCH_DATA_SEARCH_INDEX_NAME = DATA_VERSION+'_search-data'
    ELASTICSEARCH_DATA_SEARCH_DOC_NAME = 'search-object'
    ELASTICSEARCH_DATA_RELATION_INDEX_NAME = DATA_VERSION + '_relation-data'
    ELASTICSEARCH_DATA_RELATION_DOC_NAME = 'relation'
    ELASTICSEARCH_LOG_EVENT_INDEX_NAME = '!eventlog'
    DEBUG = os.getenv('API_DEBUG', False)
    TESTING = False
    PROFILE = False
    SECRET_KEY = os.getenv('SECRET_KEY', ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(32)))
    PUBLIC_API_BASE_PATH = '/api/public/v'
    PRIVATE_API_BASE_PATH = '/api/private/v'
    API_VERSION = os.getenv('API_VERSION','2.0')
    API_VERSION_MINOR = os.getenv('API_VERSION_MINOR','2.0.2')
    '''datatype configuration'''
    DATATYPES = defaultdict(lambda: "other")
    DATATYPES['rna_expression'] = ['expression_atlas',]
    DATATYPES['genetic_association'] = ['uniprot','gwas_catalog','eva','uniprot_literature', 'gene2phenotype']
    DATATYPES['affected_pathway'] = ['reactome',]
    DATATYPES['animal_model'] = ['phenodigm',]
    DATATYPES['somatic_mutation'] = ['cancer_gene_census','eva_somatic','intogen']
    DATATYPES['known_drug'] = ['chembl',]
    DATATYPES['literature'] = ['europepmc']
    DATATYPE_ORDERED=['genetic_association','somatic_mutation','known_drug','rna_expression','affected_pathway','animal_model', 'literature']
    # DATATYPES['protein_expression'] = ['hpa']

    DATASOURCE_SCORING_METHOD = defaultdict(lambda: ScoringMethods.SUM)
    # DATASOURCE_SCORING_METHOD['phenodigm'] = ScoringMethods.MAX

    PROXY_SETTINGS={'allowed_targets': {'ensembl': 'https://rest.ensembl.org/',
                                        'gxa': 'https://www.ebi.ac.uk/gxa/',
                                        'pdbe': 'https://www.ebi.ac.uk/pdbe/',
                                        'epmc': 'http://www.ebi.ac.uk/europepmc/',
                                        },
                    'allowed_domains': ['www.ebi.ac.uk'],
                    'allowed_request_domains' : ['targetvalidation.org', 'alpha.targetvalidation.org','beta.targetvalidation.org','localhost', '127.0.0.1'],
                    }
    REDIS_SERVER_PATH =os.getenv('REDIS_SERVER_PATH', '/tmp/api_redis.db')

    USAGE_LIMIT_DEFAULT_SHORT = int(os.getenv('USAGE_LIMIT_DEFAULT_SHORT', '3000'))
    USAGE_LIMIT_DEFAULT_LONG = int(os.getenv('USAGE_LIMIT_DEFAULT_LONG', '1200000'))
    SECRET_PATH = os.getenv('SECRET_PATH', 'app/authconf/')
    SECRET_RATE_LIMIT_FILE = os.getenv('SECRET_RATE_LIMIT_FILE', 'rate_limit.csv')
    SECRET_IP_RESOLVER_FILE = os.getenv('SECRET_IP_RESOLVER_FILE', 'ip_list.csv')
    USAGE_LIMIT_PATH = os.path.join(SECRET_PATH, SECRET_RATE_LIMIT_FILE)
    IP_RESOLVER_LIST_PATH = os.path.join(SECRET_PATH, SECRET_IP_RESOLVER_FILE)

    NO_CACHE_PARAMS = 'no_cache'

    MIXPANEL_TOKEN = os.getenv('MIXPANEL_TOKEN', None)



    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    # currently these also corresponds to the defaults i.e. OPENTARGETS_API_CONFIG=`default`
    DEBUG = True
    # ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200/')
    LOGSTASH_HOST = '127.0.0.1'
    LOGSTASH_PORT = 5000
    APP_CACHE_EXPIRY_TIMEOUT = 1

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)



class TestingConfig(Config):
    TESTING = True
    APP_CACHE_EXPIRY_TIMEOUT = 60
    SERVER_NAME = 'localhost:5000'


class ProductionConfig(Config):
    ## kubernetes automatically defines DNS names for each service, at least on GKE
    APP_CACHE_EXPIRY_TIMEOUT = 60*60*6 #6 hours


    @classmethod
    def init_app(cls, app):
        Config.init_app(app)






config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
