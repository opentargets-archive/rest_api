__author__ = 'andreap'

from flask.ext.restful import Api
from flask.ext.restful.utils import cors
from flask_restful_swagger import swagger

def create_api(app, api_version = '0.0', specpath = '' ):
    api = swagger.docs(Api(app,
                           decorators=[cors.crossdomain(origin='*')],
                            ),
                       basePath='http://localhost:8080',
                       resourcePath='/',
                       produces=["application/json", "text/xml"],
                       api_spec_url=specpath,
                       description='CTTV REST API',
                       apiVersion=api_version,
                       swaggerVersion=1.2,
                   )
    '''define api'''
    # api = restful.Api(app)
    # Wrap the Api with swagger.docs. It is a thin wrapper around the Api class that adds some swagger smarts

    from app.resources.genes import Genes, AvailableGenes,GeneName, GeneEvidenceByEfo
    from app.resources.uniprot import Uniprot,UniprotFromEnsembl, EnsemblFromUniprot
    from app.resources.evidences import Evidence, Evidences, EvidenceWithEfoAsObject
    from app.resources.efo import EfoLabelFromCode, EfoIDFromLabel
    from app.resources.evidenceontology import EcoLabelFromCode
    from app.resources.freetextsearch import FreeTextSearch, AutoComplete
    from app.resources.echo import Echo






    # api.add_resource(AvailableGenes,
    #                  basepath+'/available-genes')
    api.add_resource(Evidence,
                     '/getbyid'
                     )
    api.add_resource(Evidences,
                     '/filterby')
    # api.add_resource(Genes,
    #                  basepath+'/evidences-gene/<string:gene>')
    # api.add_resource(GeneEvidenceByEfo,
    #                  basepath+'/evidences-gene-efo/<string:ensemblid>/<string:efocode>')
    # api.add_resource(StartFromUniprot,
    #                  basepath+'/mapping/uniprot/<string:uniprotid>')
    # api.add_resource(StartFromEnsemblGene,
    # api.add_resource(EfoLabelFromCode,
    #                  basepath+'/efo/code/<string:code>')
    api.add_resource(EfoIDFromLabel,
                     '/efo/label/<string:label>')
    api.add_resource(EcoLabelFromCode,
                     '/eco/code/<string:code>')
    api.add_resource(UniprotFromEnsembl,
                     '/mapping/uniprot/from-ensembl/<string:ensemblid>')
    api.add_resource(EnsemblFromUniprot,
                     '/mapping/uniprot/to-ensembl/<string:uniprotid>')
    api.add_resource(FreeTextSearch,
                     '/search')
    api.add_resource(AutoComplete,
                     '/autocomplete')
    api.add_resource(Echo,
                     '/echo')

    return api