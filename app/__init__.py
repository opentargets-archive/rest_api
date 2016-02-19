import csv
import os

from flask import Flask, redirect, Blueprint, send_from_directory
from flask.ext.compress import Compress
from flask.ext.cors import CORS
from flask_limiter import Limiter

# from flask.ext.login import LoginManager
from redislite import Redis

from app.common.auth import AuthKey
from app.common.datatypes import DataTypes
from app.common.proxy import ProxyHandler
from app.common.scoring_conf import DataSourceScoring
from config import config
import logging
from elasticsearch import Elasticsearch
from common.elasticsearchclient import esQuery
from api import create_api
from werkzeug.contrib.cache import SimpleCache, FileSystemCache, RedisCache

# login_manager = LoginManager()
# login_manager.session_protection = 'strong'
# login_manager.login_view = 'auth.login'



__author__ = 'andreap'

def create_app(config_name):
    app = Flask(__name__, static_url_path='')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)


    log_level = logging.INFO
    if app.config['DEBUG']:
        log_level = logging.DEBUG
    logger = logging.getLogger()
    logHandler = logging.StreamHandler()
    # formatter = jsonlogger.JsonFormatter()
    # logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    # logger.addHandler(logstash.LogstashHandler(app.config['LOGSTASH_HOST'], app.config['LOGSTASH_PORT'], version=1))
    # logger.error("hi", extra=dict(hi="hi"))


    es = Elasticsearch(app.config['ELASTICSEARCH_URL'],
                        # # sniff before doing anything
                        # sniff_on_start=True,
                        # # refresh nodes after a node fails to respond
                        # sniff_on_connection_fail=True,
                        # # and also every 60 seconds
                        # sniffer_timeout=60
                       timeout=60*20,
                        )
    app.extensions['esquery'] = esQuery(es,
                                        DataTypes(app),
                                        DataSourceScoring(app),
                                        index_data=app.config['ELASTICSEARCH_DATA_INDEX_NAME'],
                                        index_efo=app.config['ELASTICSEARCH_EFO_LABEL_INDEX_NAME'],
                                        index_eco=app.config['ELASTICSEARCH_ECO_INDEX_NAME'],
                                        index_genename=app.config['ELASTICSEARCH_GENE_NAME_INDEX_NAME'],
                                        index_expression=app.config['ELASTICSEARCH_EXPRESSION_INDEX_NAME'],
                                        index_reactome=app.config['ELASTICSEARCH_REACTOME_INDEX_NAME'],
                                        index_association=app.config['ELASTICSEARCH_DATA_ASSOCIATION_INDEX_NAME'],
                                        index_search=app.config['ELASTICSEARCH_DATA_SEARCH_INDEX_NAME'],
                                        docname_data=app.config['ELASTICSEARCH_DATA_DOC_NAME'],
                                        docname_efo=app.config['ELASTICSEARCH_EFO_LABEL_DOC_NAME'],
                                        docname_eco=app.config['ELASTICSEARCH_ECO_DOC_NAME'],
                                        docname_genename=app.config['ELASTICSEARCH_GENE_NAME_DOC_NAME'],
                                        docname_expression=app.config['ELASTICSEARCH_EXPRESSION_DOC_NAME'],
                                        docname_reactome=app.config['ELASTICSEARCH_REACTOME_REACTION_DOC_NAME'],
                                        docname_association=app.config['ELASTICSEARCH_DATA_ASSOCIATION_DOC_NAME'],
                                        docname_search=app.config['ELASTICSEARCH_DATA_SEARCH_DOC_NAME'],
                                        log_level=log_level,

                                        )

    app.extensions['redis-core'] = Redis(app.config['REDIS_SERVER'], db=0)
    app.extensions['redis-service'] = Redis(app.config['REDIS_SERVER'], db=1)
    app.extensions['redis-user'] = Redis(app.config['REDIS_SERVER'], db=2)


    app.extensions['proxy'] = ProxyHandler(allowed_targets=app.config['PROXY_SETTINGS']['allowed_targets'],
                                           allowed_domains=app.config['PROXY_SETTINGS']['allowed_domains'],
                                           allowed_request_domains=app.config['PROXY_SETTINGS']['allowed_request_domains'])
    api_version = app.config['API_VERSION']
    basepath = app.config['PUBLIC_API_BASE_PATH']+api_version
    cors = CORS(app, resources=r'/api/*', allow_headers='Content-Type,Auth-Token')

    ''' define cache'''
    # cache = Cache(config={'CACHE_TYPE': 'simple'})
    # cache.init_app(latest_blueprint)
    # latest_blueprint.cache = cache
    # latest_blueprint.extensions['cache'] = cache
    # app.cache = SimpleCache()
    app.cache = FileSystemCache('/tmp/cttv-rest-api-cache', threshold=100000, default_timeout=60*60, mode=777)

    '''Set usage limiter '''
    # limiter = Limiter(global_limits=["2000 per hour", "20 per second"])
    # limiter.init_app(app)# use redis to store limits

    '''Load api keys in redis'''
    rate_limit_file = 'rate_limit.csv'
    if not os.path.exists(rate_limit_file):
        rate_limit_file = '../rate_limit.csv'
    if os.path.exists(rate_limit_file):
        with open(rate_limit_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                auth_key = AuthKey(**row)
                app.extensions['redis-user'].hmset(auth_key.get_key(), auth_key.__dict__)
    else:
        app.logger.error('cannot file rate limit file: %s. RATE LIMIT QUOTA LOAD SKIPPED!'%rate_limit_file)


    '''compress http response'''
    compress = Compress()
    compress.init_app(app)

    latest_blueprint = Blueprint('latest', __name__)
    current_version_blueprint = Blueprint(str(api_version), __name__)


    specpath = '/cttv'

    if app.config['PROFILE'] == True:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

    # bootstrap.init_app(app)
    # mail.init_app(app)
    # moment.init_app(app)
    # db.init_app(app)
    # login_manager.init_app(app)
    # pagedown.init_app(app)
    #
    # if 1:# not app.debug and not app.testing and not app.config['SSL_DISABLE']:
    #     from flask.ext.sslify import SSLify
    #     app.debug=False
    #     sslify = SSLify(app, age=30)

    # from .main import main as main_blueprint
    # app.register_blueprint(main_blueprint)
    #
    # from .auth import auth as auth_blueprint
    # app.register_blueprint(auth_blueprint, url_prefix='/auth')
    #
    # from .api_1_0 import api as api_1_0_blueprint
    # app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')




    create_api(latest_blueprint, api_version, specpath)
    create_api(current_version_blueprint, api_version, specpath)

    app.register_blueprint(latest_blueprint, url_prefix='/api/latest')
    app.register_blueprint(current_version_blueprint, url_prefix='/api/'+str(api_version))


    @app.route('/api-docs/%s'%str(api_version))
    def docs_current_version():
      return redirect('/api/swagger/index.html')

    @app.route('/api-docs')
    def docs():
      return redirect('/api/swagger/index.html')

    def serve_swagger():
        return app.send_static_file('docs/swagger/swagger.yaml')

    @app.route('/api/docs/swagger.yaml')
    def send_swagger():
        return serve_swagger()

    @app.route('/api/latest/docs/swagger.yaml')
    def send_swagger_latest():
        return serve_swagger()

    @app.route('/api/'+str(api_version)+'/docs/swagger.yaml')
    def send_swagger_current_cersion():
        return serve_swagger()


    return app



if __name__ == '__main__':
    create_app().run()


