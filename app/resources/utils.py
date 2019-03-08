from datetime import datetime
from flask import current_app, request
from ipaddr import IPNetwork, IPv4Network, IPv6Network

from app.common.response_templates import CTTVResponse
from app.common.results import RawResult, SimpleResult

from flask_restful import reqparse, Resource


__author__ = 'andreap'

class Ping(Resource):
    parser = reqparse.RequestParser()

    def get(self ):
        return CTTVResponse.OK(RawResult('pong'))

class Version(Resource):
    parser = reqparse.RequestParser()

    def get(self ):
        return CTTVResponse.OK(RawResult(current_app.config['API_VERSION']))

class LogEvent(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('event', type=str, required=True, help="Event to log")

    def get(self):
        mpstore = current_app.extensions['mp_access_store']
        args = self.parser.parse_args()
        event = args['event'][:120]
        ip_resolver = current_app.config['IP_RESOLVER']
        ip = request.remote_addr
        ip_net = IPNetwork(ip)
        resolved_org = ip_resolver['default']
        for net, org in ip_resolver.items():
            if isinstance(net, (IPv4Network, IPv6Network)):
                if net.overlaps(ip_net):
                    resolved_org = org
                    break
        data = dict(org=resolved_org,
                    host=request.host,
                    timestamp=datetime.now(),
                    event=event)
        # esstore.store_event(data)
        mpstore.store_event(data)
        data['timestamp']= str(data['timestamp'])
        return CTTVResponse.OK(SimpleResult(None, data=data))
