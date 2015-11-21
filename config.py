from collections import defaultdict
from app.common.scoring_conf import ScoringMethods

__author__ = 'andreap'




import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    ELASTICSEARCH_DATA_INDEX_NAME = 'evidence-data*'
    ELASTICSEARCH_DATA_DOC_NAME = 'evidencestring'
    ELASTICSEARCH_EFO_LABEL_INDEX_NAME = 'efo-data'
    ELASTICSEARCH_EFO_LABEL_DOC_NAME = 'efo'
    ELASTICSEARCH_ECO_INDEX_NAME = 'eco-data'
    ELASTICSEARCH_ECO_DOC_NAME = 'eco'
    ELASTICSEARCH_GENE_NAME_INDEX_NAME = 'gene-data'
    ELASTICSEARCH_GENE_NAME_DOC_NAME = 'genedata'
    ELASTICSEARCH_EXPRESSION_INDEX_NAME = 'expression-data'
    ELASTICSEARCH_EXPRESSION_DOC_NAME = 'expression'
    ELASTICSEARCH_REACTOME_INDEX_NAME = 'reactome-data'
    ELASTICSEARCH_REACTOME_REACTION_DOC_NAME = 'reactome-reaction'
    ELASTICSEARCH_DATA_ASSOCIATION_INDEX_NAME = 'association-data_1'
    ELASTICSEARCH_DATA_ASSOCIATION_DOC_NAME = 'association'
    DEBUG = True
    PROFILE = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or u'C=41d6xo]4940NP,9jwF@@v0KDdTtO'
    PUBLIC_API_BASE_PATH = '/api/public/v'
    PRIVATE_API_BASE_PATH = '/api/private/v'
    API_VERSION = '1.0'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    '''datatype configuration'''
    DATATYPES = defaultdict(lambda: "other")
    DATATYPES['rna_expression'] = ['expression_atlas',]
    DATATYPES['genetic_association'] = ['uniprot','gwas_catalog','eva','uniprot_literature']
    DATATYPES['affected_pathway'] = ['reactome',]
    DATATYPES['animal_model'] = ['phenodigm',]
    DATATYPES['somatic_mutation'] = ['cancer_gene_census','eva_somatic',]
    DATATYPES['known_drug'] = ['chembl',]
    DATATYPES['literature'] = ['europepmc','disgenet']
    DATATYPE_ORDERED=['genetic_association','somatic_mutation','known_drug','rna_expression','affected_pathway','animal_model', 'literature']
    # DATATYPES['protein_expression'] = ['hpa']

    DATASOURCE_SCORING_METHOD = defaultdict(lambda: ScoringMethods.SUM)
    # DATASOURCE_SCORING_METHOD['phenodigm'] = ScoringMethods.MAX
    SCORING_WEIGHTS = defaultdict(lambda: 1)
    SCORING_WEIGHTS['phenodigm'] = 0.33333333
    # SCORING_WEIGHTS['expression_atlas'] = 0.2
    SCORING_WEIGHTS['europepmc'] = 0.2
    SCORING_WEIGHTS['gwas_catalog'] = 1.5

    PROXY_SETTINGS={'allowed_targets': {'ensembl': 'https://rest.ensembl.org/',
                                        'gxa': 'https://www.ebi.ac.uk/gxa/',
                                        'pdbe': 'https://www.ebi.ac.uk/pdbe/',
                                        'epmc': 'http://www.ebi.ac.uk/europepmc/',
                                        },
                    'allowed_domains': ['www.ebi.ac.uk'],
                    'allowed_request_domains' : ['targetvalidation.org', 'alpha.targetvalidation.org','beta.targetvalidation.org','localhost', '127.0.0.1'],
                    }

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    ELASTICSEARCH_URL = 'http://127.0.0.1:9201/'
    LOGSTASH_HOST = '127.0.0.1'
    LOGSTASH_PORT = 5555
    APP_CACHE_EXPIRY_TIMEOUT = 1

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        print cls.ELASTICSEARCH_URL

class DockerLinkedDevConfig(Config):
    DEBUG = True
    ELASTICSEARCH_URL = 'http://elastic:9200'
    LOGSTASH_HOST = '192.168.0.168'
    LOGSTASH_PORT = 5000
    APP_CACHE_EXPIRY_TIMEOUT = 60

class DockerLinkedConfig(Config):
    TESTING = True
    ELASTICSEARCH_URL = 'http://elastic:9200'
    LOGSTASH_HOST = '192.168.0.168'
    LOGSTASH_PORT = 5000
    APP_CACHE_EXPIRY_TIMEOUT = 60


class TestingConfig(Config):
    TESTING = True
    ELASTICSEARCH_URL = 'http://127.0.0.1:8080/es-prod/'
    LOGSTASH_HOST = '192.168.0.168'
    LOGSTASH_PORT = 5000
    APP_CACHE_EXPIRY_TIMEOUT = 60

class StagingConfig(Config):
    ELASTICSEARCH_URL = 'http://elasticsearch-9200.staging.cttv.local:9200/'
    LOGSTASH_HOST = '192.168.0.168'
    LOGSTASH_PORT = 5000
    APP_CACHE_EXPIRY_TIMEOUT = 60*60*6 #6 hours

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        #TODO: handle logs


class ProductionConfig(Config):
    ELASTICSEARCH_URL = 'http://elasticsearch-9200.production.cttv.local:9200/'
    LOGSTASH_HOST = '192.168.0.168'
    LOGSTASH_PORT = 5000
    APP_CACHE_EXPIRY_TIMEOUT = 60*60*6 #6 hours

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        #TODO: handle logs
        #
        # import logging
        # from logging.handlers import SMTPHandler
        # credentials = None
        # secure = None
        # if getattr(cls, 'MAIL_USERNAME', None) is not None:
        #     credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
        #     if getattr(cls, 'MAIL_USE_TLS', None):
        #         secure = ()
        # mail_handler = SMTPHandler(
        #     mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
        #     fromaddr=cls.FLASKY_MAIL_SENDER,
        #     toaddrs=[cls.FLASKY_ADMIN],
        #     subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
        #     credentials=credentials,
        #     secure=secure)
        # mail_handler.setLevel(logging.ERROR)
        # app.logger.addHandler(mail_handler)




class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'dockerlink': DockerLinkedConfig,
    'dockerlinkdev': DockerLinkedDevConfig,
    'default': DevelopmentConfig
}