#!/usr/bin/python

def format_host(hosts, format, values={}, hostvars=None, lookupvars={}):
    result = []
    for host in sorted(hosts):
        d = values.copy()
        d['host'] = host
        if not hostvars is None:
            for key, default_value in lookupvars.items():
                value = hostvars[host].get(key, default_value)
                d[key] = value
        s = format.format(**d)
        result.append(s)

    return result

def first(hosts):
    return [hosts[0]]

def get_host(input):
    result = "{}".format(input)
    return result

class FilterModule(object):
    def filters(self):
        return {
            'get_host': get_host,
            'format_host': format_host,
            'first': first,
        }

