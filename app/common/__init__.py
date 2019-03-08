from __future__ import print_function
import sys
import io
import json
import csv
from contextlib import contextmanager
import tempfile as tmp
import requests as r
from config import Config
import flask_restful as restful

__author__ = 'andreap'


@contextmanager
def url_to_tmpfile(url, delete=True, *args, **kwargs):
    '''request a url using requests pkg and pass *args and **kwargs to
    requests.get function (useful for proxies) and returns the filled file
    descriptor from a tempfile.NamedTemporaryFile
    '''
    f = None

    if url.startswith('ftp://'):
        raise NotImplementedError('finish ftp')

    elif url.startswith('file://') or ('://' not in url):
        filename = url[len('file://'):] if '://' in url else url
        with open(filename, mode="r+b") as f:
            yield f

    else:
        f = r.get(url, *args, stream=True, **kwargs)
        f.raise_for_status()

        with tmp.NamedTemporaryFile(mode='r+w+b', delete=delete) as fd:
            # write data into file in streaming fashion
            for block in f.iter_content(1024):
                fd.write(block)

            fd.seek(0)
            yield fd

        f.close()


def load_tissue_map():
    def __generate_tissue_map(url):
        t2m = {'tissues': {} ,
               'codes': {}}

        with url_to_tmpfile(url) as r_file:
            t2m['tissues'] = json.load(r_file)['tissues']

        for _, v in t2m['tissues'].iteritems():
            code = v['efo_code']
            t2m['codes'][code] = v

        return t2m

    tmap = None
    try:
        tmap = __generate_tissue_map(Config.ES_TISSUE_MAP_URL.format(Config.DATA_VERSION))
        print('generate tissue map from DATA_VERSION tag on',
              Config.ES_TISSUE_MAP_URL.format(Config.DATA_VERSION))
    except:
        tmap = __generate_tissue_map(Config.ES_TISSUE_MAP_URL.format('master'))
        print('failed to generate tissue map for Config.DATA_VERSION',
              Config.DATA_VERSION,
              'so getting it from master',
              Config.ES_TISSUE_MAP_URL.format('master'),
              file=sys.stderr)
    finally:
        return tmap
