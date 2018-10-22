import copy
import json
from flask_restful import abort
from flask import request, Response
import requests
import logging
from auth import TokenAuthentication

__author__ = 'andreap'

CHUNK_SIZE = 1024
ALLOWED_HEADERS = ['Content-Type']
class ProxyHandler():

    def __init__(self,
                 allowed_targets = {},
                 allowed_domains = [],
                 allowed_request_domains = []):
        self.allowed_targets = allowed_targets
        self.allowed_domains = allowed_domains
        self.allowed_request_domains = allowed_request_domains

    def proxy(self,
              domain,
              url,
              token_payload = None,
              post_payload =None,
              preserve_headers = True,
              ):
        """Fetches the specified URL and streams it out to the client.

        If the request was referred by the proxy itself (e.g. this is an image fetch for
        a previously proxied HTML page), then the original Referer is passed."""

        r = self.get_source_rsp(domain, url, post_payload)
        logging.info("Got %s response from %s",r.status_code, url)
        headers = dict(r.headers)
        def generate():
            for chunk in r.iter_content(CHUNK_SIZE):
                yield chunk
        if preserve_headers:
            return Response(generate(), headers = headers,)
        return Response(generate())


    def get_source_rsp(self,
                       domain,
                       partial_url,
                       post_payload):
        url = self.get_full_url(domain,partial_url)
        logging.info("Fetching %s", url)
        # Pass original Referer for subsequent resource requests
        headers= {"Referer" : url}
        for h in ALLOWED_HEADERS:
            if h in request.headers and request.headers[h]:
                headers[h]=request.headers.get(h)
        # Fetch the URL, and stream it back
        logging.info("Fetching with headers: %s, %s", url, headers)
        if post_payload is not None:
            return requests.post(url,
                                stream=True ,
                                data = post_payload,
                                headers=headers)
        else:
            return requests.get(url,
                                stream=True ,
                                # params = request.args,
                                headers=headers)

    def get_full_url(self, domain, url):
        request_domain = request.environ.get('HTTP_HOST').split(':')[0]
        if request_domain not in self.allowed_request_domains:
            logging.warn("request domain is not allowed: %s%s"%(request_domain))
            abort(403)
        if domain in self.allowed_targets:
            return self.allowed_targets[domain]+url
        elif self.is_url_allowed(url):
            return url
        else:
            logging.warn("domain is not allowed: %s%s"%(domain,url))
            abort(403)

    def is_url_allowed(self, url):
        allowed = False
        try:
            domain = url.split('//')[1].split('/')[0]
            if domain in self.allowed_domains:
                allowed = True
        except:
            pass
        return allowed

