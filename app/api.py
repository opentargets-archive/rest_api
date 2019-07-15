from app.resources.enrichment import EnrichmentTargets
from app.resources.relation import  Relations
from app.resources.utils import LogEvent
from config import Config
from app.common import load_tissue_map

__author__ = 'andreap'

from flask_restful import Api


def create_api(app, api_version = '0.0', specpath = '' ):
    # app.config['CORS_HEADERS'] = 'Content-Type,Auth-Token'

    Config.ES_TISSUE_MAP = load_tissue_map()
    'custom errors for flask-restful'
    # errors = {'SignatureExpired': {
    #     'message': "Authentication expired.",
    #     'status': 419},
    # }
    errors ={}
    api = Api(app,
              errors=errors)

    '''define api'''

    from app.resources.target import TargetInfo, TargetInfoSingle
    from app.resources import evidence
    from app.resources.efo import EfoLabelFromCode
    from app.resources.drug import Drug
    from app.resources.evidenceontology import EcoLabelFromCode
    from app.resources.freetextsearch import FreeTextSearch, BestHitSearch, AutoComplete, QuickSearch
    from app.resources import association
    from app.resources.expression import Expression
    from app.resources.cache import ClearCache
    from app.resources.utils import Ping, Version
    from app.resources.relation import RelationTargetSingle, RelationDiseaseSingle
    from app.resources.stats import Stats
    from app.resources.metrics import Metrics
    from app.resources.therapeuticarea import TherapeuticAreas

    # api.add_resource(AvailableGenes,
    #                  basepath+'/available-genes')
    api.add_resource(evidence.Evidence,
                     '/public/evidence',
                     )
    api.add_resource(evidence.FilterBy,
                     '/public/evidence/filter',
                      endpoint="evidence-filter"
                     )

    api.add_resource(evidence.DrugEvidence,
                     '/public/evidence/known_drug'
                     )

    api.add_resource(association.Association,
                     '/public/association',
                     )
    api.add_resource(association.FilterBy,
                     '/public/association/filter',
                     endpoint="association-filter"
                     )
    api.add_resource(EfoLabelFromCode,
                     '/private/disease/<string:disease_id>')
    api.add_resource(EfoLabelFromCode,
                     '/private/disease',
                     endpoint="disease-facets"
                    )
    api.add_resource(Drug,
                     '/private/drug/<string:drug_id>')
    api.add_resource(EcoLabelFromCode,
                     '/private/eco/<string:code>')
    api.add_resource(TargetInfoSingle,
                     '/private/target/<string:target_id>')
    api.add_resource(TargetInfo,
                     '/private/target')
    api.add_resource(Expression,
                     '/private/target/expression')
    api.add_resource(BestHitSearch,
                     '/private/besthitsearch')
    api.add_resource(FreeTextSearch,
                     '/public/search')
    api.add_resource(QuickSearch,
                     '/private/quicksearch')
    api.add_resource(AutoComplete,
                     '/private/autocomplete')
    api.add_resource(ClearCache,
                     '/private/cache/clear')
    api.add_resource(Ping,
                     '/public/utils/ping')
    api.add_resource(Version,
                     '/public/utils/version')
    api.add_resource(Stats,
                     '/public/utils/stats')
    api.add_resource(Metrics,
                     '/public/utils/metrics')
    api.add_resource(LogEvent,
                     '/private/utils/logevent')
    api.add_resource(RelationTargetSingle,
                     '/private/relation/target/<string:target_id>')
    api.add_resource(Relations,
                     '/private/relation')
    api.add_resource(RelationDiseaseSingle,
                     '/private/relation/disease/<string:disease_id>')
    api.add_resource(EnrichmentTargets,
                     '/private/enrichment/targets')
    api.add_resource(TherapeuticAreas,
                     '/public/utils/therapeuticareas')

    return api
