from flask import current_app
from ipaddr import IPNetwork, IPv4Network, IPv6Network

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
        return CTTVResponse.OK(RawResult('pong'))

class Version(restful.Resource):
    parser = reqparse.RequestParser()

    @rate_limit
    def get(self ):
        return CTTVResponse.OK(RawResult(current_app.config['API_VERSION']))

class LogEvent(restful.Resource):
    parser = reqparse.RequestParser()

    @rate_limit
    def get(self):
        ip_resolver = current_app.config['IP_RESOLVER']
        ip = RateLimiter.get_remote_addr()
        ip_net = IPNetwork(ip)
        resolved_org = ip_resolver['default']
        for net, org in ip_resolver.items():
            if isinstance(net, (IPv4Network, IPv6Network)):
                if net.overlaps(ip_net):
                    resolved_org = org
                    break
        return CTTVResponse.OK(SimpleResult(None, data = dict(ip=ip, org=resolved_org)))
