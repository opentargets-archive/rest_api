# Configure the module according to your needs
import socket
import ujson as json
from datetime import datetime

from flask import request, current_app
from werkzeug.exceptions import HTTPException

from config import Config
from app.common.utils import get_remote_addr




class BaseDatadogSignal(object):
    def __init__(self):
        try:
            self.stats = current_app.extensions['datadog']
        except KeyError:
            self.stats = None

class BaseMixPanelSignal(object):
    def __init__(self):
        try:
            self.stats = current_app.extensions['mixpanel']
        except KeyError:
            self.stats = None

class RateLimitExceeded(BaseMixPanelSignal):
    def __init__(self,
                 rate_limiter):

        super(RateLimitExceeded, self).__init__()
        if self.stats:
            title = "Api limit exceeded"
            text = json.dumps(rate_limiter.__dict__)
            tags = ['version:'+str(Config.API_VERSION_MINOR),
                    'application:rest-api',
                    'api-key:'+rate_limiter._auth_key.id]
            ip = get_remote_addr()

            self.stats.track(rate_limiter._auth_key.id,
                             'api_limit_exceeded',
                             properties=dict(title=title,
                                             text=text,
                                             tags=tags,
                                             alert_type='error',
                                             ip=ip,
                                             ignore_time = True,))


            # self.stats.event(title=title,
            #                  text=text,
            #                  tags=tags,
            #                  alert_type='error')
            # self.stats.increment('api.auth.rate.limit.exceeded',
            #                 tags=tags,)



class LogApiCallWeight(BaseMixPanelSignal):
    def __init__(self,
                 value):
        super(LogApiCallWeight, self).__init__()
        if self.stats:
            tags = ['version:'+str(Config.API_VERSION_MINOR), 'application:rest-api']
            ip = get_remote_addr()

            self.stats.track(get_remote_addr(),
                             'api_call_weight',
                             properties=dict(value=value,
                                             tags=tags,
                                             ip=ip,
                                             ignore_time = True,
                                             ))

            # self.stats.increment('api.call.weight',
            #                 value=value,
            #                 tags=tags,)

class LogApiCallCount(BaseMixPanelSignal):
    def __init__(self, rate_limiter):
        super(LogApiCallCount, self).__init__()
        if self.stats:
            tags = ['version:'+str(Config.API_VERSION_MINOR),
                    'application:rest-api',
                    'api-key:'+rate_limiter._auth_key.id,
                    'method:'+request.environ['REQUEST_METHOD'],
                    'endpoint:'+request.url_rule.rule.split('<')[0].split(request.blueprint)[1]]
            ip = get_remote_addr()
            self.stats.track(get_remote_addr(),
                             'api_call_count',
                             properties=dict(tags=tags,
                                             ip=ip,
                                             ignore_time = True,
                                             ))

            # self.stats.increment('api.call.count',
            #                 tags=tags,)



class LogApiTokenServed(BaseMixPanelSignal):
    def __init__(self,):
        super(LogApiTokenServed, self).__init__()
        if self.stats:
            tags = ['version:'+str(Config.API_VERSION_MINOR), 'application:rest-api']
            ip = get_remote_addr()
            self.stats.track(get_remote_addr(),
                             'api_auth_token_served',
                             properties=dict(tags=tags,
                                             ip=ip,
                                             ignore_time = True,
                                             ))
            # self.stats.increment('api.auth.token.served',
            #                 tags=tags,)

class LogApiTokenExpired(BaseMixPanelSignal):
    def __init__(self,):
        super(LogApiTokenExpired, self).__init__()
        if self.stats:
            tags = ['version:'+str(Config.API_VERSION_MINOR), 'application:rest-api']
            ip = get_remote_addr()
            self.stats.track(get_remote_addr(),
                             'api_auth_token_expired',
                             properties=dict(tags=tags,
                                             ip=ip,
                                             ignore_time=True,
                                             ))
            # self.stats.increment('api.auth.token.expired',
            #                 tags=tags,)

