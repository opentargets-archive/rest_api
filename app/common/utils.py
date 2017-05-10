from flask import request

__author__ = 'andreap'


def get_ordered_filter_list(params):
    """
    the list of get parameters in a list of key:value tuples if they start fwith filterby

    :return: ordered list of (key,value) tuples
    """
    filters = []
    if params:
        for param in params.split('&'):
            if param.startswith('filterby'):
                key, value = param.split('=')
                try:
                    value = float(value)
                except:
                    pass
                filters.append((key,value))
    return filters



def get_remote_addr():
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


def fix_empty_strings(l):
    new_l = []
    if l:
        for i in l:
            if i:
                new_l.append(i)
    return new_l
