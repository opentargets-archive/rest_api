from datetime import datetime
import time

__author__ = 'andreap'

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from itsdangerous import SignatureExpired, BadSignature
from flask import current_app, request, make_response
from flask.ext import restful
from flask.ext.restful import abort, wraps
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
import json
from config import Config

class AuthKey(object):
    _AUTH_KEY_NAMESPACE='REST_API_AUTH_KEY_v'+Config.API_VERSION

    def __init__(self,
                 appname='',
                 secret='',
                 domain='',
                 short_window_rate=100,
                 long_window_rate=60000,
                 users_allowed="False",
                 reference=''):
        self.appname=appname
        self.secret=secret
        self.domain=domain.split('|')
        self.short_window_rate=int(short_window_rate)
        self.long_window_rate=int(long_window_rate)
        self.users_allowed=users_allowed.lower()=='true'
        self.reference=reference
        self.id = '-'.join((secret,appname))

    def get_key(self, ):
        return '|'.join((self._AUTH_KEY_NAMESPACE,self.id))

    def load(self,secret, appname):
        data = current_app.extensions['redis-user'].hmset(self.get_key())
        if data:
            self.__dict__.update(data)




class AESCipher:
    def __init__(self, key):
        self.bs = 16
        self.key = hashlib.sha256(key.encode()).digest()
    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))
    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')
    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]




def get_domain():
    return request.environ.get('HTTP_HOST').split(':')[0]

class TokenAuthentication():

    app_name='cttv-rest-api'
    EXPIRED = 'expired'

    @staticmethod
    def _autenticate(auth_data):
        #TODO: use a proper authentication
        authorized_keys = current_app.config['AUTORISED_KEYS']

        domain = get_domain()
        if auth_data['secret'] in authorized_keys:
            if authorized_keys[auth_data['secret']].domain:
                for allowed_domain in authorized_keys[auth_data['secret']].domain:
                    if domain.endswith(allowed_domain):
                        return True
            else:
                return True
        return False


    @staticmethod
    def _prepare_payload(api_name, auth_data):
        payload = {'api_name': api_name,
                   'app_name': auth_data['appname'],
                   'secret': auth_data['secret'],
                   'domain': get_domain()}
        if 'uid' in auth_data:
            payload['uid'] = auth_data['uid']
        return payload

    @staticmethod
    def get_payload_from_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        cipher = AESCipher(current_app.config['SECRET_KEY'][:16])
        try:
            data = json.loads(cipher.decrypt(s.loads(token)))
            return data
        except SignatureExpired, se:
            time_offset = (datetime.now()- se.date_signed).total_seconds()
            current_app.logger.error('token expired: %s. signature date %s. offset with current date = %s'%(se.message,str(se.date_signed),str(time_offset)))
            if -1<= time_offset < 0:#allow for 5 seconds out of sync machines
                current_app.logger.info('token time offset within grace period. allowing auth')
                return json.loads(cipher.decrypt(se.payload))
            else:
                raise SignatureExpired(se)
        except BadSignature, e:
            current_app.logger.error('bad signature in token')
            # encoded_payload = e.payload
            # if encoded_payload is not None:
            #     try:
            #         decoded_payload = s.load_payload(encoded_payload)
            #         print json.loads(cipher.decrypt(decoded_payload))
            #     except BadData:
            #         print 'bad data in token'




    @classmethod
    def get_auth_token(cls, api_name='', expiry=600, salt='', auth_data ={}):
        """

        :rtype : str token
        """
        if cls._autenticate(auth_data):
            payload = cls._prepare_payload(api_name,auth_data)
            s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiry, )
            cipher = AESCipher(current_app.config['SECRET_KEY'][:16])
            token = s.dumps(cipher.encrypt(json.dumps(payload)))
            current_app.logger.info('token served', extra=dict(token=token))
            return dict(token=token)
        abort(401)

    @classmethod
    def is_valid(cls,token):
        payload = cls.get_payload_from_token(token)
        if payload:
            if payload['domain'] != get_domain():
                current_app.logger.error("bad domain in token: got %s expecting %s"%(payload['domain'],get_domain()))
                return False
            return True
        return False


def is_authenticated(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(func, 'authenticated', True):
            return func(*args, **kwargs)
        # authorized =False # set to false to authorise only requests with token
        authorized =True
        token = request.headers.get('Auth-Token')
        if token:
            authorized = TokenAuthentication.is_valid(token)
        if authorized:
            return func(*args, **kwargs)

        restful.abort(401)
    return wrapper

def get_token_payload():
    token = request.headers.get('Auth-Token')
    if not token:
        token= request.headers.get('Authorization')
        if token:
            token = token.split()[-1].strip()
            token = base64.b64decode(token)[:-1]
    if token:
        return TokenAuthentication.get_payload_from_token(token)
