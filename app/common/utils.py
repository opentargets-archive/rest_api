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

