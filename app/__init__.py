import csv
import os
from datetime import datetime

import datadog
from flask import Flask, redirect, Blueprint, send_from_directory, g
from flask.ext.compress import Compress
from flask.ext.cors import CORS
from flask_limiter import Limiter

# from flask.ext.login import LoginManager
from redislite import Redis

from app.common.auth import AuthKey
from app.common.datadog_signals import LogApiCallWeight
from app.common.datatypes import DataTypes
from app.common.proxy import ProxyHandler
from app.common.rate_limit import RateLimiter, ceil_dt_to_future_time
from app.common.rate_limit import increment_call_rate
from app.common.scoring_conf import DataSourceScoring
from config import config, Config
import logging
from elasticsearch import Elasticsearch
from common.elasticsearchclient import esQuery, InternalCache
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
    api_version = app.config['API_VERSION']


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
    app.extensions['redis-core'] = Redis(app.config['REDIS_SERVER'], db=0) #served data
    app.extensions['redis-service'] = Redis(app.config['REDIS_SERVER'], db=1) #cache, rate limit and internal things
    app.extensions['redis-user'] = Redis(app.config['REDIS_SERVER'], db=2)# user info

    icache = InternalCache(app.extensions['redis-service'],
                           str(api_version))
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
                                        cache = icache
                                        )




    app.extensions['proxy'] = ProxyHandler(allowed_targets=app.config['PROXY_SETTINGS']['allowed_targets'],
                                           allowed_domains=app.config['PROXY_SETTINGS']['allowed_domains'],
                                           allowed_request_domains=app.config['PROXY_SETTINGS']['allowed_request_domains'])

    basepath = app.config['PUBLIC_API_BASE_PATH']+api_version
    # cors = CORS(app, resources=r'/api/*', allow_headers='Content-Type,Auth-Token')

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
        app.logger.error('cannot find rate limit file: %s. RATE LIMIT QUOTA LOAD SKIPPED!'%rate_limit_file)


    '''setup datadog logging'''
    if  Config.datadog_options:
        datadog.initialize(**Config.datadog_options)
        stats = datadog.ThreadStats()
        stats.start(flush_interval=5, roll_up_interval=5)
        app.extensions['datadog'] = stats
        log = logging.getLogger('dd.datadogpy')
        log.setLevel(logging.DEBUG)
    else:
         app.extensions['datadog'] = None


    '''compress http response'''
    compress = Compress()
    compress.init_app(app)

    latest_blueprint = Blueprint('latest', __name__)
    current_version_blueprint = Blueprint(str(api_version), __name__)


    specpath = '/cttv'

    if app.config['PROFILE'] == True:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])




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

    @app.before_request
    def before_request():
        g.request_start = datetime.now()
    @app.after_request
    def after(resp):
        rate_limiter = RateLimiter()
        now = datetime.now()
        took = (now - g.request_start).total_seconds()*1000
        if took > 500:
            cache_time = str(int(3600*took))# set cache to last one our for each second spent in the request
            resp.headers.add('X-Accel-Expires', cache_time)
        took = int(round(took))
        LogApiCallWeight(took)
        # if took < RateLimiter.DEFAULT_CALL_WEIGHT:
        #     took = RateLimiter.DEFAULT_CALL_WEIGHT
        current_values = increment_call_rate(took,rate_limiter)
        now = datetime.now()
        resp.headers.add('X-API-Took', took)
        resp.headers.add('X-RateLimit-Limit-10s', rate_limiter.short_window_rate)
        resp.headers.add('X-RateLimit-Limit-1h', rate_limiter.long_window_rate)
        resp.headers.add('X-RateLimit-Remaining-10s', rate_limiter.short_window_rate-current_values['short'])
        resp.headers.add('X-RateLimit-Remaining-1h', rate_limiter.long_window_rate-current_values['long'])
        resp.headers.add('X-RateLimit-Reset-10s', round(ceil_dt_to_future_time(now, 10),2))
        resp.headers.add('X-RateLimit-Reset-1h', round(ceil_dt_to_future_time(now, 3600),2))
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.headers.add('Access-Control-Allow-Headers','Content-Type,Auth-Token')
        resp.headers.add('Cache-Control', "no-cache, must-revalidate, max-age=0")
        return resp


    return app



if __name__ == '__main__':
    create_app().run()


