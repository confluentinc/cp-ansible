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


def non_zero(input):
    return len(input) > 0


class FilterModule(object):
    def filters(self):
        return {
            'format_host': format_host,
            'first': first,
            'non_zero': non_zero,
        }

