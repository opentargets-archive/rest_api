import csv
import os
from collections import defaultdict
from datetime import datetime
from functools import wraps

import flask_restful as restful
import requests
import json, yaml
from flask import Flask, redirect, Blueprint, send_file, g, request, jsonify, render_template
from flask_compress import Compress
from redislite import Redis
from app.common.auth import AuthKey
from app.common.signals import LogApiCallWeight, IP2Org, MixPanelStore, esStore
from app.common.datatypes import DataTypes
from app.common.proxy import ProxyHandler
from app.common.rate_limit import RateLimiter, ceil_dt_to_future_time
from app.common.rate_limit import increment_call_rate
from app.common.scoring_conf import DataSourceScoring
from config import config, Config
from elasticsearch import Elasticsearch
from app.common.elasticsearchclient import esQuery, InternalCache
from api import create_api
from werkzeug.contrib.cache import SimpleCache, FileSystemCache, RedisCache
from app.common.signals import LogException
from ipaddr import IPNetwork
from mixpanel import Mixpanel
from mixpanel_async import AsyncBufferedConsumer

# from flask.ext.cors import CORS
# from flask_limiter import Limiter
# from flask.ext.login import LoginManager
# login_manager = LoginManager()
# login_manager.session_protection = 'strong'
# login_manager.login_view = 'auth.login'


__author__ = 'andreap'

def get_http_exception_handler(app):
    """Overrides the default http exception handler to return JSON."""
    handle_http_exception = app.handle_http_exception
    @wraps(handle_http_exception)
    def ret_val(exception):
        exc = handle_http_exception(exception)
        resp = jsonify({'code':exc.code, 'message':exc.description})
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.headers.add('Access-Control-Allow-Headers', 'Content-Type,Auth-Token')
        resp.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')

        return resp, exc.code
    return ret_val

def do_not_cache(request):
    cache_skip = [Config.NO_CACHE_PARAMS,
                  '/request_token?',
                  ]
    for skip in cache_skip:
        if skip in str(request):
            return True
    return False


