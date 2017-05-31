from datetime import datetime
from flask import current_app, request
from ipaddr import IPNetwork, IPv4Network, IPv6Network

from app.common.auth import TokenAuthentication
from app.common.response_templates import CTTVResponse
from app.common.results import RawResult, SimpleResult
from flask.ext import restful
from flask.ext.restful import reqparse
from app.common.rate_limit import rate_limit, RateLimiter

__author__ = 'andreap'

class Ping(restful.Resource):
    parser = reqparse.RequestParser()

    @rate_limit
    def get(self ):
        return CTTVResponse.OK(RawResult('something nice'))

class Version(restful.Resource):
    parser = reqparse.RequestParser()

    @rate_limit
    def get(self ):
        return CTTVResponse.OK(RawResult(current_app.config['API_VERSION']))

class LogEvent(restful.Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('event', type=str, required=True, help="Event to log")

    @rate_limit
    def get(self):
        esstore = current_app.extensions['es_access_store']
        mpstore = current_app.extensions['mp_access_store']
        args = self.parser.parse_args()
        event = args['event'][:120]
        auth_token=request.headers.get('Auth-Token')
        ip_resolver = current_app.config['IP_RESOLVER']
        ip = RateLimiter.get_remote_addr()
        ip_net = IPNetwork(ip)
        resolved_org = ip_resolver['default']
        for net, org in ip_resolver.items():
            if isinstance(net, (IPv4Network, IPv6Network)):
                if net.overlaps(ip_net):
                    resolved_org = org
                    break
        data = dict(ip=ip,
                    org=resolved_org,
                    host=request.host,
                    timestamp=datetime.now(),
                    event=event)
        if auth_token:
            payload = TokenAuthentication.get_payload_from_token(auth_token)
            data['app_name'] = payload['app_name']
        # esstore.store_event(data)
        mpstore.store_event(data)
        data['timestamp']= str(data['timestamp'])
        return CTTVResponse.OK(SimpleResult(None, data=data))
