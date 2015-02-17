
__author__ = 'andreap'




from flask import Flask, redirect, Blueprint
# from flask.ext.bootstrap import Bootstrap
# from flask.ext.mail import Mail
# from flask.ext.moment import Moment
# from flask.ext.sqlalchemy import SQLAlchemy
# from flask.ext.login import LoginManager
# from flask.ext.pagedown import PageDown
from config import config
import logging

# bootstrap = Bootstrap()
# mail = Mail()
# moment = Moment()
# db = SQLAlchemy()
# pagedown = PageDown()

# login_manager = LoginManager()
# login_manager.session_protection = 'strong'
# login_manager.login_view = 'auth.login'


from elasticsearch import Elasticsearch
from common.elasticsearchclient import esQuery
from api import create_api


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    es = Elasticsearch(app.config['ELASTICSEARCH_URL'],
                        # # sniff before doing anything
                        # sniff_on_start=True,
                        # # refresh nodes after a node fails to respond
                        # sniff_on_connection_fail=True,
                        # # and also every 60 seconds
                        # sniffer_timeout=60
                        )
    log_level = logging.INFO
    if app.config['DEBUG']:
        log_level = logging.DEBUG
    app.extensions['esquery'] = esQuery(es,
                                        index_data = app.config['ELASTICSEARCH_DATA_INDEX_NAME'],
                                        index_efo = app.config['ELASTICSEARCH_EFO_LABEL_INDEX_NAME'],
                                        index_eco = app.config['ELASTICSEARCH_ECO_INDEX_NAME'],
                                        index_genename = app.config['ELASTICSEARCH_GENE_NAME_INDEX_NAME'],
                                        docname_data = app.config['ELASTICSEARCH_DATA_DOC_NAME'],
                                        docname_efo = app.config['ELASTICSEARCH_EFO_LABEL_DOC_NAME'],
                                        docname_eco = app.config['ELASTICSEARCH_ECO_DOC_NAME'],
                                        docname_genename = app.config['ELASTICSEARCH_GENE_NAME_DOC_NAME'],
                                        log_level= log_level,
                                        )
    api_version = app.config['API_VERSION']
    basepath = app.config['PUBLIC_API_BASE_PATH']+api_version
    latest_blueprint = Blueprint('latest', __name__)


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
    # if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
    #     from flask.ext.sslify import SSLify
    #     sslify = SSLify(app)
    #
    # from .main import main as main_blueprint
    # app.register_blueprint(main_blueprint)
    #
    # from .auth import auth as auth_blueprint
    # app.register_blueprint(auth_blueprint, url_prefix='/auth')
    #
    # from .api_1_0 import api as api_1_0_blueprint
    # app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    create_api(latest_blueprint, api_version, specpath)

    app.register_blueprint(latest_blueprint, url_prefix='/api/latest')

    @app.route('/api-docs')
    def docs():
      return redirect('/api/latest/cttv.html')


    return app





if __name__ == '__main__':
    create_app().run()


