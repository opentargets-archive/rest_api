__author__ = 'andreap'

from flask import Flask
from flask.ext import restful
from elasticsearch import Elasticsearch
from flask import g
from flask_restful_swagger import swagger




#TODO Use this to document api: https://github.com/rantav/flask-restful-swagger

app = Flask(__name__)
app.config.from_pyfile('../common/config.py')
app.extensions['elasticsearch'] = Elasticsearch(app.config['ELASTICSEARCH_URL'])
api_version = app.config['API_VERSION']
basepath = '/api/public/v'+api_version
specpath = basepath +'/spec'

if app.config['PROFILE'] == True:
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

# def get_db():
#     """Opens a new database connection if there is none yet for the
#     current application context.
#     """
#     es = getattr(g, '_es', None)
#     if es is None:
#         es = g._es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
#     return es
#
# @app.teardown_appcontext
# def close_db(error):
#     """Closes the database again at the end of the request."""
#     if hasattr(g, 'es'):
#         g.es.close()


'''define api'''
# api = restful.Api(app)
# Wrap the Api with swagger.docs. It is a thin wrapper around the Api class that adds some swagger smarts
api = swagger.docs(restful.Api(app),
                   apiVersion=api_version,
                   api_spec_url=specpath)



from resources.genes import Genes, AvailableGenes, EfficientAvailableGenes
from resources.uniprot import Uniprot
api.add_resource(Genes,
                 basepath+'/genes/<string:ensemblid>')
api.add_resource(Uniprot,
                 basepath+'/uniprot/<string:uniprotid>')
api.add_resource(AvailableGenes,
                 basepath+'/available-genes')
api.add_resource(EfficientAvailableGenes,
                 basepath+'/efficient-available-genes')

if __name__ == '__main__':
    app.run()


