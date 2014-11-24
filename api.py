
__author__ = 'andreap'

from flask import Flask
from flask.ext import restful
from elasticsearch import Elasticsearch
from flask_restful_swagger import swagger



app = Flask(__name__)
app.config.from_pyfile('common/config.py')
app.extensions['elasticsearch'] = Elasticsearch(app.config['ELASTICSEARCH_URL'])
                                                # ,
                                                # # sniff before doing anything
                                                # sniff_on_start=True,
                                                # # refresh nodes after a node fails to respond
                                                # sniff_on_connection_fail=True,
                                                # # and also every 60 seconds
                                                # sniffer_timeout=60)
api_version = app.config['API_VERSION']
basepath = app.config['PUBLIC_API_BASE_PATH']+api_version
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
from app.resources.genes import Genes, AvailableGenes,GeneName
from app.resources.uniprot import Uniprot,UniprotFromEnsembl, EnsemblFromUniprot
from app.resources.evidences import Evidence, EvidenceWithEfoAsObject
from app.resources.mappings import StartFromUniprot, StartFromEnsemblGene, StartFromEnsemblProtein, StartFromEnsemblTranscript
from app.resources.efo import EfoLabelFromCode, EfoLabelFromID, EfoIDFromLabel
from app.resources.evidenceontology import EcoLabelFromCode
from app.resources.freetextsearch import FreeTextSearch
from app.resources.echo import Echo

api.add_resource(Genes,
                 basepath+'/gene/<string:ensemblid>')
api.add_resource(GeneName,
                 basepath+'/genename/<string:genename>')
api.add_resource(Uniprot,
                 basepath+'/uniprot/<string:uniprotid>')
api.add_resource(UniprotFromEnsembl,
                 basepath+'/uniprot/from-ensembl/<string:ensemblid>')
api.add_resource(EnsemblFromUniprot,
                 basepath+'/uniprot/to-ensembl/<string:uniprotid>')
api.add_resource(AvailableGenes,
                 basepath+'/available-genes')
api.add_resource(Evidence,
                 basepath+'/evidence/<int:evidenceid>')
api.add_resource(EvidenceWithEfoAsObject,
                 basepath+'/evidence/efo-object/<string:efocode>')
api.add_resource(StartFromUniprot,
                 basepath+'/mapping/uniprot/<string:uniprotid>')
api.add_resource(StartFromEnsemblGene,
                 basepath+'/mapping/ensembl/gene/<string:ensemblgeneid>')
api.add_resource(StartFromEnsemblProtein,
                 basepath+'/mapping/ensembl/transcript/<string:ensembltranscriptid>')
api.add_resource(StartFromEnsemblTranscript,
                 basepath+'/mapping/ensembl/protein/<string:ensemblproteinid>')
api.add_resource(EfoLabelFromID,
                 basepath+'/efo/id/<string:efoid>')
api.add_resource(EfoLabelFromCode,
                 basepath+'/efo/code/<string:code>')
api.add_resource(EfoIDFromLabel,
                 basepath+'/efo/label/<string:efolabel>')
api.add_resource(EcoLabelFromCode,
                 basepath+'/eco/id/<string:ecoid>')
api.add_resource(FreeTextSearch,
                 basepath+'/search')
api.add_resource(Echo,
                 basepath+'/echo')

if __name__ == '__main__':
    app.run()


