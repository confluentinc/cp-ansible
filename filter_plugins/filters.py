#!/usr/bin/python
class FilterModule(object):
    def filters(self):
        return {
            'java_arg_build_out': self.java_arg_build_out
        }

    def java_arg_build_out(self, java_arg_list):
        java_args = ''
        for value in java_arg_list:
            if value != '':
                java_args = ' ' + value
        return java_args[1:]
