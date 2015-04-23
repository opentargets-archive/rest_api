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
    def _autenticate(auth_data):
        #TODO: use a proper authentication
        authorized_keys = {
            '2J23T20O31UyepRj7754pEA2osMOYfFK' :['targetvalidation.org', 'beta.targetvalidation.org','localhost', '127.0.0.1']
        }

        domain = request.environ.get('HTTP_HOST').split(':')[0]
        if auth_data['secret'] in authorized_keys:
            if authorized_keys[auth_data['secret']]:
                if domain in authorized_keys[auth_data['secret']]:
                    return True
            else:
                return True
        return False


    @staticmethod
    def _prepare_payload(api_name, auth_data):
        payload = {'api_name': api_name,
                   'app_name': auth_data['appname']}
        if 'uid' in auth_data:
            payload['uid'] = auth_data['uid']
        return payload

    @staticmethod
    def _get_payload_from_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        cipher = AESCipher(current_app.config['SECRET_KEY'][:16])
        try:
            data = json.loads(cipher.decrypt(s.loads(token)))

            return data
        except SignatureExpired:
            current_app.logger.error('token expired')
            return False    # valid token, but expired
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
    def get_auth_token(cls, api_name='', expiration=600, salt='', auth_data ={}):
        """

        :rtype : str token
        """
        if cls._autenticate(auth_data):
            payload = cls._prepare_payload(api_name,auth_data)
            s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration,)
            cipher = AESCipher(current_app.config['SECRET_KEY'][:16])
            token = s.dumps(cipher.encrypt(json.dumps(payload)))
            current_app.logger.info('token served', extra=dict(token=token))
            return dict(token=token)
        abort(401)

    @classmethod#TODO: this is temporary just for testing
    def is_valid(cls,token):
        if cls._get_payload_from_token(token):
            return True
        return False


def is_authenticated(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(func, 'authenticated', True):
            return func(*args, **kwargs)
        authorized =False

        # if current_app.config['DEBUG']:
        #     authorized = True
        token = request.headers.get('Auth-Token')
        if not token:
            token= request.headers.get('Authorization')
            if token:
                token = token.split()[-1].strip()
                token = base64.b64decode(token)[:-1]
        if token:
            authorized = TokenAuthentication.is_valid(token)
        else:
            try:
                 call_args = args[0].parser.parse_args()
                 if 'auth_token' in call_args:
                     authorized = TokenAuthentication.is_valid(call_args['auth_token'])
            except:pass
        if authorized:
            return func(*args, **kwargs)

        restful.abort(401)
    return wrapper