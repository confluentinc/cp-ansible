#!/usr/bin/python

def to_ini(input):
    result = ""
    input_sorted = sorted(input.items())

    for section, section_values in input_sorted:
        result += "[{}]\n".format(section)
        for key, value in sorted(section_values.items()):
            if isinstance(value, dict):
                for k,v in sorted(value.items()):
                    result+="{}=\"{}={}\"\n".format(key, k, v)
            else:
                result += "{}={}\n".format(key, value)

    return result


def to_properties(input):
    input_sorted = sorted(input.items())
    result = ""
    for key, value in input_sorted:
        result+="{}={}\n".format(key, value)
    return result


def prefix_map(input, prefix):
    result = {}
    for key, value in input:
        result[prefix + key] = value
    return result


def producer(input):
    return prefix_map(input, 'producer.')


def consumer(input):
    return prefix_map(input, 'consumer.')


class FilterModule(object):
    def filters(self):
        return {
            'to_properties': to_properties,
            'to_ini': to_ini,
            'prefix_map': prefix_map,
            'producer': producer,
            'consumer': consumer,
        }

