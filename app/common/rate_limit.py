import time

import datetime
from flask.ext import restful
from flask.ext.restful import abort, wraps
from flask import current_app, request

from app.common.auth import TokenAuthentication, get_token_payload, AuthKey
from config import Config

'''
Rate limit is computed every 10 seconds
the value stored is the amount of ms spent in the elasticsearch backend.
each request also count for a minimum default ms (10?), so if the request does not hit es
an higher throughput is allowed
'''





class RateLimiter(object):

    _RATE_LIMIT_NAMESPACE= 'REST_API_RATE_LIMIT_v' + Config.API_VERSION
    SHORT_WINDOW_SIZE = 10 #10 seconds
    LONG_WINDOW_SIZE = 60*60 #1 hour
    DEFAULT_CALL_WEIGHT = 10

    def __init__(self,
                 r_server= None):

        self.get_auth_token_payload()
        self.set_limits()
        self.set_unique_requester_id()
        self.set_short_window_key()
        self.set_long_window_key()

    def set_limits(self):
        auth_key = AuthKey()
        if self.auth_token_payload:
            auth_key.load(secret=self.auth_token_payload['secret'],
                          appname=self.auth_token_payload['appname'])
        self.short_window_rate = auth_key.short_window_rate
        self.long_window_rate = auth_key.long_window_rate



    def set_short_window_key(self):
        self.short_window_key =  '|'.join((self._RATE_LIMIT_NAMESPACE,
                                           str(request.environ.get('REMOTE_ADDR')),
                                           self.unique_id,
                                           time.strftime("%H%M%S")[:-1],
                                           #r.environ.get('HTTP_USER_AGENT')
                                           ))


    def set_long_window_key(self):
        self.long_window_key ='|'.join((self._RATE_LIMIT_NAMESPACE,
                                        str(request.environ.get('REMOTE_ADDR')),
                                        self.unique_id,
                                        time.strftime("%d%H"),
                                        #r.environ.get('HTTP_USER_AGENT')
                                        ))

    def set_unique_requester_id(self):
        self.unique_id = ''

    def get_auth_token_payload(self):
        self.auth_token_payload = get_token_payload()




def increment_call_rate(value=RateLimiter.DEFAULT_CALL_WEIGHT, rate_limiter = None):
    if rate_limiter is None:
        rate_limiter = RateLimiter()
    r_server = current_app.extensions['redis-service']
    pipe = r_server.pipeline()
    # current_app.logger.debug/('ratelimit increase for key %s value: %i'%(rate_limiter.short_window_key, value))
    pipe.incr(rate_limiter.short_window_key, value)
    pipe.expire(rate_limiter.short_window_key, RateLimiter.SHORT_WINDOW_SIZE)
    pipe.incr(rate_limiter.long_window_key, value)
    pipe.expire(rate_limiter.long_window_key, RateLimiter.LONG_WINDOW_SIZE)
    result=pipe.execute()
    current_values = dict(short=result[0],
                         long=result[2])
    # current_app.logger.debug('current values: %(short)i, %(long)i '%current_values)
    return current_values

def ceil_dt_to_future_time(dt, ceil = 10):
    nsecs = dt.minute*60 + dt.second + dt.microsecond*1e-6
    delta = (nsecs//ceil)*ceil + ceil - nsecs
    return delta

def rate_limit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        rate_limiter = RateLimiter()
        current_values = increment_call_rate(rate_limiter=rate_limiter)
        if (current_values['short'] <= rate_limiter.short_window_rate and \
            current_values['long'] <= rate_limiter.long_window_rate) or \
                 current_app.config['DEBUG']:
            # current_app.logger.debug('Rate Limit PASSED')
            return func(*args, **kwargs)
        current_app.logger.info('Rate Limit NOT PASSED')
        restful.abort(429)
    return wrapper