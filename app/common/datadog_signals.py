# Configure the module according to your needs
from flask import request, current_app
from config import Config
from datadog import initialize, ThreadStats, api
import ujson as json




class BaseDatadogSignal(object):
    def __init__(self):
        self.stats = current_app.extensions['datadog']

class RateLimitExceeded(BaseDatadogSignal):
    def __init__(self,
                 rate_limiter):

        super(RateLimitExceeded, self).__init__()
        if self.stats:
            title = "Api limit exceeded"
            text = json.dumps(rate_limiter.__dict__)
            tags = ['version:'+str(Config.API_VERSION),
                    'application:rest-api',
                    'api-key:'+rate_limiter._auth_key.id]

            self.stats.event(title=title,
                             text=text,
                             tags=tags,
                             alert_type='error')
            self.stats.increment('api.auth.rate.limit.exceeded',
                            tags=tags,)



class LogApiCallWeight(BaseDatadogSignal):
    def __init__(self,
                 value):
        super(LogApiCallWeight, self).__init__()
        if self.stats:
            tags = ['version:'+str(Config.API_VERSION), 'application:rest-api']

            self.stats.increment('api.call.weight',
                            value=value,
                            tags=tags,)

class LogApiCallCount(BaseDatadogSignal):
    def __init__(self, rate_limiter):
        super(LogApiCallCount, self).__init__()
        if self.stats:
            tags = ['version:'+str(Config.API_VERSION),
                    'application:rest-api',
                    'api-key:'+rate_limiter._auth_key.id,
                    'method:'+request.environ['REQUEST_METHOD'],
                    'endpoint:'+request.url_rule.rule.split('<')[0].split(request.blueprint)[1]]

            self.stats.increment('api.call.count',
                            tags=tags,)



class LogApiTokenServed(BaseDatadogSignal):
    def __init__(self,):
        super(LogApiTokenServed, self).__init__()
        if self.stats:
            tags = ['version:'+str(Config.API_VERSION), 'application:rest-api']

            self.stats.increment('api.auth.token.served',
                            tags=tags,)

class LogApiTokenExpired(BaseDatadogSignal):
    def __init__(self,):
        super(LogApiTokenExpired, self).__init__()
        if self.stats:
            tags = ['version:'+str(Config.API_VERSION), 'application:rest-api']

            self.stats.increment('api.auth.token.expired',
                            tags=tags,)

class LogApiTokenInvalid(BaseDatadogSignal):
    def __init__(self,
                 message):
        super(LogApiTokenInvalid, self).__init__()
        if self.stats:

            message['host']= request.environ.get('HTTP_HOST').split(':')[0]

            title = "Invalid token used"
            text = json.dumps(message)
            tags = ['version:'+str(Config.API_VERSION), 'application:rest-api']

            self.stats.event(title=title,
                             text=text,
                             tags=tags,
                             alert_type='error')
            self.stats.increment('api.auth.token.invalid',
                            tags=tags,)

class LogApiTokenInvalidDomain(BaseDatadogSignal):
    def __init__(self,
                 message):
        super(LogApiTokenInvalidDomain, self).__init__()
        if self.stats:
            message['host']= request.environ.get('HTTP_HOST').split(':')[0]

            title = "Invalid token used"
            text = json.dumps(message)
            tags = ['version:'+str(Config.API_VERSION), 'application:rest-api']

            self.stats.event(title=title,
                             text=text,
                             tags=tags,
                             alert_type='error')
            self.stats.increment('api.auth.token.invalid.domain',
                            tags=tags,)