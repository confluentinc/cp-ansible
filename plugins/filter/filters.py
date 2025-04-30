import re

DOCUMENTATION = '''
---
module: filter
description: This plugin contains python functions which act as custom filters to generate configurations based on Ansible input.
'''


class FilterModule(object):
    def filters(self):
        return {
            'normalize_sasl_protocol': self.normalize_sasl_protocol,
            'kafka_protocol_normalized': self.kafka_protocol_normalized,
            'kafka_protocol': self.kafka_protocol,
            'kafka_protocol_defaults': self.kafka_protocol_defaults,
            'get_sasl_mechanisms': self.get_sasl_mechanisms,
            'get_hostnames': self.get_hostnames,
            'split_to_list': self.split_to_list,
            'get_roles': self.get_roles,
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
            'c3_ksql_properties': self.c3_ksql_properties,
            'resolve_principal': self.resolve_principal
        }

    def normalize_sasl_protocol(self, protocols):
        # Returns a list of standardized values for sasl mechanism strings
        protocol_list = self.split_to_list(protocols)

        normalized_protocols = []
        for protocol in protocol_list:
            if protocol.lower() == 'kerberos':
                normalized = 'GSSAPI'
            elif protocol.upper() == 'SCRAM':
                normalized = 'SCRAM-SHA-512'
            elif protocol.lower() == 'scram256':
                normalized = 'SCRAM-SHA-256'
            elif protocol.upper() == 'PLAIN':
                normalized = 'PLAIN'
            elif protocol.upper() == 'OAUTH':
                normalized = 'OAUTHBEARER'
            else:
                normalized = 'none'
            normalized_protocols.append(normalized)
        return normalized_protocols

    def kafka_protocol_normalized(self, sasl_protocols_normalized, ssl_enabled):
        # Joins a sasl mechanism and tls setting to return a kafka protocol
        required_mechanisms = ['GSSAPI', 'PLAIN', 'SCRAM-SHA-512', 'SCRAM-SHA-256', 'OAUTHBEARER']

        if ssl_enabled and self.all_elements_present(sasl_protocols_normalized, required_mechanisms):
            kafka_protocol = 'SASL_SSL'
        elif not ssl_enabled and self.all_elements_present(sasl_protocols_normalized, required_mechanisms):
            kafka_protocol = 'SASL_PLAINTEXT'
        elif ssl_enabled and 'none' in sasl_protocols_normalized:
            kafka_protocol = 'SSL'
        else:
            kafka_protocol = 'PLAINTEXT'
        return kafka_protocol

    def split_to_list(self, string):
        return re.sub(r"[ \t]", "", string).split(',')

    def all_elements_present(self, sasl_protocols_normalized, required_mechanisms):
        return all(protocol in required_mechanisms for protocol in sasl_protocols_normalized)

    def kafka_protocol(self, sasl_protocol, ssl_enabled):
        # Joins a sasl mechanism and tls setting to return a kafka protocol
        sasl_protocols_normalized = self.normalize_sasl_protocol(sasl_protocol)
        kafka_protocol = self.kafka_protocol_normalized(sasl_protocols_normalized, ssl_enabled)
        return kafka_protocol

    def kafka_protocol_defaults(self, listener, default_ssl_enabled, default_sasl_protocol):
        # Joins a sasl mechanism and tls setting and their default values, to return a kafka protocol
        ssl_enabled = listener.get('ssl_enabled', default_ssl_enabled)
        sasl_protocol = listener.get('sasl_protocol', default_sasl_protocol)
        sasl_protocols_normalized = self.normalize_sasl_protocol(sasl_protocol)
        kafka_protocol = self.kafka_protocol_normalized(sasl_protocols_normalized, ssl_enabled)
        return kafka_protocol

    def get_sasl_mechanisms(self, listeners_dict, default_sasl_protocol):
        # Loops over listeners dictionary and returns list of sasl mechanisms
        mechanisms = []
        for listener in listeners_dict:
            sasl_protocol = listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)
            mechanisms = mechanisms + self.normalize_sasl_protocol(sasl_protocol)
        return mechanisms

    def get_hostnames(self, listeners_dict, default_hostname):
        # Loops over listeners dictionary and returns all hostnames attached to a listener
        hostnames = []
        for listener in listeners_dict:
            hostname = listeners_dict[listener].get('hostname', default_hostname)
            hostnames = hostnames + [hostname]
        return hostnames

    def get_roles(self, basic_users_dict):
        # Loops over basic_users dictionary and returns all roles attached to each user
        roles = []
        for user in basic_users_dict:
            user_roles = basic_users_dict[user].get('roles', 'admin').split(',')
            roles = roles + user_roles
        return roles

    def resolve_hostname(self, hosts_hostvars_dict):
        # Goes through selected possible VARs to provide the HOSTNAME for a given node for internal addressing within Confluent Platform
        if hosts_hostvars_dict.get('hostname_aliasing_enabled') is True:
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
        extension = 'dns:' + ",dns:".join(hostnames)
        return extension

    def ssl_required(self, listeners_dict, default_ssl_enabled):
        # Loops over listeners dictionary and returns True if any have TLS encryption enabled
        ssl_required = False
        for listener in listeners_dict:
            ssl_enabled = listeners_dict[listener].get('ssl_enabled', default_ssl_enabled)
            ssl_required = ssl_required is True or ssl_enabled is True
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
        properties_tmp = {}

        for prop in properties_dict:
            if properties_dict[prop].get('enabled'):
                for p in properties_dict[prop].get('properties'):
                    properties_tmp[p] = str(properties_dict[prop].get('properties')[p])
                final_dict.update(properties_tmp)
                properties_tmp = {}
        return final_dict

    def split_to_dict(self, string):
        # Splits a string like key=val,key=val into dict
        return dict(x.split('=') for x in string.split(','))

    def split_newline_to_dict(self, string):
        # Splits a string like key=val\nkey=val=with=equals\nkey=val into dict
        final_dict = {}
        for x in string.split('\n'):
            prop_list = x.split('=', 1)
            if (len(prop_list) == 2):
                final_dict[prop_list[0]] = prop_list[1]
        return final_dict

    def listener_properties(self, listeners_dict, default_ssl_enabled,
                            bouncy_castle_keystore, default_ssl_client_authentication,
                            default_principal_mapping_rules, default_sasl_protocol,
                            kafka_broker_truststore_path, kafka_broker_truststore_storepass,
                            kafka_broker_keystore_path,
                            kafka_broker_keystore_storepass,
                            kafka_broker_keystore_keypass,
                            plain_jaas_config, keytab_path,
                            kerberos_principal, kerberos_primary,
                            scram_user, scram_password, scram256_user,
                            scram256_password, rbac_enabled_public_pem_path, oauth_enabled, oauth_jwks_uri, oauth_expected_audience,
                            oauth_sub_claim, rbac_enabled, kraft_listener, idp_self_signed):
        # For kafka broker properties: Takes listeners dictionary and outputs all properties based on the listeners' settings
        # Other inputs help fill out the properties
        final_dict = {}
        for listener in listeners_dict:
            listener_name = listeners_dict[listener].get('name').lower()
            sasl_protocol = listeners_dict[listener].get('sasl_protocol', default_sasl_protocol)
            normalize_sasl_protocols = self.normalize_sasl_protocol(sasl_protocol)
            final_dict['listener.name.' + listener_name + '.sasl.enabled.mechanisms'] = ','.join(normalize_sasl_protocols)
            if listeners_dict[listener].get('ssl_enabled', default_ssl_enabled):
                final_dict['listener.name.' + listener_name + '.ssl.truststore.location'] = kafka_broker_truststore_path
                final_dict['listener.name.' + listener_name + '.ssl.truststore.password'] = str(kafka_broker_truststore_storepass)
                final_dict['listener.name.' + listener_name + '.ssl.keystore.location'] = kafka_broker_keystore_path
                final_dict['listener.name.' + listener_name + '.ssl.keystore.password'] = str(kafka_broker_keystore_storepass)
                final_dict['listener.name.' + listener_name + '.ssl.key.password'] = str(kafka_broker_keystore_keypass)

                # we check 3 places for ssl_client_authentication
                # 1 listener dict ssl_client_authentication (listener level new variable)
                # 2 listener dict ssl_mutual_auth_enabled (listener level deprecated variable)
                # 3 default_ssl_client_authentication (global level new variable)
                mtls_mode = listeners_dict[listener].get('ssl_client_authentication', 'none')
                if mtls_mode == 'none':
                    if listeners_dict[listener].get('ssl_mutual_auth_enabled', False):
                        mtls_mode = 'required'
                    else:
                        mtls_mode = default_ssl_client_authentication

                final_dict['listener.name.' + listener_name + '.ssl.client.auth'] = mtls_mode
                final_dict['listener.name.' + listener_name + '.ssl.principal.mapping.rules'] = \
                    ','.join(listeners_dict[listener].get('principal_mapping_rules', default_principal_mapping_rules))

            if bouncy_castle_keystore:
                final_dict['listener.name.' + listener_name + '.ssl.keymanager.algorithm'] = 'PKIX'
                final_dict['listener.name.' + listener_name + '.ssl.trustmanager.algorithm'] = 'PKIX'
                final_dict['listener.name.' + listener_name + '.ssl.keystore.type'] = 'BCFKS'
                final_dict['listener.name.' + listener_name + '.ssl.truststore.type'] = 'BCFKS'
                final_dict['listener.name.' + listener_name + '.ssl.enabled.protocols'] = 'TLSv1.2,TLSv1.3'

            if 'PLAIN' in normalize_sasl_protocols:
                final_dict['listener.name.' + listener_name + '.plain.sasl.jaas.config'] = plain_jaas_config

            if 'GSSAPI' in normalize_sasl_protocols:
                final_dict['listener.name.' + listener_name + '.sasl.kerberos.service.name'] = kerberos_primary
                final_dict['listener.name.' + listener_name + '.gssapi.sasl.jaas.config'] =\
                    'com.sun.security.auth.module.Krb5LoginModule required useKeyTab=true storeKey=true keyTab=\"' +\
                    keytab_path + '\" principal=\"' + kerberos_principal + '\";'

            if 'SCRAM-SHA-512' in normalize_sasl_protocols:
                final_dict['listener.name.' + listener_name + '.scram-sha-512.sasl.jaas.config'] =\
                    'org.apache.kafka.common.security.scram.ScramLoginModule required username=\"' +\
                    scram_user + '\" password=\"' + str(scram_password) + '\";'

            if 'SCRAM-SHA-256' in normalize_sasl_protocols:
                final_dict['listener.name.' + listener_name + '.scram-sha-256.sasl.jaas.config'] =\
                    'org.apache.kafka.common.security.scram.ScramLoginModule required username=\"' +\
                    scram256_user + '\" password=\"' + scram256_password + '\";'

            if 'OAUTHBEARER' in normalize_sasl_protocols:
                final_dict['listener.name.' + listener_name + '.principal.builder.class'] =\
                    'io.confluent.kafka.security.authenticator.OAuthKafkaPrincipalBuilder'

            if 'OAUTHBEARER' in normalize_sasl_protocols and not oauth_enabled:
                final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.jaas.config'] =\
                    'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required publicKeyPath=\"' + rbac_enabled_public_pem_path + '\";'
                final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.server.callback.handler.class'] =\
                    'io.confluent.kafka.server.plugins.auth.token.TokenBearerValidatorCallbackHandler'
                final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.login.callback.handler.class'] =\
                    'io.confluent.kafka.server.plugins.auth.token.TokenBearerServerLoginCallbackHandler'

            if 'OAUTHBEARER' in normalize_sasl_protocols and \
                    oauth_enabled and rbac_enabled:
                final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.server.callback.handler.class'] =\
                    'io.confluent.kafka.server.plugins.auth.token.CompositeBearerValidatorCallbackHandler'
                final_dict['listener.name.' + listener_name + '.sasl.oauthbearer.jwks.endpoint.url'] = oauth_jwks_uri
                final_dict['listener.name.' + listener_name + '.sasl.oauthbearer.sub.claim.name'] = oauth_sub_claim

            if 'OAUTHBEARER' in normalize_sasl_protocols \
                    and oauth_enabled and not rbac_enabled:
                final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.server.callback.handler.class'] =\
                    'org.apache.kafka.common.security.oauthbearer.secured.OAuthBearerValidatorCallbackHandler'
                final_dict['listener.name.' + listener_name + '.sasl.oauthbearer.jwks.endpoint.url'] = oauth_jwks_uri
                final_dict['listener.name.' + listener_name + '.sasl.oauthbearer.sub.claim.name'] = oauth_sub_claim

            if 'OAUTHBEARER' in normalize_sasl_protocols and \
                    oauth_enabled:
                if rbac_enabled and idp_self_signed:
                    final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.jaas.config'] =\
                        'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required publicKeyPath=\"' + \
                        rbac_enabled_public_pem_path + '\" ssl.truststore.location=\"' + kafka_broker_truststore_path + \
                        '\" ssl.truststore.password=\"' + kafka_broker_truststore_storepass + '\" unsecuredLoginStringClaim_sub="thePrincipalName";'
                if (rbac_enabled and (not idp_self_signed)):
                    final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.jaas.config'] =\
                        'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required publicKeyPath=\"' + \
                        rbac_enabled_public_pem_path + '\" unsecuredLoginStringClaim_sub="thePrincipalName";'
                if ((not rbac_enabled) and idp_self_signed):
                    final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.jaas.config'] =\
                        'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required' + \
                        ' ssl.truststore.location=\"' + kafka_broker_truststore_path + \
                        '\" ssl.truststore.password=\"' + kafka_broker_truststore_storepass + '\" unsecuredLoginStringClaim_sub="thePrincipalName";'
                if ((not rbac_enabled) and (not idp_self_signed)):
                    final_dict['listener.name.' + listener_name + '.oauthbearer.sasl.jaas.config'] =\
                        'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required unsecuredLoginStringClaim_sub="thePrincipalName";'

            if 'OAUTHBEARER' in normalize_sasl_protocols and \
                    oauth_enabled and oauth_expected_audience != 'none':
                final_dict['listener.name.' + listener_name + '.sasl.oauthbearer.expected.audience'] = oauth_expected_audience

            if kraft_listener and (rbac_enabled or oauth_enabled):
                final_dict['listener.name.' + listener_name + '.principal.builder.class'] =\
                    'io.confluent.kafka.security.authenticator.OAuthKafkaPrincipalBuilder'

        return final_dict

    def client_properties(self, listener_dict, default_ssl_enabled, bouncy_castle_keystore, default_ssl_mutual_auth_enabled, default_sasl_protocol,
                          config_prefix, truststore_path, truststore_storepass, public_certificates_enabled, keystore_path, keystore_storepass,
                          keystore_keypass, omit_jaas_configs, sasl_plain_username, sasl_plain_password, sasl_scram_username, sasl_scram_password,
                          sasl_scram256_username, sasl_scram256_password, kerberos_kafka_broker_primary, keytab_path, kerberos_principal,
                          omit_oauth_configs, oauth_username, oauth_password, mds_bootstrap_server_urls, oauth_enabled, oauth_superuser_client_id,
                          oauth_superuser_client_password, oauth_groups_scope, oauth_token_uri, idp_self_signed, kraft_listener):
        # For any kafka client's properties: Takes in a single kafka listener and output properties to connect to that listener
        # Other inputs help fill out the properties
        final_dict = {
            config_prefix + 'security.protocol': self.kafka_protocol_defaults(listener_dict, default_ssl_enabled, default_sasl_protocol)
        }
        if listener_dict.get('ssl_enabled', default_ssl_enabled) and not public_certificates_enabled:
            # Public certificates are in default java truststore, so these properties should be ommitted
            final_dict[config_prefix + 'ssl.truststore.location'] = truststore_path
            final_dict[config_prefix + 'ssl.truststore.password'] = str(truststore_storepass)

        if listener_dict.get('ssl_mutual_auth_enabled', default_ssl_mutual_auth_enabled):
            final_dict[config_prefix + 'ssl.keystore.location'] = keystore_path
            final_dict[config_prefix + 'ssl.keystore.password'] = str(keystore_storepass)
            final_dict[config_prefix + 'ssl.key.password'] = str(keystore_keypass)

        if bouncy_castle_keystore:
            final_dict[config_prefix + 'ssl.keymanager.algorithm'] = 'PKIX'
            final_dict[config_prefix + 'ssl.trustmanager.algorithm'] = 'PKIX'
            final_dict[config_prefix + 'ssl.keystore.type'] = 'BCFKS'
            final_dict[config_prefix + 'ssl.truststore.type'] = 'BCFKS'

        sasl_protocols = listener_dict.get('sasl_protocol', default_sasl_protocol)
        normalize_sasl_protocols = self.normalize_sasl_protocol(sasl_protocols)
        if normalize_sasl_protocols[0] == 'PLAIN' and not omit_jaas_configs:
            final_dict[config_prefix + 'sasl.mechanism'] = 'PLAIN'
            final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.plain.PlainLoginModule required username=\"' +\
                sasl_plain_username +\
                '\" password=\"' +\
                str(sasl_plain_password) + '\";'

        if normalize_sasl_protocols[0] == 'SCRAM-SHA-512' and not omit_jaas_configs and not kraft_listener:
            final_dict[config_prefix + 'sasl.mechanism'] = 'SCRAM-SHA-512'
            final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.scram.ScramLoginModule required username=\"' +\
                sasl_scram_username + '\" password=\"' + str(sasl_scram_password) + '\";'

        if normalize_sasl_protocols[0] == 'SCRAM-SHA-256' and not omit_jaas_configs and not kraft_listener:
            final_dict[config_prefix + 'sasl.mechanism'] = 'SCRAM-SHA-256'
            final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.scram.ScramLoginModule required username=\"' +\
                sasl_scram256_username + '\" password=\"' + sasl_scram256_password + '\";'

        if normalize_sasl_protocols[0] == 'GSSAPI':
            final_dict[config_prefix + 'sasl.mechanism'] = 'GSSAPI'
            final_dict[config_prefix + 'sasl.kerberos.service.name'] = kerberos_kafka_broker_primary

        if normalize_sasl_protocols[0] == 'GSSAPI' and not omit_jaas_configs:
            final_dict[config_prefix + 'sasl.jaas.config'] = 'com.sun.security.auth.module.Krb5LoginModule required useKeyTab=true storeKey=true keyTab=\"' +\
                keytab_path + '\" principal=\"' + kerberos_principal + '\";'

        if not omit_oauth_configs:
            if normalize_sasl_protocols[0] == 'OAUTHBEARER' and not oauth_enabled:
                final_dict[config_prefix + 'sasl.mechanism'] = 'OAUTHBEARER'
                final_dict[config_prefix + 'sasl.login.callback.handler.class'] = 'io.confluent.kafka.clients.plugins.auth.token.TokenUserLoginCallbackHandler'
                final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required username=\"' +\
                    oauth_username + '\" password=\"' + str(oauth_password) + '\" metadataServerUrls=\"' + mds_bootstrap_server_urls + '\";'

            if normalize_sasl_protocols[0] == 'OAUTHBEARER' and oauth_enabled:
                final_dict[config_prefix + 'sasl.mechanism'] = 'OAUTHBEARER'
                final_dict[config_prefix + 'sasl.login.callback.handler.class'] =\
                    'org.apache.kafka.common.security.oauthbearer.secured.OAuthBearerLoginCallbackHandler'
                final_dict[config_prefix + 'sasl.login.connect.timeout'] = '15000'
                final_dict[config_prefix + 'sasl.oauthbearer.token.endpoint.url'] = oauth_token_uri

                if (oauth_groups_scope == 'none' and (not idp_self_signed)):
                    final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required ' + \
                        'clientId=\"' + oauth_superuser_client_id + '\" clientSecret=\"' + str(oauth_superuser_client_password) + '\";'

                if (oauth_groups_scope != 'none' and (not idp_self_signed)):
                    final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required ' + \
                        'clientId=\"' + oauth_superuser_client_id + '\" clientSecret=\"' + str(oauth_superuser_client_password) + \
                        '\" scope=\"' + oauth_groups_scope + '\";'

                if oauth_groups_scope == 'none' and idp_self_signed:
                    final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required ' + \
                        'clientId=\"' + oauth_superuser_client_id + '\" clientSecret=\"' + str(oauth_superuser_client_password) + \
                        '\" ssl.truststore.location=\"' + \
                        truststore_path + '\" ssl.truststore.password=\"' + truststore_storepass + '\";'

                if oauth_groups_scope != 'none' and idp_self_signed:
                    final_dict[config_prefix + 'sasl.jaas.config'] = 'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required ' + \
                        'clientId=\"' + oauth_superuser_client_id + '\" clientSecret=\"' + str(oauth_superuser_client_password) + \
                        '\" scope=\"' + oauth_groups_scope + \
                        '\" ssl.truststore.location=\"' + truststore_path + '\" ssl.truststore.password=\"' + truststore_storepass + '\";'

        return final_dict

    def c3_connect_properties(self, connect_group_list, groups, hostvars, ssl_enabled, http_protocol, port, default_connect_group_id,
                              truststore_path, truststore_storepass, keystore_path, keystore_storepass, keystore_keypass,
                              oauth_enabled, rbac_enabled, oauth_user, oauth_password, oauth_groups_scope, idp_self_signed):
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

                if delegate_host.get('kafka_connect_oauth_enabled', oauth_enabled) and not rbac_enabled:
                    final_dict['confluent.controlcenter.connect.' + group_id + '.oauthbearer.login.client.id'] = oauth_user
                    final_dict['confluent.controlcenter.connect.' + group_id + '.oauthbearer.login.client.secret'] = oauth_password

                if delegate_host.get('kafka_connect_oauth_enabled', oauth_enabled) and not rbac_enabled and oauth_groups_scope != 'none':
                    final_dict['confluent.controlcenter.connect.' + group_id + '.oauthbearer.login.oauth.scope'] = oauth_groups_scope

                if delegate_host.get('kafka_connect_oauth_enabled', oauth_enabled) and not rbac_enabled and idp_self_signed:
                    final_dict['confluent.controlcenter.connect.' + group_id + '.ssl.truststore.location'] = truststore_path
                    final_dict['confluent.controlcenter.connect.' + group_id + '.ssl.truststore.password'] = truststore_storepass

        return final_dict

    def c3_ksql_properties(self, ksql_group_list, groups, hostvars, ssl_enabled, http_protocol, port,
                           truststore_path, truststore_storepass, keystore_path, keystore_storepass, keystore_keypass,
                           oauth_enabled, rbac_enabled, oauth_user, oauth_password, oauth_groups_scope, idp_self_signed):
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
                    advertised_urls.append(protocol + '://' + hostvars[host].get('ksql_advertised_listener_hostname', self.resolve_hostname(hostvars[host])) +
                                           ':' + str(hostvars[host].get('ksql_listener_port', port)))

                final_dict['confluent.controlcenter.ksql.' + ansible_group + '.url'] = ','.join(urls)
                final_dict['confluent.controlcenter.ksql.' + ansible_group + '.advertised.url'] = ','.join(advertised_urls)
                delegate_host = hostvars[groups[ansible_group][0]]

                if delegate_host.get('ksql_ssl_enabled', ssl_enabled):
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.truststore.location'] = truststore_path
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.truststore.password'] = str(truststore_storepass)
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.keystore.location'] = keystore_path
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.keystore.password'] = str(keystore_storepass)
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.key.password'] = str(keystore_keypass)

                if delegate_host.get('ksql_oauth_enabled', oauth_enabled) and not rbac_enabled:
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.oauthbearer.login.client.id'] = oauth_user
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.oauthbearer.login.client.secret'] = oauth_password

                if delegate_host.get('ksql_oauth_enabled', oauth_enabled) and not rbac_enabled and oauth_groups_scope != 'none':
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.oauthbearer.login.oauth.scope'] = oauth_groups_scope

                if delegate_host.get('ksql_oauth_enabled', oauth_enabled) and not rbac_enabled and idp_self_signed:
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.truststore.location'] = truststore_path
                    final_dict['confluent.controlcenter.ksql.' + ansible_group + '.ssl.truststore.password'] = truststore_storepass

        return final_dict

    def resolve_principal(self, common_names: str, rules: str):
        """
        This filter is to extract principle from the keystore based on the provided rule. This filter should be
        used when we have ssl.principal.mapping.rules variable set to some value.
        reference - https://cwiki.apache.org/confluence/display/KAFKA/KIP-371%3A+Add+a+configuration+to+build+custom+SSL+principal+name
        :param common_names:
        :param rules: Rules to map with against given common names
        :return:
        | Common Name                                       |   Mapping Pattern                                         | Mapping Replacement |  Mapped Name  |
        | CN=kafka-server1, OU=KAFKA                        | ^CN=(.*?), OU=(.*?)$                                      | $1                  | kafka-server1 |
        | CN=kafka1, OU=SME, O=mycp, L=Fulton, ST=MD, C=US  | ^CN=(.*?), OU=(.*?), O=(.*?), L=(.*?), ST=(.*?), C=(.*?)$ | $1@$2               | kafka1@SME    |
        | cn=kafka1,ou=SME,dc=mycp,dc=com                   | ^cn=(.*?),ou=(.*?),dc=(.*?),dc=(.*?)$                     | $1                  | kafka1        |

        """

        # Get all common names
        common_names = common_names.split("\n")
        # Get the default mapping value which is string representation of certificate
        principal_mapping_value = common_names[0]

        # When no extra rules just return the full common names string
        if rules == "DEFAULT":
            return principal_mapping_value

        # Get all the rules and apply one by one on given Dname
        list_of_rules = rules.split("RULE:")
        list_of_rules = [i for i in list_of_rules if i]

        for rule_str in list_of_rules:
            mapping_pattern, mapping_value, *options = rule_str.split('/')
            for common_name in common_names:
                matched = re.match(mapping_pattern, common_name)
                if bool(matched):
                    index = 1
                    for match_str in matched.groups():
                        mapping_value = mapping_value.replace(f"${index}", match_str)
                        index = index + 1

                    # Remove leading and trailing whitespaces
                    mapping_value = mapping_value.strip()
                    principal_mapping_value = mapping_value
                    case = [option for option in options[0].split(',') if option]
                    if case and case[0] == 'L':
                        principal_mapping_value = mapping_value.lower()
                    elif case and case[0] == 'U':
                        principal_mapping_value = mapping_value.upper()
                    break
            if bool(matched):
                # Remaining rules in the list are ignored when match is found
                break
        return principal_mapping_value
