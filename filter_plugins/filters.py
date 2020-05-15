class FilterModule(object):
    def filters(self):
        return {
            'normalize_sasl_protocol': self.normalize_sasl_protocol,
            'kafka_protocol_normalized': self.kafka_protocol_normalized,
            'kafka_protocol': self.kafka_protocol,
            'kafka_protocol_defaults': self.kafka_protocol_defaults,
            'get_sasl_mechanisms': self.get_sasl_mechanisms,
            'get_hostnames': self.get_hostnames,
            'cert_extension': self.cert_extension,
            'ssl_required': self.ssl_required,
            'java_arg_build_out': self.java_arg_build_out,
            'combine_properties': self.combine_properties,
            'split_to_dict': self.split_to_dict,
            'listener_properties': self.listener_properties,
            'client_properties': self.client_properties
        }

    def normalize_sasl_protocol(self, protocol):
        normalized = 'GSSAPI' if protocol.lower() == 'kerberos' \
            else 'SCRAM-SHA-256' if protocol.upper() == 'SCRAM' \
            else 'PLAIN' if protocol.upper() == 'PLAIN' \
            else 'OAUTHBEARER' if protocol.upper() == 'OAUTH' \
            else 'none'
        return normalized

    def kafka_protocol_normalized(self, sasl_protocol_normalized, ssl_enabled):
        kafka_protocol = 'SASL_SSL' if ssl_enabled == True and sasl_protocol_normalized in ['GSSAPI', 'PLAIN', 'SCRAM-SHA-256', 'OAUTHBEARER'] \
            else 'SASL_PLAINTEXT' if ssl_enabled == False and sasl_protocol_normalized in ['GSSAPI', 'PLAIN', 'SCRAM-SHA-256', 'OAUTHBEARER'] \
            else 'SSL' if ssl_enabled == True and sasl_protocol_normalized == 'none' \
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

    def get_hostnames(self, listeners_dict, default_hostname):
        hostnames = []
        for listener in listeners_dict:
            hostname = listeners_dict[listener].get('hostname', default_hostname)
            hostnames = hostnames + [hostname]
        return hostnames

    def cert_extension(self, hostnames):
        extension = 'dns:'+",dns:".join(hostnames)
        return extension

    def ssl_required(self, listeners_dict, default_ssl_enabled):
        ssl_required = False
        for listener in listeners_dict:
            ssl_enabled = listeners_dict[listener].get('ssl_enabled', default_ssl_enabled)
            ssl_required = ssl_required == True or ssl_enabled == True
        return ssl_required

    def java_arg_build_out(self, java_arg_list):
        java_args = ''
        for value in java_arg_list:
            if value != '':
                java_args = java_args + ' ' + value
        return java_args[1:]

    def combine_properties(self, properties_dict):
        final_dict = {}
        for prop in properties_dict:
            if properties_dict[prop].get('enabled'):
                final_dict.update(properties_dict[prop].get('properties'))
        return final_dict

    def split_to_dict(self, string):
        # Splits a string like key=val,key=val into dict
        return dict(x.split('=') for x in string.split(','))

    def listener_properties(self, listeners_dict, default_ssl_enabled, default_pkcs12_enabled, default_ssl_mutual_auth_enabled, default_sasl_protocol,
                            kafka_broker_truststore_path, kafka_broker_truststore_storepass, kafka_broker_keystore_path, kafka_broker_keystore_storepass, kafka_broker_keystore_keypass,
                            plain_jaas_config, keytab_dir, keytab_filename, kerberos_principal,
                            scram_user, scram_password, oauth_pem_path ):

        final_dict = {}
        for listener in listeners_dict:
            if listeners_dict[listener].get('enabled', default_ssl_enabled):
                final_dict.update({
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.truststore.location': kafka_broker_truststore_path,
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.truststore.password': kafka_broker_truststore_storepass,
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.keystore.location': kafka_broker_keystore_path,
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.keystore.password': kafka_broker_keystore_storepass,
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.key.password': kafka_broker_keystore_keypass
                })
            if listeners_dict[listener].get('pkcs12_enabled', default_pkcs12_enabled):
                final_dict.update({
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.keymanager.algorithm': 'PKIX',
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.trustmanager.algorithm': 'PKIX',
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.keystore.type': 'pkcs12',
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.truststore.type': 'pkcs12',
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.enabled.protocols': 'TLSv1.2'
                })
            if listeners_dict[listener].get('ssl_mutual_auth_enabled', default_ssl_mutual_auth_enabled):
                final_dict.update({
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.client.auth': 'required'
                })
            if self.normalize_sasl_protocol(listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)) == 'PLAIN':
                final_dict.update({
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.sasl.enabled.mechanisms': 'PLAIN',
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.plain.sasl.jaas.config': plain_jaas_config
                })
            if self.normalize_sasl_protocol(listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)) == 'GSSAPI':
                final_dict.update({
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.sasl.enabled.mechanisms': 'GSSAPI',
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.gssapi.sasl.jaas.config': 'com.sun.security.auth.module.Krb5LoginModule required useKeyTab=true storeKey=true keyTab=\"' + keytab_dir + '/' + keytab_filename+ '\"principal=\"' + kerberos_principal + '\";'
                })
            if self.normalize_sasl_protocol(listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)) == 'SCRAM-SHA-256':
                final_dict.update({
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.sasl.enabled.mechanisms': 'SCRAM-SHA-256',
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.scram-sha-256.sasl.jaas.config': 'org.apache.kafka.common.security.scram.ScramLoginModule required username=\"' + scram_user + '\"password=\"' + scram_password + '\";'
                })
            if self.normalize_sasl_protocol(listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)) == 'OAUTHBEARER':
                final_dict.update({
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.sasl.enabled.mechanisms': 'OAUTHBEARER',
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.oauthbearer.sasl.server.callback.handler.class': 'io.confluent.kafka.server.plugins.auth.token.TokenBearerValidatorCallbackHandler',
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.oauthbearer.sasl.login.callback.handler.class': 'io.confluent.kafka.server.plugins.auth.token.TokenBearerServerLoginCallbackHandler',
                    'listener.name.' + listeners_dict[listener].get('name').lower() + '.oauthbearer.sasl.jaas.config': 'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required publicKeyPath=\"' + oauth_pem_path + '\";'
                })
        return final_dict

    def client_properties(self, listener_dict, prefix):
        final_dict = {}
        final_dict.update({prefix: 'that' })
        # if listeners_dict[listener].get('enabled', default_ssl_enabled):
        #     final_dict.update({
        #         'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl.truststore.location': kafka_broker_truststore_path,
        #         'listener.name.' + listeners_dict[listener].get('name').lower() + '.ssl
        return final_dict
