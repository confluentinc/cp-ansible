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
            elif isinstance(value, bool):
                result += "{}={}\n".format(key, str(value).lower())
            else:
                result += "{}={}\n".format(key, value)

    return result


def to_properties(input):
    input_sorted = sorted(input.items())
    result = ""
    for key, value in input_sorted:
        if isinstance(value, bool):
            result += "{}={}\n".format(key, str(value).lower())
        else:
            result+="{}={}\n".format(key, value)
    return result


def append_prefix(input, prefix):
    result = input.copy()
    if isinstance(prefix, list):
        for p in prefix:
            for key, value in input.items():
                result[p + key] = value
    else:
        for key, value in input.items():
            result[prefix + key] = value
    return result


class FilterModule(object):
    def filters(self):
        return {
            'to_properties': to_properties,
            'to_ini': to_ini,
            'append_prefix': append_prefix
        }

