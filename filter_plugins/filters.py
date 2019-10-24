#!/usr/bin/python
class FilterModule(object):
    def filters(self):
        return {
            'normalize_sasl_protocol': self.normalize_sasl_protocol,
            'kafka_protocol_normalized': self.kafka_protocol_normalized,
            'kafka_protocol': self.kafka_protocol
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
