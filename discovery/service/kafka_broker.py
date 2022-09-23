import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices, DEFAULT_KEY
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, FileUtils

logger = Logger.get_logger()


class KafkaServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        obj = get_service_builder_class(modules=sys.modules[__name__],
                                        default_class_name="KafkaServicePropertyBaseBuilder",
                                        version=input_context.from_version)
        obj(input_context, inventory).build_properties()


class KafkaServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None
    hosts = []

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()
        self.service = ConfluentServices.KAFKA_BROKER

    def build_properties(self):

        # Get the hosts for given service
        hosts = self.get_service_host(self.service, self.inventory)
        self.hosts = hosts
        if not hosts:
            logger.error(f"Could not find any host with service {self.service.value.get('name')} ")
            return

        host_service_properties = self.get_property_mappings(self.input_context, self.service, hosts)
        service_properties = host_service_properties.get(hosts[0]).get(DEFAULT_KEY)
        service_facts = AbstractPropertyBuilder.get_service_facts(self.input_context, self.service, hosts)

        # Build service user group properties
        self.__build_daemon_properties(self.input_context, self.service, hosts)

        # Build broker id mappings
        # self.__build_broker_host_properties(host_service_properties)

        # Build service properties
        self.__build_service_properties(service_properties)

        # Add custom properties
        self.__build_custom_properties(host_service_properties, self.mapped_service_properties)

        # Build Command line properties
        self.__build_runtime_properties(hosts)

    def __build_daemon_properties(self, input_context: InputContext, service: ConfluentServices, hosts: list):

        # User group information
        response = self.get_service_user_group(input_context, service, hosts)
        self.update_inventory(self.inventory, response)

    def __build_service_properties(self, service_properties):
        for key, value in vars(KafkaServicePropertyBaseBuilder).items():
            if callable(getattr(KafkaServicePropertyBaseBuilder, key)) and key.startswith("_build"):
                func = getattr(KafkaServicePropertyBaseBuilder, key)
                logger.info(f"Calling KafkaBroker property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_broker_host_properties(self, host_service_properties):
        key = "broker.id"
        self.mapped_service_properties.add(key)
        for hostname, properties in host_service_properties.items():
            default_properties = properties.get(DEFAULT_KEY)
            if key in default_properties:
                host = self.inventory.get_host(hostname)
                host.set_variable(key, int(default_properties.get(key)))

    def __build_custom_properties(self, host_service_properties: dict, mapped_properties: set):

        custom_group = "kafka_broker_custom_properties"
        skip_properties = set(FileUtils.get_kafka_broker_configs("skip_properties"))

        _host_service_properties = dict()
        for host in host_service_properties.keys():
            _host_service_properties[host] = host_service_properties.get(host).get(DEFAULT_KEY)
        self.build_custom_properties(inventory=self.inventory, group=self.service.value.get('group'),
                                     custom_properties_group_name=custom_group,
                                     host_service_properties=_host_service_properties, skip_properties=skip_properties,
                                     mapped_properties=mapped_properties)


    def __build_runtime_properties(self, hosts):
        # Build Java runtime overrides
        data = (
            'all', {'kafka_broker_custom_java_args': self.get_jvm_arguments(self.input_context, self.service, hosts)})
        self.update_inventory(self.inventory, data)

    def __get_user_dict(self, service_prop: dict, key: str) -> dict:
        users = dict()
        jaas_config = service_prop.get(key, None)
        if not jaas_config:
            return users

        # parse line to get the user configs
        for token in jaas_config.split():
            if "=" in token:
                username, password = token.split('=')
                if username.startswith('user_'):
                    principal = username.replace('user_', '')
                    # Sanitize the password
                    password = password.rstrip(';').strip('"')
                    users[principal] = {'principal': principal, 'password': password}

        return users

    def _build_replication_factors(self, service_properties: dict) -> tuple:

        property_dict = dict()
        key = "confluent.balancer.topic.replication.factor"
        value = service_properties.get(key)

        self.mapped_service_properties.add(key)
        self.mapped_service_properties.add("confluent.license.topic.replication.factor")
        self.mapped_service_properties.add("confluent.metadata.topic.replication.factor")
        property_dict["kafka_broker_default_internal_replication_factor"] = int(value)

        # Check for audit logs replication factor
        key = "confluent.security.event.logger.exporter.kafka.topic.replicas"
        audit_replication = service_properties.get(key)
        if value != audit_replication:
            property_dict["audit_logs_destination_enabled"] = True
            self.mapped_service_properties.add(key)

        return "all", property_dict

    def _build_inter_broker_listener_name(self, service_prop: dict) -> tuple:
        key = "inter.broker.listener.name"
        self.mapped_service_properties.add(key)
        return "all", {"kafka_broker_inter_broker_listener_name": service_prop.get(key).lower()}

    def _build_http_server_listener(self, service_prop: dict) -> tuple:

        key1 = "kafka.rest.bootstrap.servers"
        key2 = "kafka.rest.enable"
        key3 = "confluent.http.server.advertised.listeners"
        key4 = "confluent.http.server.listeners"
        self.mapped_service_properties.add(key1)
        self.mapped_service_properties.add(key2)
        self.mapped_service_properties.add(key3)
        self.mapped_service_properties.add(key4)

        rest_proxy_enabled = bool(service_prop.get(key2, False))
        return "all", {"kafka_broker_rest_proxy_enabled": rest_proxy_enabled}

    def _build_service_metrics(self, service_prop: dict) -> tuple:
        key = "confluent.metrics.reporter.bootstrap.servers"
        self.mapped_service_properties.add(key)
        metric_reporter_enabled = key in service_prop
        return "all", {"kafka_broker_metrics_reporter_enabled": metric_reporter_enabled}

    def _build_schema_registry_url(self, service_prop: dict) -> tuple:
        key = "confluent.schema.registry.url"
        self.mapped_service_properties.add(key)
        schema_registry_url = key in service_prop
        return "all", {"kafka_broker_schema_validation_enabled": schema_registry_url}

    def _build_broker_rest_proxy(self, service_prop: dict) -> tuple:
        property_dict = dict()
        key1 = 'kafka.rest.enable'
        key2 = 'kafka.rest.authentication.method'
        self.mapped_service_properties.add(key1)
        self.mapped_service_properties.add(key2)
        value = service_prop.get(key1, None)
        if value is not None and value == 'true':
            property_dict['kafka_broker_rest_proxy_enabled'] = True
        else:
            property_dict['kafka_broker_rest_proxy_enabled'] = False
        value2 = service_prop.get(key2, None)
        if value2 is not None and value == 'BASIC':
            property_dict['kafka_broker_rest_proxy_authentication_type'] = 'basic'
        return "all", property_dict

    def _build_ssl_properties(self, service_properties: dict) -> tuple:

        property_dict = dict()
        key = "zookeeper.ssl.client.enable"
        zookeeper_ssl_enabled = service_properties.get(key)
        if zookeeper_ssl_enabled != 'true':
            return "all", {}

        key1 = "zookeeper.ssl.truststore.location"
        key2 = "zookeeper.ssl.truststore.password"
        self.mapped_service_properties.add(key1)
        self.mapped_service_properties.add(key2)

        property_dict['ssl_truststore_filepath'] = service_properties.get(key1)
        property_dict['ssl_truststore_password'] = service_properties.get(key2)
        property_dict['ssl_enabled'] = True
        property_dict['ssl_provided_keystore_and_truststore'] = True
        property_dict['ssl_provided_keystore_and_truststore_remote_src'] = True
        property_dict['ssl_truststore_ca_cert_alias'] = ''

        if service_properties.get("confluent.http.server.ssl.keystore.location") is not None:
            property_dict['ssl_keystore_filepath'] = service_properties.get(
                "confluent.http.server.ssl.keystore.location")
            property_dict['ssl_keystore_store_password'] = service_properties.get(
                'confluent.http.server.ssl.keystore.password')
            property_dict['ssl_keystore_key_password'] = service_properties.get(
                'confluent.http.server.ssl.key.password')

        if service_properties.get("confluent.ssl.keystore.location") is not None:
            property_dict['ssl_keystore_filepath'] = service_properties.get(
                "confluent.ssl.keystore.location")
            property_dict['ssl_keystore_store_password'] = service_properties.get(
                'confluent.ssl.keystore.password')
            property_dict['ssl_keystore_key_password'] = service_properties.get(
                'confluent.ssl.key.password')

        keystore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                         keystorepass=property_dict['ssl_keystore_store_password'],
                                                         keystorepath=property_dict['ssl_keystore_filepath'],
                                                         hosts=self.hosts)
        truststore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                           keystorepass=property_dict['ssl_truststore_password'],
                                                           keystorepath=property_dict['ssl_truststore_filepath'],
                                                           hosts=self.hosts)
        if keystore_aliases:
            # Set the first alias name
            property_dict["ssl_keystore_alias"] = keystore_aliases[0]
        if truststore_aliases:
            property_dict["ssl_truststore_ca_cert_alias"] = truststore_aliases[0]

        return "kafka_broker", property_dict

    def _build_mtls_property(self, service_properties: dict) -> tuple:
        key1 = 'zookeeper.ssl.keystore.location'
        key2 = 'zookeeper.ssl.keystore.password'
        self.mapped_service_properties.add(key1)
        self.mapped_service_properties.add(key2)
        if service_properties.get(key1) is not None:
            return "kafka_broker", {'ssl_mutual_auth_enabled': True}
        return "all", {}

    def _build_fips_properties(self, service_properties: dict) -> tuple:
        key = 'enable.fips'
        self.mapped_service_properties.add(key)
        return "all", {'fips_enabled': bool(service_properties.get(key, False))}

    def _build_custom_listeners(self, service_prop: dict) -> tuple:
        custom_listeners = dict()
        default_scram_users = dict()
        default_scram256_users = dict()
        default_scram_sha_512_users = dict()
        default_plain_users = dict()
        default_gssapi_users = dict()
        default_oauthbearer_users = dict()

        key = "listeners"
        self.mapped_service_properties.add(key)

        listeners = service_prop.get(key).split(",")
        for listener in listeners:
            from urllib.parse import urlparse
            parsed_uri = urlparse(listener)
            name = parsed_uri.scheme
            port = parsed_uri.port

            key1 = f"listener.name.{name}.sasl.enabled.mechanisms"
            key2 = f"listener.name.{name}.ssl.client.auth"
            self.mapped_service_properties.add(key1)
            self.mapped_service_properties.add(key2)

            custom_listeners[name] = {
                "name": name.upper(),
                "port": port
            }

            ssl_enabled = service_prop.get(key2)
            if ssl_enabled is not None:
                custom_listeners[name]['ssl_enabled'] = True

            if 'ssl_mutual_auth_enabled' in self.inventory.groups.get('kafka_broker').vars:
                custom_listeners[name]['ssl_mutual_auth_enabled'] = True

            sasl_protocol = service_prop.get(key1)
            if sasl_protocol is not None:
                custom_listeners[name]['sasl_protocol']: sasl_protocol
                # Add the users to corresponding sasl mechanism
                key = f"listener.name.{name.lower()}.{sasl_protocol.lower()}.sasl.jaas.config"
                _dict = locals()[f"default_{sasl_protocol.lower().replace('-', '_')}_users"]
                _dict.update(self.__get_user_dict(service_prop, key))
                self.mapped_service_properties.add(key)

        return 'all', {
            "kafka_broker_custom_listeners": custom_listeners,
            "sasl_scram_users": default_scram_users,
            "sasl_scram256_users": default_scram256_users,
            "sasl_scram512_users": default_scram_sha_512_users,
            "sasl_plain_users": default_plain_users
        }

    def _build_rbac_properties(self, service_prop: dict) -> tuple:
        property_dict = dict()
        key1 = 'authorizer.class.name'
        key2 = 'super.users'
        if service_prop.get(key1) != 'io.confluent.kafka.security.authorizer.ConfluentServerAuthorizer':
            return "all", {}

        self.mapped_service_properties.add(key1)
        self.mapped_service_properties.add(key2)
        property_dict['rbac_enabled'] = True

        super_user_property = service_prop.get(key2)
        property_dict['create_mds_certs'] = False
        property_dict['mds_super_user'] = super_user_property.split(";")[0].split('User:', 1)[1]
        property_dict['mds_super_user_password'] = ''

        key3 = 'confluent.metadata.server.advertised.listeners'
        if service_prop.get(key3) is not None:
            listener = service_prop.get(key3)
            property_dict['mds_http_protocol'] = listener.split("://")[0]
            # property_dict['mds_advertised_listener_hostname'] = listener.split("://")[1].split(":")[0]
            property_dict['mds_port'] = int(listener.split("://")[1].split(":")[1])
            property_dict['rbac_enabled_private_pem_path'] = service_prop.get(
                'confluent.metadata.server.token.key.path')
            property_dict['external_mds_enabled'] = False

        self.mapped_service_properties.add('confluent.metadata.server.token.key.path')
        key4 = 'confluent.metadata.bootstrap.servers'
        if service_prop.get(key4) is not None:
            property_dict['external_mds_enabled'] = True
            property_dict['mds_broker_bootstrap_servers'] = service_prop.get(key4)

        self.mapped_service_properties.add(key3)
        self.mapped_service_properties.add(key4)

        key5 = 'kafka.rest.kafka.rest.resource.extension.class'
        if service_prop.get(key5) is not None:
            property_dict['rbac_enabled_public_pem_path'] = service_prop.get('kafka.rest.public.key.path')
            metadata_user_info = service_prop.get('kafka.rest.confluent.metadata.basic.auth.user.info')
            property_dict['kafka_broker_ldap_user'] = metadata_user_info.split(':')[0]
            property_dict['kafka_broker_ldap_password'] = metadata_user_info.split(':')[1]
            property_dict['mds_super_user_password'] = property_dict['kafka_broker_ldap_password']

        self.mapped_service_properties.add(key5)
        self.mapped_service_properties.add('kafka.rest.public.key.path')
        self.mapped_service_properties.add('kafka.rest.confluent.metadata.bootstrap.server.urls')
        self.mapped_service_properties.add('kafka.rest.confluent.metadata.basic.auth.user.info')

        return "all", property_dict

    def _build_secret_protection_key(self, service_prop: dict) -> tuple:
        master_key = self.get_secret_protection_key(self.input_context, self.service, self.hosts)
        if master_key:
            return 'all', {
                'secrets_protection_enabled': True,
                'secrets_protection_masterkey': master_key
            }
        else:
            return 'all', {}


class KafkaServicePropertyLegacyBuilder(KafkaServicePropertyBaseBuilder):
    pass


class KafkaServicePropertyBuilder60(KafkaServicePropertyLegacyBuilder):
    pass


class KafkaServicePropertyBuilder61(KafkaServicePropertyLegacyBuilder):
    pass


class KafkaServicePropertyBuilder62(KafkaServicePropertyLegacyBuilder):
    pass


class KafkaServicePropertyBuilder70(KafkaServicePropertyLegacyBuilder):
    pass


class KafkaServicePropertyBuilder71(KafkaServicePropertyLegacyBuilder):
    pass


class KafkaServicePropertyBuilder72(KafkaServicePropertyLegacyBuilder):
    pass
