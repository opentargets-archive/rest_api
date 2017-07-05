#!/usr/bin/env python
from gevent import monkey
monkey.patch_all()
import os
import sys
from gevent.wsgi import WSGIServer
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import run_with_reloader
from healthcheck import HealthCheck, EnvironmentDump
from elasticsearch import Elasticsearch

__author__ = 'andreap'

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

from app import create_app
# from app.models import User, Follow, Role, Permission, Post, Comment
from flask.ext.script import Manager, Shell
# from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('OPENTARGETS_API_CONFIG') or 'default')

# add healthcheck and endpoint to read config
health = HealthCheck(app, "/_ah/health")

def es_available():
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
    return es.ping(), "elasticsearch is up"

health.add_check(es_available)

envdump = EnvironmentDump(app, "/environment", 
                          include_python=False, 
                          include_os=False,
                          include_process=False)
manager = Manager(app)
# migrate = Migrate(app, db)

#
# def make_shell_context():
#     return dict(app=app, db=db, User=User, Follow=Follow, Role=Role,
#                 Permission=Permission, Post=Post, Comment=Comment)
# manager.add_command("shell", Shell(make_context=make_shell_context))
# manager.add_command('db', MigrateCommand)


@manager.command
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
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
def runserver(host="127.0.0.1", port=8008):
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


#TODO: consolidate logs of all libraries involved
# from logging import getLogger
# loggers = [app.logger, getLogger('sqlalchemy'),
#            getLogger('otherlibrary')]
# for logger in loggers:
#     logger.addHandler(mail_handler)
#     logger.addHandler(file_handler)

if __name__ == '__main__':
    manager.run()