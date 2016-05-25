import time

from flask.ext.restful import abort, wraps
from flask import current_app, request

from app.common.auth import get_token_payload, AuthKey
from app.common.datadog_signals import RateLimitExceeded, LogApiCallCount
from config import Config

'''
Rate limit is computed every 10 seconds
the value stored is the amount of ms spent in the elasticsearch backend.
each request also count for a minimum default ms (10), so if the request does not hit es
an higher throughput is allowed
'''





class RateLimiter(object):

    _RATE_LIMIT_NAMESPACE= 'REST_API_RATE_LIMIT_v' + Config.API_VERSION_MINOR
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
        self._auth_key = AuthKey()
        if self.auth_token_payload:
            self._auth_key = AuthKey(app_name=self.auth_token_payload['app_name'],
                                     secret=self.auth_token_payload['secret'],
                                     )
            self._auth_key.get_loaded_data()
        self.short_window_rate = int(self._auth_key.short_window_rate)
        self.long_window_rate = int(self._auth_key.long_window_rate)



    def set_short_window_key(self):
        self.short_window_key =  '|'.join((self._RATE_LIMIT_NAMESPACE,
                                           self._get_remote_addr(),
                                           self.unique_id,
                                           time.strftime("%H%M%S")[:-1],
                                           #r.environ.get('HTTP_USER_AGENT')
                                           ))


    def set_long_window_key(self):
        self.long_window_key ='|'.join((self._RATE_LIMIT_NAMESPACE,
                                        self._get_remote_addr(),
                                        self.unique_id,
                                        time.strftime("%d%H"),
                                        #r.environ.get('HTTP_USER_AGENT')
                                        ))

    def set_unique_requester_id(self):
        self.unique_id = self._auth_key.id

    def get_auth_token_payload(self):
        self.auth_token_payload = get_token_payload()
        if not self.auth_token_payload:
            if 'app_name' in request.form and \
                'secret' in request.form:
                self.auth_token_payload = dict(app_name=request.form['app_name'],
                                               secret=request.form['secret'])
    def _get_remote_addr(self):
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            remote_addr = real_ip
        elif not request.headers.getlist("X-Forwarded-For"):
            if request.remote_addr is None:
                remote_addr = '127.0.0.1'
            else:
                remote_addr = request.remote_addr
        else:
            #securely log all the forwarded ips.
            #can be improved if a fixed number of proxied is known http://esd.io/blog/flask-apps-heroku-real-ip-spoofing.html
            #TODO: change to a known number of proxy if env is production
            remote_addr = ','.join(request.headers.getlist("X-Forwarded-For"))
        return str(remote_addr)



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
        LogApiCallCount(rate_limiter)
        current_values = increment_call_rate(rate_limiter=rate_limiter)
        if (current_values['short'] <= rate_limiter.short_window_rate and \
            current_values['long'] <= rate_limiter.long_window_rate):
            return func(*args, **kwargs)
        # elif current_app.config['DEBUG']:
        #     current_app.logger.debug('Rate Limit Exceeded, skipped in debug mode')
        #     return func(*args, **kwargs)
        current_app.logger.info('Rate Limit Exceeded')
        RateLimitExceeded(rate_limiter)
        abort(429, description = 'Too many requests. Please look at the "X-Usage-Limit-Wait" header for the time to wait for an other call')
    return wrapper