class FilterModule(object):
    def filters(self):
        return {
            'normalize_sasl_protocol': self.normalize_sasl_protocol,
            'kafka_protocol_normalized': self.kafka_protocol_normalized,
            'kafka_protocol': self.kafka_protocol,
            'kafka_protocol_defaults': self.kafka_protocol_defaults,
            'get_sasl_mechanisms': self.get_sasl_mechanisms,
            'get_hostnames': self.get_hostnames,
            'resolve_hostname': self.resolve_hostname,
            'resolve_hostnames': self.resolve_hostnames,
            'cert_extension': self.cert_extension,
            'ssl_required': self.ssl_required,
            'java_arg_build_out': self.java_arg_build_out,
            'combine_properties': self.combine_properties,
            'split_to_dict': self.split_to_dict,
            'split_newline_to_dict': self.split_newline_to_dict,
            'listener_properties': self.listener_properties,
            'client_properties': self.client_properties,
            'c3_connect_properties': self.c3_connect_properties,
            'c3_ksql_properties': self.c3_ksql_properties
        }

    def normalize_sasl_protocol(self, protocol):
        # Returns standardized value for sasl mechanism string
        normalized = 'GSSAPI' if protocol.lower() == 'kerberos' \
            else 'SCRAM-SHA-512' if protocol.upper() == 'SCRAM' \
            else 'SCRAM-SHA-256' if protocol.lower() == 'scram256' \
            else 'PLAIN' if protocol.upper() == 'PLAIN' \
            else 'OAUTHBEARER' if protocol.upper() == 'OAUTH' \
            else 'none'
        return normalized

    def kafka_protocol_normalized(self, sasl_protocol_normalized, ssl_enabled):
        # Joins a sasl mechanism and tls setting to return a kafka protocol
        kafka_protocol = 'SASL_SSL' if ssl_enabled == True and sasl_protocol_normalized in ['GSSAPI', 'PLAIN', 'SCRAM-SHA-512', 'SCRAM-SHA-256', 'OAUTHBEARER'] \
            else 'SASL_PLAINTEXT' if ssl_enabled == False and sasl_protocol_normalized in ['GSSAPI', 'PLAIN', 'SCRAM-SHA-512', 'SCRAM-SHA-256', 'OAUTHBEARER'] \
            else 'SSL' if ssl_enabled == True and sasl_protocol_normalized == 'none' \
            else 'PLAINTEXT'
        return kafka_protocol

    def kafka_protocol(self, sasl_protocol, ssl_enabled):
        # Joins a sasl mechanism and tls setting to return a kafka protocol
        sasl_protocol_normalized = self.normalize_sasl_protocol(sasl_protocol)
        kafka_protocol = self.kafka_protocol_normalized(sasl_protocol_normalized, ssl_enabled)
        return kafka_protocol

    def kafka_protocol_defaults(self, listener, default_ssl_enabled, default_sasl_protocol):
        # Joins a sasl mechanism and tls setting and their default values, to return a kafka protocol
        ssl_enabled = listener.get('ssl_enabled', default_ssl_enabled)
        sasl_protocol = listener.get('sasl_protocol', default_sasl_protocol)
        sasl_protocol_normalized = self.normalize_sasl_protocol(sasl_protocol)
        kafka_protocol = self.kafka_protocol_normalized(sasl_protocol_normalized, ssl_enabled)
        return kafka_protocol

    def get_sasl_mechanisms(self, listeners_dict, default_sasl_protocol):
        # Loops over listeners dictionary and returns list of sasl mechanisms
        mechanisms = []
        for listener in listeners_dict:
            sasl_protocol = listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)
            mechanisms = mechanisms + [self.normalize_sasl_protocol(sasl_protocol)]
        return mechanisms

    def get_hostnames(self, listeners_dict, default_hostname):
        # Loops over listeners dictionary and returns all hostnames attached to a listener
        hostnames = []
        for listener in listeners_dict:
            hostname = listeners_dict[listener].get('hostname', default_hostname)
            hostnames = hostnames + [hostname]
        return hostnames

    def resolve_hostname(self, hosts_hostvars_dict):
        # Goes through selected possible VARs to provide the HOSTNAME for a given node for internal addressing within Confluent Platform
        if hosts_hostvars_dict.get('hostname_aliasing_enabled') == True:
            return hosts_hostvars_dict.get('hostname', hosts_hostvars_dict.get('ansible_host', hosts_hostvars_dict.get('inventory_hostname')))
        else:
            return hosts_hostvars_dict.get('inventory_hostname')

    def resolve_hostnames(self, hosts, hostvars_dict):
        # Given a collection of hosts, usually from a group, will resolve the correct hostname to use for each.
        hostnames = []
        for host in hosts:
            if host == "localhost":
                hostnames.append("localhost")
            else:
                hostnames.append(self.resolve_hostname(hostvars_dict.get(host)))

        return hostnames

    def cert_extension(self, hostnames):
        # Joins a list of hostnames to be added to SAN of certificate
        extension = 'dns:'+",dns:".join(hostnames)
        return extension

    def ssl_required(self, listeners_dict, default_ssl_enabled):
        # Loops over listeners dictionary and returns True if any have TLS encryption enabled
        ssl_required = False
        for listener in listeners_dict:
            ssl_enabled = listeners_dict[listener].get('ssl_enabled', default_ssl_enabled)
            ssl_required = ssl_required == True or ssl_enabled == True
        return ssl_required

    def java_arg_build_out(self, java_arg_list):
        # Joins list of java args into string if arg is not the empty string
        java_args = ''
        for value in java_arg_list:
            if value != '':
                java_args = java_args + ' ' + value
        return java_args[1:]

    def combine_properties(self, properties_dict):
        # Loops over master properties dictionary and combines sub elements if enabled
        final_dict = {}
        for prop in properties_dict:
            if properties_dict[prop].get('enabled'):
                final_dict.update(properties_dict[prop].get('properties'))
        return final_dict

    def split_to_dict(self, string):
        # Splits a string like key=val,key=val into dict
        return dict(x.split('=') for x in string.split(','))

    def split_newline_to_dict(self, string):
        # Splits a string like key=val\nkey=val=with=equals\nkey=val into dict
        final_dict = {}
        for x in string.split('\n'):
            prop_list = x.split('=',1)
            if (len(prop_list)==2):
                final_dict[prop_list[0]] = prop_list[1]
        return final_dict

    def listener_properties(self, listeners_dict, default_ssl_enabled, bouncy_castle_keystore, default_ssl_mutual_auth_enabled, default_sasl_protocol,
                            kafka_broker_truststore_path, kafka_broker_truststore_storepass, kafka_broker_keystore_path, kafka_broker_keystore_storepass, kafka_broker_keystore_keypass,
                            plain_jaas_config, keytab_path, kerberos_principal, kerberos_primary,
                            scram_user, scram_password, scram256_user, scram256_password, oauth_pem_path ):
        # For kafka broker properties: Takes listeners dictionary and outputs all properties based on the listeners' settings
        # Other inputs help fill out the properties
        final_dict = {}
        for listener in listeners_dict:
            listener_name = listeners_dict[listener].get('name').lower()

            if listeners_dict[listener].get('ssl_enabled', default_ssl_enabled):
                final_dict['listener.name.' + listener_name + '.ssl.truststore.location'] = kafka_broker_truststore_path
                final_dict['listener.name.' + listener_name + '.ssl.truststore.password'] = kafka_broker_truststore_storepass
                final_dict['listener.name.' + listener_name + '.ssl.keystore.location'] = kafka_broker_keystore_path
                final_dict['listener.name.' + listener_name + '.ssl.keystore.password'] = kafka_broker_keystore_storepass
                final_dict['listener.name.' + listener_name + '.ssl.key.password'] = kafka_broker_keystore_keypass

            if bouncy_castle_keystore:
                final_dict['listener.name.' + listener_name + '.ssl.keymanager.algorithm'] = 'PKIX'
                final_dict['listener.name.' + listener_name + '.ssl.trustmanager.algorithm'] = 'PKIX'
                final_dict['listener.name.' + listener_name + '.ssl.keystore.type'] = 'BCFKS'
                final_dict['listener.name.' + listener_name + '.ssl.truststore.type'] = 'BCFKS'
                final_dict['listener.name.' + listener_name + '.ssl.enabled.protocols'] = 'TLSv1.2'

            if listeners_dict[listener].get('ssl_mutual_auth_enabled', default_ssl_mutual_auth_enabled):
                final_dict['listener.name.' + listener_name + '.ssl.client.auth'] = 'required'

            if self.normalize_sasl_protocol(listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)) == 'PLAIN':
                final_dict['listener.name.' + listener_name + '.sasl.enabled.mechanisms'] = 'PLAIN'
                final_dict['listener.name.' + listener_name + '.plain.sasl.jaas.config'] = plain_jaas_config

            if self.normalize_sasl_protocol(listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)) == 'GSSAPI':
                final_dict['listener.name.' + listener_name + '.sasl.enabled.mechanisms'] = 'GSSAPI'
                final_dict['listener.name.' + listener_name + '.sasl.kerberos.service.name'] = kerberos_primary
                final_dict['listener.name.' + listener_name + '.gssapi.sasl.jaas.config'] = 'com.sun.security.auth.module.Krb5LoginModule required useKeyTab=true storeKey=true keyTab=\"' + keytab_path + '\" principal=\"' + kerberos_principal + '\";'

            if self.normalize_sasl_protocol(listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)) == 'SCRAM-SHA-512':
                final_dict['listener.name.' + listener_name + '.sasl.enabled.mechanisms'] = 'SCRAM-SHA-512'
                final_dict['listener.name.' + listener_name + '.scram-sha-512.sasl.jaas.config'] = 'org.apache.kafka.common.security.scram.ScramLoginModule required username=\"' + scram_user + '\" password=\"' + scram_password + '\";'

            if self.normalize_sasl_protocol(listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)) == 'SCRAM-SHA-256':
                final_dict['listener.name.' + listener_name + '.sasl.enabled.mechanisms'] = 'SCRAM-SHA-256'
                final_dict['listener.name.' + listener_name + '.scram-sha-256.sasl.jaas.config'] = 'org.apache.kafka.common.security.scram.ScramLoginModule required username=\"' + scram256_user + '\" password=\"' + scram256_password + '\";'

            if self.normalize_sasl_protocol(listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)) == 'OAUTHBEARER':
                final_dict['listener.name.' + listener_name + '.sasl.enabled.mechanisms'] = 'OAUTHBEARER'
                final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.server.callback.handler.class'] = 'io.confluent.kafka.server.plugins.auth.token.TokenBearerValidatorCallbackHandler'
                final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.login.callback.handler.class'] = 'io.confluent.kafka.server.plugins.auth.token.TokenBearerServerLoginCallbackHandler'
                final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.jaas.config'] = 'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required publicKeyPath=\"' + oauth_pem_path + '\";'

        return final_dict

    def client_properties(self, listener_dict, default_ssl_enabled, bouncy_castle_keystore, default_ssl_mutual_auth_enabled, default_sasl_protocol,
                            config_prefix, truststore_path, truststore_storepass, public_certificates_enabled, keystore_path, keystore_storepass, keystore_keypass,
                            omit_jaas_configs, sasl_plain_username, sasl_plain_password, sasl_scram_username, sasl_scram_password, sasl_scram256_username, sasl_scram256_password,
                            kerberos_kafka_broker_primary, keytab_path, kerberos_principal,
                            omit_oauth_configs, oauth_username, oauth_password, mds_bootstrap_server_urls):
        # For any kafka client's properties: Takes in a single kafka listener and output properties to connect to that listener
        # Other inputs help fill out the properties
        final_dict = {
            config_prefix + 'security.protocol': self.kafka_protocol_defaults(listener_dict, default_ssl_enabled, default_sasl_protocol)
        }
        if listener_dict.get('ssl_enabled', default_ssl_enabled) and not public_certificates_enabled:
            # Public certificates are in default java truststore, so these properties should be ommitted
            final_dict[config_prefix + 'ssl.truststore.location'] = truststore_path
            final_dict[config_prefix + 'ssl.truststore.password'] = truststore_storepass

        if listener_dict.get('ssl_mutual_auth_enabled', default_ssl_mutual_auth_enabled):
            final_dict[config_prefix + 'ssl.keystore.location'] = keystore_path
            final_dict[config_prefix + 'ssl.keystore.password'] = keystore_storepass
            final_dict[config_prefix + 'ssl.key.password'] = keystore_keypass

        if listener_dict.get('ssl_mutual_auth_enabled', default_ssl_mutual_auth_enabled):
            final_dict[config_prefix + 'ssl.keystore.location'] = keystore_path
            final_dict[config_prefix + 'ssl.keystore.password'] = keystore_storepass
            final_dict[config_prefix + 'ssl.key.password'] = keystore_keypass

        if bouncy_castle_keystore:
            final_dict[config_prefix + 'ssl.keymanager.algorithm'] = 'PKIX'
            final_dict[config_prefix + 'ssl.trustmanager.algorithm'] = 'PKIX'
            final_dict[config_prefix + 'ssl.keystore.type'] = 'BCFKS'
            final_dict[config_prefix + 'ssl.truststore.type'] = 'BCFKS'

        if self.normalize_sasl_protocol(listener_dict.get('sasl_protocol', default_sasl_protocol)) == 'PLAIN' and not omit_jaas_configs:
            final_dict[config_prefix + 'sasl.mechanism'] = 'PLAIN'
            final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.plain.PlainLoginModule required username=\"' + sasl_plain_username + '\" password=\"' + sasl_plain_password + '\";'

        if self.normalize_sasl_protocol(listener_dict.get('sasl_protocol', default_sasl_protocol)) == 'SCRAM-SHA-512' and not omit_jaas_configs:
            final_dict[config_prefix + 'sasl.mechanism'] = 'SCRAM-SHA-512'
            final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.scram.ScramLoginModule required username=\"' + sasl_scram_username + '\" password=\"' + sasl_scram_password + '\";'

        if self.normalize_sasl_protocol(listener_dict.get('sasl_protocol', default_sasl_protocol)) == 'SCRAM-SHA-256' and not omit_jaas_configs:
            final_dict[config_prefix + 'sasl.mechanism'] = 'SCRAM-SHA-256'
            final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.scram.ScramLoginModule required username=\"' + sasl_scram256_username + '\" password=\"' + sasl_scram256_password + '\";'

        if self.normalize_sasl_protocol(listener_dict.get('sasl_protocol', default_sasl_protocol)) == 'GSSAPI':
            final_dict[config_prefix + 'sasl.mechanism'] = 'GSSAPI'
            final_dict[config_prefix + 'sasl.kerberos.service.name'] = kerberos_kafka_broker_primary

        if self.normalize_sasl_protocol(listener_dict.get('sasl_protocol', default_sasl_protocol)) == 'GSSAPI' and not omit_jaas_configs:
            final_dict[config_prefix + 'sasl.jaas.config'] = 'com.sun.security.auth.module.Krb5LoginModule required useKeyTab=true storeKey=true keyTab=\"' + keytab_path + '\" principal=\"' + kerberos_principal + '\";'

        if not omit_oauth_configs:
            if self.normalize_sasl_protocol(listener_dict.get('sasl_protocol', default_sasl_protocol)) == 'OAUTHBEARER':
                final_dict[config_prefix + 'sasl.mechanism'] = 'OAUTHBEARER'
                final_dict[config_prefix + 'sasl.login.callback.handler.class'] = 'io.confluent.kafka.clients.plugins.auth.token.TokenUserLoginCallbackHandler'

            if self.normalize_sasl_protocol(listener_dict.get('sasl_protocol', default_sasl_protocol)) == 'OAUTHBEARER' and not omit_jaas_configs:
                final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required username=\"' + oauth_username + '\" password=\"' + oauth_password + '\" metadataServerUrls=\"' + mds_bootstrap_server_urls + '\";'

        return final_dict

    def c3_connect_properties(self, connect_group_list, groups, hostvars, ssl_enabled, http_protocol, port, default_connect_group_id,
            truststore_path, truststore_storepass, keystore_path, keystore_storepass, keystore_keypass ):
        # For c3's connect properties, inputs a list of ansible groups of connect hosts, as well as their ssl settings
        # Outputs a properties dictionary with properties necessary to connect to each connect group
        # Other inputs help fill out the properties
        final_dict = {}
        for ansible_group in connect_group_list:
            # connect_group_list defaults to ['kafka_connect'], but there may be scenario where no connect group exists
            if ansible_group in groups.keys() and len(groups[ansible_group]) > 0:
                delegate_host = hostvars[groups[ansible_group][0]]
                group_id = delegate_host.get('kafka_connect_group_id', default_connect_group_id)

                urls = []
                for host in groups[ansible_group]:
                    if hostvars[host].get('kafka_connect_ssl_enabled', ssl_enabled):
                        protocol = 'https'
                    else:
                        protocol = 'http'
                    urls.append(protocol + '://' + self.resolve_hostname(hostvars[host]) + ':' + str(hostvars[host].get('kafka_connect_rest_port', port)))

                final_dict['confluent.controlcenter.connect.' + group_id + '.cluster'] = ','.join(urls)

                if delegate_host.get('kafka_connect_ssl_enabled', ssl_enabled):
                    final_dict['confluent.controlcenter.connect.' + group_id + '.ssl.truststore.location'] = truststore_path
                    final_dict['confluent.controlcenter.connect.' + group_id + '.ssl.truststore.password'] = truststore_storepass
                    final_dict['confluent.controlcenter.connect.' + group_id + '.ssl.keystore.location'] = keystore_path
                    final_dict['confluent.controlcenter.connect.' + group_id + '.ssl.keystore.password'] = keystore_storepass
                    final_dict['confluent.controlcenter.connect.' + group_id + '.ssl.key.password'] = keystore_keypass

        return final_dict

    def c3_ksql_properties(self, ksql_group_list, groups, hostvars, ssl_enabled, http_protocol, port,
            truststore_path, truststore_storepass, keystore_path, keystore_storepass, keystore_keypass ):
        # For c3's ksql properties, inputs a list of ansible groups of ksql hosts, as well as their ssl settings
        # Outputs a properties dictionary with properties necessary to connect to each ksql group
        # Other inputs help fill out the properties
        final_dict = {}
        for ansible_group in ksql_group_list:
            # ksql_group_list defaults to ['ksql'], but there may be scenario where no ksql group exists
            if ansible_group in groups.keys() and len(groups[ansible_group]) > 0:
                urls = []
                advertised_urls = []
                for host in groups[ansible_group]:
                    if hostvars[host].get('ksql_ssl_enabled', ssl_enabled):
                        protocol = 'https'
                    else:
                        protocol = 'http'
                    urls.append(protocol + '://' + self.resolve_hostname(hostvars[host]) + ':' + str(hostvars[host].get('ksql_listener_port', port)))
                    advertised_urls.append(protocol + '://' + hostvars[host].get('ksql_advertised_listener_hostname', self.resolve_hostname(hostvars[host])) + ':' + str(hostvars[host].get('ksql_listener_port', port)))

                final_dict['confluent.controlcenter.ksql.' + ansible_group + '.url'] = ','.join(urls)
                final_dict['confluent.controlcenter.ksql.' + ansible_group + '.advertised.url'] = ','.join(advertised_urls)

                if hostvars[groups[ansible_group][0]].get('ksql_ssl_enabled', ssl_enabled):
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.truststore.location'] = truststore_path
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.truststore.password'] = truststore_storepass
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.keystore.location'] = keystore_path
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.keystore.password'] = keystore_storepass
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.key.password'] = keystore_keypass

        return final_dict
