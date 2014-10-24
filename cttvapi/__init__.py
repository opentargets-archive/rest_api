__author__ = 'andreap'

from flask import Flask
from flask.ext import restful
from elasticsearch import Elasticsearch
from flask import g


#TODO Use this to document api: https://github.com/rantav/flask-restful-swagger

app = Flask(__name__)
app.config.from_pyfile('../common/config.py')
app.extensions['elasticsearch'] = Elasticsearch(app.config['ELASTICSEARCH_URL'])

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    es = getattr(g, '_es', None)
    if es is None:
        es = g._es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
    return es

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'es'):
        g.es.close()


'''define api'''
api = restful.Api(app)

basepath = '/api/public/v0.1'
from resources.genes import Genes
from resources.uniprot import Uniprot
api.add_resource(Genes,
                 basepath+'/genes',
                 basepath+'/genes/<string:ensemblid>')
api.add_resource(Uniprot,
                 basepath+'/uniprot/<string:uniprotid>')



if __name__ == '__main__':
    app.run()


