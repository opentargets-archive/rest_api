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
import ujson as json

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






class TokenAuthentication():

    app_name='cttv-rest-api'


    @staticmethod
    def get_auth_token(api_name='', expiration=600, salt='', payload ={}):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration,)
        cipher = AESCipher(current_app.config['SECRET_KEY'][:16])
        payload['api'] = api_name
        payload['app secret'] = salt
        token = s.dumps(cipher.encrypt(json.dumps(payload)))
        print repr(token)
        return token

    @staticmethod
    def is_valid(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        print repr(token)
        cipher = AESCipher(current_app.config['SECRET_KEY'][:16])
        try:
            data = json.loads(cipher.decrypt(s.loads(token)))

            print data
            #TODO: do something with data and log usage
        except SignatureExpired:
            print 'expired'
            return False    # valid token, but expired
        except BadSignature, e:
            print 'bad signature'
            encoded_payload = e.payload
            if encoded_payload is not None:
                try:
                    decoded_payload = s.load_payload(encoded_payload)
                    print json.loads(cipher.decrypt(decoded_payload))
                except BadData:
                    print 'bad data'
            raise
            return False    # invalid token
        return True


def is_authenticated(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(func, 'authenticated', True):
            return func(*args, **kwargs)

        resp = make_response(func(*args, **kwargs))
        h = resp.headers
        authorized =False
        print h
        if 'X-Auth-Token' in h:
            authorized = TokenAuthentication.is_valid(h['X-Auth-Token'])
        else:
            try:
                 call_args = args[0].parser.parse_args()
                 print call_args
                 if 'auth_token' in call_args:
                     authorized = TokenAuthentication.is_valid(call_args['auth_token'])
            except:pass
        if authorized:
            return func(*args, **kwargs)

        restful.abort(401)
    return wrapper