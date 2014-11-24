import requests
import random, string
from datetime import datetime, timedelta
import time
import random


__author__ = 'andreap'

base_path = 'http://127.0.0.1:8008/api/public/v0.1' # direct
# base_path = 'http://127.0.0.1:8080/api/public/v0.1' # behind ngix

def test_random_search():
    path = base_path+'/search'
    start_time = datetime.now()
    ok = errors= 0
    while 1:
        random_string = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
        r = requests.get(path , params = dict(q=random_string))
        if r.status_code ==200:
            ok +=1
        else:
            errors+=1
        delta = (datetime.now() - start_time).total_seconds()
        if  delta >= 1:
            print ok, errors
            start_time = datetime.now()
            ok = errors= 0


def test_available_genes():
    path = base_path+'/available-genes'
    start_time = datetime.now()
    ok = errors= 0.
    while 1:
        r = requests.get(path)
        if r.status_code ==200:
            ok +=1
        else:
            errors+=1
        delta = (datetime.now() - start_time).total_seconds()
        if  delta >= 1:
            print ok/delta, errors/delta
            start_time = datetime.now()
            ok = errors= 0.

def test_echo():
    path = base_path+'/echo'
    start_time = datetime.now()
    ok = errors= 0.
    while 1:
        r = requests.get(path, params = dict(echo="Hi"))
        if r.status_code ==200:
            ok +=1
        else:
            errors+=1
        delta = (datetime.now() - start_time).total_seconds()
        if  delta >= 1:
            print ok/delta, errors/delta
            start_time = datetime.now()
            ok = errors= 0.

def test_echo_random_slowdown():
    path = base_path+'/echo'
    start_time = datetime.now()
    ok = errors= 0.
    while 1:
        r = requests.get(path, params = dict(echo="Hi", random = True))
        if r.status_code ==200:
            ok +=1
        else:
            errors+=1
        delta = (datetime.now() - start_time).total_seconds()
        if  delta >= 1:
            print ok/delta, errors/delta
            start_time = datetime.now()
            ok = errors= 0.

if __name__ == '__main__':
    test_available_genes()
    # test_random_search()
    # test_echo()
    # test_echo_random_slowdown()