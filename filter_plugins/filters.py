class FilterModule(object):
    def filters(self):
        return {
            'normalize_sasl_protocol': self.normalize_sasl_protocol,
            'kafka_protocol_normalized': self.kafka_protocol_normalized,
            'kafka_protocol': self.kafka_protocol,
            'kafka_protocol_defaults': self.kafka_protocol_defaults,
            'get_sasl_mechanisms': self.get_sasl_mechanisms,
            'ssl_required': self.ssl_required,
            'java_arg_build_out': self.java_arg_build_out
        }

    def normalize_sasl_protocol(self, protocol):
        normalized = 'GSSAPI' if protocol.lower() == 'kerberos' \
            else 'SCRAM-SHA-256' if protocol.upper() == 'SCRAM' \
            else 'PLAIN' if protocol.upper() == 'PLAIN' \
            else 'none'
        return normalized

    def kafka_protocol_normalized(self, sasl_protocol_normalized, ssl_enabled):
        kafka_protocol = 'SASL_SSL' if ssl_enabled and sasl_protocol_normalized in ['GSSAPI', 'PLAIN', 'SCRAM-SHA-256'] \
            else 'SASL_PLAINTEXT' if not ssl_enabled and sasl_protocol_normalized in ['GSSAPI', 'PLAIN', 'SCRAM-SHA-256'] \
            else 'SSL' if ssl_enabled and sasl_protocol_normalized == 'none' \
            else 'PLAINTEXT'
        return kafka_protocol

    def kafka_protocol(self, sasl_protocol, ssl_enabled):
        sasl_protocol_normalized = self.normalize_sasl_protocol(sasl_protocol)
        kafka_protocol = self.kafka_protocol_normalized(sasl_protocol_normalized, ssl_enabled)
        return kafka_protocol

    def kafka_protocol_defaults(self, listener, default_ssl_enabled, default_sasl_protocol):
        ssl_enabled = listener.get('ssl_enabled', default_ssl_enabled)
        sasl_protocol = listener.get('sasl_protocol', default_sasl_protocol)
        sasl_protocol_normalized = self.normalize_sasl_protocol(sasl_protocol)
        kafka_protocol = self.kafka_protocol_normalized(sasl_protocol_normalized, ssl_enabled)
        return kafka_protocol

    def get_sasl_mechanisms(self, listeners_dict, default_sasl_protocol):
        mechanisms = []
        for listener in listeners_dict:
            sasl_protocol = listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)
            mechanisms = mechanisms + [self.normalize_sasl_protocol(sasl_protocol)]
        return mechanisms

    def ssl_required(self, listeners_dict, default_ssl_enabled):
        ssl_required = False
        for listener in listeners_dict:
            ssl_enabled = listeners_dict[listener].get('ssl_enabled', default_ssl_enabled)
            ssl_required = ssl_required or ssl_enabled
        return ssl_required

    def java_arg_build_out(self, java_arg_list):
        java_args = ''
        for value in java_arg_list:
            if value != '':
                java_args = java_args + ' ' + value
        return java_args[1:]