def create_app(config_name):
    app = Flask(__name__, static_url_path='')
    # This first loads the configuration from eg. config['development'] which corresponds to the DevelopmentConfig class in the config.py
    app.config.from_object(config[config_name])
    # Then you can override the values with the contents of the file the OPENTARGETS_API_LOCAL_SETTINGS environment variable points to.
    # For eg:
    # $ export OPENTARGETS_API_LOCAL_SETTINGS=/path/to/settings.cfg
    #
    # where settings.cfg looks like:
    #
    # DEBUG = False
    # SECRET_KEY = 'foo'
    #
    app.config.from_envvar("OPENTARGETS_API_LOCAL_SETTINGS", silent=True)

    config[config_name].init_app(app)
    api_version = app.config['API_VERSION']
    api_version_minor = app.config['API_VERSION_MINOR']


    app.logger.info('looking for elasticsearch at: %s' % app.config['ELASTICSEARCH_URL'])


    app.extensions['redis-core'] = Redis(app.config['REDIS_SERVER_PATH'], db=0) #served data
    app.extensions['redis-service'] = Redis(app.config['REDIS_SERVER_PATH'], db=1) #cache, rate limit and internal things
    app.extensions['redis-user'] = Redis(app.config['REDIS_SERVER_PATH'], db=2)# user info
    '''setup cache'''
    app.extensions['redis-service'].config_set('save','')
    app.extensions['redis-service'].config_set('appendonly', 'no')
    icache = InternalCache(app.extensions['redis-service'],
                           str(api_version_minor))
    ip2org = IP2Org(icache)
    if app.config['ELASTICSEARCH_URL']:
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'],
                           # # sniff before doing anything
                           # sniff_on_start=True,
                           # # refresh nodes after a node fails to respond
                           # sniff_on_connection_fail=True,
                           # # and also every 60 seconds
                           # sniffer_timeout=60
                           timeout=60 * 20,
                           maxsize=32,
                           )
    else:
        es = None
    '''elasticsearch handlers'''
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
                                        # docname_search_target=app.config['ELASTICSEARCH_DATA_SEARCH_TARGET_DOC_NAME'],
                                        # docname_search_disease=app.config['ELASTICSEARCH_DATA_SEARCH_DISEASE_DOC_NAME'],
                                        docname_relation=app.config['ELASTICSEARCH_DATA_RELATION_DOC_NAME'],
                                        log_level=app.logger.getEffectiveLevel(),
                                        cache=icache
                                        )

    app.extensions['es_access_store'] = esStore(es,
                                        eventlog_index=app.config['ELASTICSEARCH_LOG_EVENT_INDEX_NAME'],
                                        ip2org=ip2org,
                                        )
    '''mixpanel handlers'''
    if Config.MIXPANEL_TOKEN:
        mp = Mixpanel(Config.MIXPANEL_TOKEN, consumer=AsyncBufferedConsumer())
        app.extensions['mixpanel']= mp
        app.extensions['mp_access_store'] = MixPanelStore(mp,
                                            ip2org=ip2org,
                                            )


        app.extensions['proxy'] = ProxyHandler(allowed_targets=app.config['PROXY_SETTINGS']['allowed_targets'],
                                               allowed_domains=app.config['PROXY_SETTINGS']['allowed_domains'],
                                               allowed_request_domains=app.config['PROXY_SETTINGS']['allowed_request_domains'])

    # basepath = app.config['PUBLIC_API_BASE_PATH']+api_version
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
    csvfile = None
    if Config.GITHUB_AUTH_TOKEN:
        r = requests.get('https://api.github.com/repos/opentargets/rest_api_auth/contents/rate_limit.csv',
                         headers = {'Authorization': 'token %s'%Config.GITHUB_AUTH_TOKEN,
                                    'Accept': 'application/vnd.github.v3.raw'})
        if r.ok:
            csvfile = r.text.split('\n')
            app.logger.info('Retrieved rate limit file from github remote')
        else:
            app.logger.warning('Cannot retrieve rate limit file from remote, SKIPPED!')
    elif os.path.exists(rate_limit_file):
        csvfile = open(rate_limit_file)
        app.logger.info('Using dummy rate limit file')

    if csvfile is None:
        app.logger.error('cannot find rate limit file: %s. RATE LIMIT QUOTA LOAD SKIPPED!'%rate_limit_file)
    else:
        reader = csv.DictReader(csvfile)
        for row in reader:
            auth_key = AuthKey(**row)
            app.extensions['redis-user'].set(auth_key.get_key(), json.dumps(auth_key.__dict__))
        try:
            csvfile.close()
        except:
            pass
        app.logger.info('succesfully loaded rate limit file')


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


    '''set the right prefixes'''

    create_api(latest_blueprint, api_version, specpath)
    create_api(current_version_blueprint, api_version, specpath)
    create_api(current_minor_version_blueprint, api_version_minor, specpath)

    # app.register_blueprint(latest_blueprint, url_prefix='/latest/platform')
    app.register_blueprint(current_version_blueprint, url_prefix='/v'+str(api_version) + '/platform')
    app.register_blueprint(current_minor_version_blueprint, url_prefix='/v'+str(api_version_minor) + '/platform')


    '''serve the static docs'''

    try:
        '''
        NOTE: this file gets created only at deployment time
        '''
        openapi_def = yaml.load(file('app/static/openapi.yaml', 'r'))
        app.logger.info('parsing swagger from static/openapi.yaml')

    except IOError:
        '''if we are not deployed, then simply use the template'''
        openapi_def = yaml.load(file('openapi.template.yaml', 'r'))
        app.logger.error('parsing swagger from openapi.template.yaml')

    with open("api-description.md", "r") as f:
        desc = f.read()
    openapi_def['info']['description'] = desc
    openapi_def['basePath'] = '/v%s' % str(api_version)
    @app.route('/v%s/platform/swagger' % str(api_version))
    def serve_swagger(apiversion=api_version):
        return jsonify(openapi_def)


    @app.route('/v%s/platform/docs' % str(api_version))
    def render_redoc(apiversion=api_version):
        return render_template('docs.html',api_version=apiversion)

    @app.route('/v%s/platform/docs/swagger-ui' % str(api_version))
    def render_swaggerui(apiversion=api_version):
        return render_template('swaggerui.html',api_version=apiversion)

    '''pre and post-request'''


    @app.before_request
    def before_request():
        g.request_start = datetime.now()
    @app.after_request
    def after(resp):
        try:
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
            resp.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            if do_not_cache(request):# do not cache in the browser
                resp.headers.add('Cache-Control', "no-cache, must-revalidate, max-age=0")
            else:
                resp.headers.add('Cache-Control', "no-transform, public, max-age=%i, s-maxage=%i"%(took*1800/1000, took*9000/1000))
            return resp

        except Exception as e:
            app.logger.exception('failed request teardown function', str(e))
            return resp



    # Override the HTTP exception handler.
    app.handle_http_exception = get_http_exception_handler(app)
    return app


if __name__ == '__main__':
    create_app().run()


