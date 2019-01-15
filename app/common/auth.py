from flask import current_app, request
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
import json

from config import Config
__author__ = 'andreap'

class AuthKey(object):
    _AUTH_KEY_NAMESPACE='REST_API_AUTH_KEY_v'+Config.API_VERSION_MINOR

    def __init__(self,
                 app_name='',
                 secret='',
                 domain='',
                 users_allowed="False",
                 reference='',
                 **kwargs):
        self.app_name=app_name
        self.secret=secret
        self.domain=domain
        self.users_allowed=users_allowed.lower()=='true'
        self.reference=reference
        self.id = '-'.join((secret, app_name))

    def get_key(self, ):
        return '|'.join((self._AUTH_KEY_NAMESPACE,self.id))

    def get_loaded_data(self):
        data = current_app.extensions['redis-user'].get(self.get_key())
        if data:
            self.__dict__.update(json.loads(data))


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

