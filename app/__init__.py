import csv
import os
from collections import defaultdict
from datetime import datetime
from flask import Flask, redirect, Blueprint, send_from_directory, g, request
from flask.ext.compress import Compress
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
from common.elasticsearchclient import esQuery, InternalCache, esStore
from api import create_api
from werkzeug.contrib.cache import SimpleCache, FileSystemCache, RedisCache
from app.common.datadog_signals import LogException
from ipaddr import IPAddress, IPNetwork

# from flask.ext.cors import CORS
# from flask_limiter import Limiter
# from flask.ext.login import LoginManager
# login_manager = LoginManager()
# login_manager.session_protection = 'strong'
# login_manager.login_view = 'auth.login'



__author__ = 'andreap'


def do_not_cache(request):
    cache_skip = [Config.NO_CACHE_PARAMS,
                  '/request_token?',
                  ]
    for skip in cache_skip:
        if skip in str(request):
            return True
    return False


def log_exception_to_datadog(sender, exception, **extra):
    LogException(exception)


def create_app(config_name):
    app = Flask(__name__, static_url_path='')
    app.config.from_object(config[config_name])
    app.config.from_envvar("OPENTARGETS_API_LOCAL_SETTINGS", silent=True)
    config[config_name].init_app(app)
    api_version = app.config['API_VERSION']
    api_version_minor = app.config['API_VERSION_MINOR']


    # log_level = logging.INFO
    # if app.config['DEBUG']:
    #     log_level = logging.DEBUG

    # Flask has a default logger which works well and pushes to stderr
    # if you want to add different handlers (to file, or logstash, or whatever)
    # you can use code similar to the one below and set the error level accordingly.

    # logHandler = logging.StreamHandler()
    # formatter = jsonlogger.JsonFormatter()
    # logHandler.setFormatter(formatter)
    # loghandler.setLevel(logging.INFO)
    # app.logger.addHandler(logHandler)

    # or for LOGSTASH
    # app.logger.addHandler(logstash.LogstashHandler(app.config['LOGSTASH_HOST'], app.config['LOGSTASH_PORT'], version=1))

    app.logger.info('looking for elasticsearch at: %s' % app.config['ELASTICSEARCH_URL'])
    print('looking for elasticsearch at: %s' % app.config['ELASTICSEARCH_URL'])


    app.extensions['redis-core'] = Redis(app.config['REDIS_SERVER_PATH'], db=0) #served data
    app.extensions['redis-service'] = Redis(app.config['REDIS_SERVER_PATH'], db=1) #cache, rate limit and internal things
    app.extensions['redis-user'] = Redis(app.config['REDIS_SERVER_PATH'], db=2)# user info
    '''setup cache'''
    app.extensions['redis-service'].config_set('save','')
    app.extensions['redis-service'].config_set('appendonly', 'no')
    icache = InternalCache(app.extensions['redis-service'],
                           str(api_version_minor))
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'],
                       # # sniff before doing anything
                       # sniff_on_start=True,
                       # # refresh nodes after a node fails to respond
                       # sniff_on_connection_fail=True,
                       # # and also every 60 seconds
                       # sniffer_timeout=60
                       timeout=60 * 20,
                       maxsize=100,
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
                                        index_relation=app.config['ELASTICSEARCH_DATA_RELATION_INDEX_NAME'],
                                        docname_data=app.config['ELASTICSEARCH_DATA_DOC_NAME'],
                                        docname_efo=app.config['ELASTICSEARCH_EFO_LABEL_DOC_NAME'],
                                        docname_eco=app.config['ELASTICSEARCH_ECO_DOC_NAME'],
                                        docname_genename=app.config['ELASTICSEARCH_GENE_NAME_DOC_NAME'],
                                        docname_expression=app.config['ELASTICSEARCH_EXPRESSION_DOC_NAME'],
                                        docname_reactome=app.config['ELASTICSEARCH_REACTOME_REACTION_DOC_NAME'],
                                        docname_association=app.config['ELASTICSEARCH_DATA_ASSOCIATION_DOC_NAME'],
                                        docname_search=app.config['ELASTICSEARCH_DATA_SEARCH_DOC_NAME'],
                                        docname_relation=app.config['ELASTICSEARCH_DATA_RELATION_DOC_NAME'],
                                        log_level=app.logger.getEffectiveLevel(),
                                        cache=icache
                                        )

    app.extensions['esstore'] = esStore(es,
                                        eventlog_index=app.config['ELASTICSEARCH_LOG_EVENT_INDEX_NAME'],
                                        cache=icache,
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
    rate_limit_file = app.config['USAGE_LIMIT_PATH']
    if not os.path.exists(rate_limit_file):
        rate_limit_file = '../'+rate_limit_file
    if os.path.exists(rate_limit_file):
        with open(rate_limit_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                auth_key = AuthKey(**row)
                app.extensions['redis-user'].hmset(auth_key.get_key(), auth_key.__dict__)
    else:
        app.logger.error('cannot find rate limit file: %s. RATE LIMIT QUOTA LOAD SKIPPED!'%rate_limit_file)


    '''load ip name resolution'''
    ip_resolver = defaultdict(lambda: "PUBLIC")
    ip_list_file = app.config['IP_RESOLVER_LIST_PATH']
    if not os.path.exists(ip_list_file):
        ip_list_file = '../' + ip_list_file
    if os.path.exists(ip_list_file):
        with open(ip_list_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                net = IPNetwork(row['ip'])
                ip_resolver[net] = row['org']
    else:
        app.logger.warning('cannot find IP list for IP resolver. All traffic will be logged as PUBLIC')
    app.config['IP_RESOLVER'] = ip_resolver



    '''compress http response'''
    compress = Compress()
    compress.init_app(app)

    latest_blueprint = Blueprint('latest', __name__)
    current_version_blueprint = Blueprint(str(api_version), __name__)
    current_minor_version_blueprint = Blueprint(str(api_version_minor), __name__)


    specpath = '/cttv'

    if app.config['PROFILE'] == True:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])




    create_api(latest_blueprint, api_version, specpath)
    create_api(current_version_blueprint, api_version, specpath)
    create_api(current_minor_version_blueprint, api_version_minor, specpath)

    app.register_blueprint(latest_blueprint, url_prefix='/api/latest')
    app.register_blueprint(current_version_blueprint, url_prefix='/api/'+str(api_version))
    app.register_blueprint(current_minor_version_blueprint, url_prefix='/api/'+str(api_version_minor))

    @app.route('/api-docs/%s' % str(api_version_minor))
    def docs_current_minor_version():
        return redirect('/api/swagger/index.html')

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
        ceil10s=round(ceil_dt_to_future_time(now, 10),2)
        ceil1h=round(ceil_dt_to_future_time(now, 3600),2)
        usage_left_10s = rate_limiter.short_window_rate-current_values['short']
        usage_left_1h = rate_limiter.long_window_rate - current_values['long']
        min_ceil = ceil10s
        if usage_left_1h <0:
            min_ceil = ceil1h
        if (usage_left_10s < 0) or (usage_left_1h <0):
            resp.headers.add('Retry-After', min_ceil)
        resp.headers.add('X-API-Took', took)
        resp.headers.add('X-Usage-Limit-10s', rate_limiter.short_window_rate)
        resp.headers.add('X-Usage-Limit-1h', rate_limiter.long_window_rate)
        resp.headers.add('X-Usage-Remaining-10s', usage_left_10s)
        resp.headers.add('X-Usage-Remaining-1h', usage_left_1h)
        # resp.headers.add('X-Usage-Limit-Reset-10s', ceil10s)
        # resp.headers.add('X-Usage-Limit-Reset-1h', ceil1h)
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.headers.add('Access-Control-Allow-Headers','Content-Type,Auth-Token')
        if do_not_cache(request):# do not cache in the browser
            resp.headers.add('Cache-Control', "no-cache, must-revalidate, max-age=0")
        else:
            resp.headers.add('Cache-Control', "no-transform, public, max-age=%i, s-maxage=%i"%(took*1800/1000, took*9000/1000))
        return resp



    return app



if __name__ == '__main__':
    create_app().run()


