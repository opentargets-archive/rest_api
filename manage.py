#!/usr/bin/env python
from flask import url_for
from gevent import monkey
monkey.patch_all()
import os
import sys
from gevent.wsgi import WSGIServer
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import run_with_reloader
from healthcheck import HealthCheck, EnvironmentDump
from elasticsearch import Elasticsearch
from envparse import env

__author__ = 'andreap'

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()


from app import create_app
# from app.models import User, Follow, Role, Permission, Post, Comment
from flask.ext.script import Manager, Shell
# from flask.ext.migrate import Migrate, MigrateCommand

# look for a .env file, where we might have specified OT_API_CONFIG
env.read_envfile()
app = create_app(env('OPENTARGETS_API_CONFIG', default='default'))

# add healthcheck and endpoint to read config
health = HealthCheck(app, "/_ah/health")

def es_available():
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
    if es.ping():
        return True, "elasticsearch is up!"
    else:
        return False, "cannot find elasticsearch :("

def es_index_exists():
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
    if es.indices.exists('%s*' % app.config['DATA_VERSION']):
        return True, "found indices beginning with %s" % app.config['DATA_VERSION']
    else:
        #NOTE: passing true, otherwise google appengine will not make any path available
        return True, "cannot find indices..."

def dummy():
    return True, "we are live!"

health.add_check(dummy)
health.add_check(es_available)
health.add_check(es_index_exists)

envdump = EnvironmentDump(app, "/environment",
                          include_python=False,
                          include_os=False,
                          include_process=False)
manager = Manager(app)


@manager.command
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run(ssl_context=('data/cert/server.crt', 'data/cert/server.crt'))

@manager.command
def runserver(host="127.0.0.1", port=8080):
    """Run a gevent-based WSGI server."""
    port = int(port)

    wrapped_app = app
    if app.config.get("DEBUG", True):
        #it is necessary to do this for the debug to work, since the classic
        # flask debugger does not operate when running the app from
        # a WSGIServer() call.
        wrapped_app = DebuggedApplication(app)

    server = WSGIServer(listener=(host, port), application=wrapped_app,)

    def serve():
        print(" * Running on http://%s:%d/" % (host, port))
        server.serve_forever()

    if app.debug:
        # the watchdog reloader (with watchdog==0.8.3) appears to hang on
        # Windows 8.1, so we're using stat instead
        run_with_reloader(
            serve, reloader_type="stat" if sys.platform == "win32" else "auto")
    else:
        serve()


@manager.command
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)

    for line in sorted(output):
        print line

if __name__ == '__main__':
    manager.run()