class LogApiTokenInvalid(BaseMixPanelSignal):
    def __init__(self,
                 message):
        super(LogApiTokenInvalid, self).__init__()
        if self.stats:

            message['host']= request.environ.get('HTTP_HOST').split(':')[0]

            title = "Invalid token used"
            text = json.dumps(message)
            tags = ['version:'+str(Config.API_VERSION_MINOR), 'application:rest-api']
            ip = get_remote_addr()
            self.stats.track(ip,
                             'api_auth_token_invalid',
                             properties=dict(title=title,
                                             text=text,
                                             tags=tags,
                                             alert_type='error',
                                             ip=ip,
                                             ignore_time = True,
                                             ))

            # self.stats.event(title=title,
            #                  text=text,
            #                  tags=tags,
            #                  alert_type='error')
            # self.stats.increment('api.auth.token.invalid',
            #                 tags=tags,)

class LogApiTokenInvalidDomain(BaseMixPanelSignal):
    def __init__(self,
                 message):
        super(LogApiTokenInvalidDomain, self).__init__()
        if self.stats:
            message['host']= request.environ.get('HTTP_HOST').split(':')[0]

            title = "Invalid token used"
            text = json.dumps(message)
            tags = ['version:'+str(Config.API_VERSION_MINOR), 'application:rest-api']
            ip = get_remote_addr()
            self.stats.track(ip,
                             'api_auth_token_invalid_domain',
                             properties=dict(title=title,
                                             text=text,
                                             tags=tags,
                                             alert_type='error',
                                             ip=ip,
                                             ignore_time=True,
                                             ))

            # self.stats.event(title=title,
            #                  text=text,
            #                  tags=tags,
            #                  alert_type='error')
            # self.stats.increment('api.auth.token.invalid.domain',
            #                 tags=tags,)

class LogException(BaseMixPanelSignal):
    def __init__(self,
                 exception):

        super(LogException, self).__init__()
        if self.stats:
            title = "Exception in REST API"
            import traceback
            try:
                raise exception
            except:
                tb = traceback.format_exc(limit=3)
                #TODO: the traceback reporting is not working as expexted. might need to be called from a subclassed Flask app, and not from a signal
                #http://flask.pocoo.org/snippets/127/

            plain_exception = '%s: %s'%(exception.__class__.__name__, str(exception))
            text = json.dumps(dict(#traceback= tb,
                                       url = str(request.url),
                                       method = str(request.method),
                                       args = request.args,
                                       headers = request.headers.items(),
                                       exception_class = exception.__class__.__name__,
                                       exception = plain_exception,
                                       )
                                  )
            tags = ['version:'+str(Config.API_VERSION_MINOR),
                    'application:rest-api',
                    exception.__class__.__name__
                    ]

            alert_type ='error'
            if isinstance(exception, HTTPException):
                if str(exception.code)[0] =='4':
                    alert_type = 'warning'
                    title = '4XX error in REST API'

            ip = get_remote_addr()
            self.stats.track(ip,
                             'api_error',
                             properties=dict(title=title,
                                             text=text,
                                             tags=tags,
                                             alert_type=alert_type,
                                             ip=ip,
                                             ignore_time=True,
                                             ))

            # self.stats.event(title=title,
            #                  text=text,
            #                  tags=tags,
            #                  alert_type=alert_type)
            # self.stats.increment('api.error',
            #                 tags=tags,)


class IP2Org(object):
    def __init__(self,
                 ip_cache,
                 ):
        self.ip_cache = ip_cache

    def get_ip_org(self, ip):
        host_from_ip = self.ip_cache.get(ip)
        if host_from_ip is None:
            try:
                host_from_ip = socket.gethostbyaddr(ip)[0]
                self.ip_cache.set(ip, host_from_ip, 24 * 60 * 60)
            except:
                pass
        return host_from_ip


class esStore(object):
    def __init__(self,
                 es,
                 eventlog_index,
                 ip2org,
                 ):
        self.es = es
        self.eventlog_index = eventlog_index
        self.ip2org = ip2org

    def store_event(self, event):
        event['org_from_ip'] = self.ip2org.get_ip_org(event['ip'])
        index_name = self.eventlog_index + '_' + '-'.join(map(str, datetime.now().isocalendar()[:2]))
        self.es.index(index=index_name,
                      doc_type='event',
                      body=event)




class MixPanelStore():
    def __init__(self,
                 mp,
                 ip2org):
        self.ip2org = ip2org
        self.mp = mp

    def store_event(self, event):
        event['org_from_ip'] = self.ip2org.get_ip_org(event['ip'])
        self.mp.track(event['ip'],
                      'api_event',
                      properties=event)