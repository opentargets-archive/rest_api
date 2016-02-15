

__author__ = 'andreap'

from flask.ext.restful import Api
# from flask.ext.restful.utils import cors
from flask.ext.cors import CORS
from flask_restful_swagger import swagger
from flask.ext.compress import Compress


def create_api(app, api_version = '0.0', specpath = '' ):
    # app.config['CORS_HEADERS'] = 'Content-Type,Auth-Token'

    'custom errors for flask-restful'
    errors = {'SignatureExpired': {
        'message': "Authentication expired.",
        'status': 419},
    }
    api = Api(app)
    api = swagger.docs(api,
                           # decorators=[cors.crossdomain(origin='*',
                           #                              headers=["Auth-Token",
                           #                                       "Content-Type",
                           #                                       "Authentication"],
                           #                              methods=["GET",
                           #                                       "POST",
                           #                                       "OPTIONS",
                           #                                       "OPTIONS"])],
                           # ),
                           # resources=r'/api/*', allow_headers='Content-Type, Auth-Token'),
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

    from app.resources.genes import GeneInfo
    from app.resources import evidence
    from app.resources.efo import EfoLabelFromCode
    from app.resources.evidenceontology import EcoLabelFromCode
    from app.resources.freetextsearch import FreeTextSearch, AutoComplete, QuickSearch
    from app.resources import association
    from app.resources.auth import RequestToken, ValidateToken
    from app.resources.expression import Expression
    from app.resources.proxy import ProxyEnsembl, ProxyGXA, ProxyPDB, ProxyGeneric
    from app.resources.cache import ClearCache
    from app.resources.utils import Ping, Version





    # api.add_resource(AvailableGenes,
    #                  basepath+'/available-genes')
    api.add_resource(evidence.Evidence,
                     '/public/evidence/getbyid',
                     )
    api.add_resource(evidence.FilterBy,
                     '/public/evidence/filterby',
                     )
    api.add_resource(association.Association,
                     '/public/association/getbyid',
                     )
    api.add_resource(association.FilterBy,
                     '/public/association/filterby',
                     )
    api.add_resource(EfoLabelFromCode,
                     '/private/disease/<string:disease_id>')
    api.add_resource(EcoLabelFromCode,
                     '/private/eco/<string:code>')
    api.add_resource(GeneInfo,
                     '/private/target/<string:target_id>')
    api.add_resource(Expression,
                     '/private/expression')
    api.add_resource(FreeTextSearch,
                     '/public/search')
    api.add_resource(QuickSearch,
                     '/private/quicksearch')
    api.add_resource(AutoComplete,
                     '/private/autocomplete')
    api.add_resource(RequestToken,
                     '/public/auth/request_token')
    api.add_resource(ValidateToken,
                     '/public/auth/validate_token')
    api.add_resource(ClearCache,
                     '/private/cache/clear')
    api.add_resource(Ping,
                     '/public/utils/ping')
    api.add_resource(Version,
                     '/public/utils/version')
    #
    # api.add_resource(ProxyEnsembl,
    #                  '/proxy/ensembl/<path:url>')
    # api.add_resource(ProxyGXA,
    #                  '/proxy/gxa/<path:url>')
    # api.add_resource(ProxyPDB,
    #                  '/proxy/pdbe/<path:url>')
    # api.add_resource(ProxyEPMC,
    #                  '/proxy/epmc/<path:url>')
    # api.add_resource(ProxyGeneric,
    #                  '/proxy/generic/<path:url>')
    return api