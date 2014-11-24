__author__ = 'andreap'

from flask.ext.restful import Api
from flask.ext.restful.utils import cors
from flask_restful_swagger import swagger

def create_api(app, api_version = '0.0', basepath = '', specpath = '' ):
    api = swagger.docs(Api(app,
                           decorators=[cors.crossdomain(origin='*')],
                            ),
                   apiVersion=api_version,
                   api_spec_url=specpath)
    '''define api'''
    # api = restful.Api(app)
    # Wrap the Api with swagger.docs. It is a thin wrapper around the Api class that adds some swagger smarts

    from app.resources.genes import Genes, AvailableGenes,GeneName, GeneEvidenceByEfo
    from app.resources.uniprot import Uniprot,UniprotFromEnsembl, EnsemblFromUniprot
    from app.resources.evidences import Evidence, EvidenceWithEfoAsObject
    from app.resources.mappings import StartFromUniprot, StartFromEnsemblGene, StartFromEnsemblProtein, StartFromEnsemblTranscript
    from app.resources.efo import EfoLabelFromCode, EfoIDFromLabel
    from app.resources.evidenceontology import EcoLabelFromCode
    from app.resources.freetextsearch import FreeTextSearch
    from app.resources.echo import Echo

    api.add_resource(Genes,
                     basepath+'/gene/<string:ensemblid>')
    api.add_resource(GeneEvidenceByEfo,
                     basepath+'/gene-efo/<string:ensemblid>/<string:efocode>')
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
                     basepath+'/evidence/')
    api.add_resource(EvidenceWithEfoAsObject,
                     basepath+'/evidence/efo-object/<string:efocode>')
    # api.add_resource(StartFromUniprot,
    #                  basepath+'/mapping/uniprot/<string:uniprotid>')
    # api.add_resource(StartFromEnsemblGene,
    #                  basepath+'/mapping/ensembl/gene/<string:ensemblgeneid>')
    # api.add_resource(StartFromEnsemblProtein,
    #                  basepath+'/mapping/ensembl/transcript/<string:ensembltranscriptid>')
    # api.add_resource(StartFromEnsemblTranscript,
    #                  basepath+'/mapping/ensembl/protein/<string:ensemblproteinid>')
    api.add_resource(EfoLabelFromCode,
                     basepath+'/efo/code/<string:code>')
    api.add_resource(EfoIDFromLabel,
                     basepath+'/efo/label/<string:label>')
    api.add_resource(EcoLabelFromCode,
                     basepath+'/eco/code/<string:code>')
    api.add_resource(FreeTextSearch,
                     basepath+'/search')
    api.add_resource(Echo,
                     basepath+'/echo')

    return api