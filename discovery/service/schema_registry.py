import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices, DEFAULT_KEY
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, FileUtils

logger = Logger.get_logger()

class_name = ""

class SchemaRegistryServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        builder_class = get_service_builder_class(modules=sys.modules[__name__],
                                                  default_class_name="SchemaRegistryServicePropertyBaseBuilder",
                                                  version=input_context.from_version)
        global class_name
        class_name = builder_class
        builder_class(input_context, inventory).build_properties()


class SchemaRegistryServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None
    hosts = []

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()
        self.service = ConfluentServices.SCHEMA_REGISTRY
        self.group = self.service.value.get("group")
    def build_properties(self):

        # Get the hosts for given service
        hosts = self.get_service_host(self.service, self.inventory)
        self.hosts = hosts

        if not hosts:
            logger.error(f"Could not find any host with service {self.service.value.get('name')} ")
            return

        host_service_properties = self.get_property_mappings(self.input_context, self.service, hosts)
        service_properties = host_service_properties.get(hosts[0]).get(DEFAULT_KEY)

        # Build service user group properties
        self.__build_daemon_properties(self.input_context, self.service, hosts)

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
        for key, value in vars(class_name).items():
            if callable(getattr(class_name, key)) and key.startswith("_build"):
                func = getattr(class_name, key)
                logger.info(f"Calling SchemaRegistry property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, host_service_properties: dict, mapped_properties: set):

        custom_group = "schema_registry_custom_properties"
        skip_properties = set(FileUtils.get_schema_registry_configs("skip_properties"))

        _host_service_properties = dict()
        for host in host_service_properties.keys():
            _host_service_properties[host] = host_service_properties.get(host).get(DEFAULT_KEY)
        self.build_custom_properties(inventory=self.inventory, group=self.service.value.get('group'),
                                     custom_properties_group_name=custom_group,
                                     host_service_properties=_host_service_properties, skip_properties=skip_properties,
                                     mapped_properties=mapped_properties)


    def __build_runtime_properties(self, hosts: list):
        # Build Java runtime overrides
        data = (self.group,
            {'schema_registry_custom_java_args': self.get_jvm_arguments(self.input_context, self.service, hosts)})
        self.update_inventory(self.inventory, data)

    def _build_ssl_properties(self, service_prop: dict) -> tuple:

        ssl_props = dict()
        key = "inter.instance.protocol"
        protocol = service_prop.get(key)
        self.mapped_service_properties.add(key)
        self.mapped_service_properties.add("security.protocol")
        is_ssl = bool(f"{protocol == 'https'}")

        ssl_props["ssl_enabled"] = is_ssl
        if is_ssl == False:
            return self.group, {}

        property_list = ["ssl.truststore.location", "ssl.truststore.password", "ssl.keystore.location",
                         "ssl.keystore.password", "ssl.key.password"]
        for property_key in property_list:
            self.mapped_service_properties.add(property_key)

        ssl_props['ssl_provided_keystore_and_truststore'] = True
        ssl_props['ssl_provided_keystore_and_truststore_remote_src'] = True

        ssl_props["schema_registry_keystore_path"] = service_prop.get("ssl.keystore.location")
        ssl_props["ssl_keystore_store_password"] = service_prop.get("ssl.keystore.password")
        ssl_props["ssl_keystore_key_password"] = service_prop.get("ssl.key.password")
        ssl_props["schema_registry_truststore_path"] = service_prop.get("ssl.truststore.location")
        ssl_props["ssl_truststore_password"] = service_prop.get("ssl.truststore.password")
        ssl_props['ssl_truststore_ca_cert_alias'] = ''

        keystore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                         keystorepass=ssl_props['ssl_keystore_store_password'],
                                                         keystorepath=ssl_props['schema_registry_keystore_path'],
                                                         hosts=self.hosts)
        truststore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                           keystorepass=ssl_props['ssl_truststore_password'],
                                                           keystorepath=ssl_props['schema_registry_truststore_path'],
                                                           hosts=self.hosts)
        if keystore_aliases:
            # Set the first alias name
            ssl_props["ssl_keystore_alias"] = keystore_aliases[0]
        if truststore_aliases:
            ssl_props["ssl_truststore_ca_cert_alias"] = truststore_aliases[0]

        return self.group, ssl_props

    def _build_mtls_property(self, service_prop: dict) -> tuple:
        key = 'ssl.client.auth'
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        if value is not None and value == 'true':
            return "schema_registry", {'ssl_mutual_auth_enabled': True}
        return self.group, {}

    def _build_authentication_property(self, service_prop: dict) -> tuple:
        key = 'authentication.method'
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        if value is not None and value == 'BASIC':
            return self.group, {'schema_registry_authentication_type': 'basic'}
        return self.group, {}

    def _build_replication_property(self, service_prop: dict) -> tuple:
        key = "kafkastore.topic.replication.factor"
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        return self.group, {"schema_registry_default_internal_replication_factor": int(value)}

    def _build_service_port_property(self, service_prop: dict) -> tuple:
        key = "listeners"
        self.mapped_service_properties.add(key)
        listeners = service_prop.get(key, "").split(',')[0]
        *_, port = listeners.split(':')
        return self.group, {"schema_registry_listener_port": int(port)}

    def _build_rbac_properties(self, service_prop: dict) -> tuple:
        key1 = 'confluent.schema.registry.authorizer.class'
        self.mapped_service_properties.add(key1)
        if service_prop.get(key1) is None:
            return 'schema_registry', {'rbac_enabled': False}
        property_dict = dict()
        property_dict['rbac_enabled'] = True
        property_dict['rbac_enabled_public_pem_path'] = service_prop.get('public.key.path')
        self.mapped_service_properties.add('public.key.path')
        self.mapped_service_properties.add('confluent.metadata.bootstrap.server.urls')
        return self.group, property_dict

    def _build_ldap_properties(self, service_prop: dict) -> tuple:
        property_dict = dict()
        key = 'confluent.metadata.basic.auth.user.info'
        self.mapped_service_properties.add(key)
        if service_prop.get(key) is not None:
            metadata_user_info = service_prop.get(key)
            property_dict['schema_registry_ldap_user'] = metadata_user_info.split(':')[0]
            property_dict['schema_registry_ldap_password'] = metadata_user_info.split(':')[1]
        return self.group, property_dict

    def _build_telemetry_properties(self, service_prop: dict) -> tuple:
        property_dict = self.build_telemetry_properties(service_prop)
        return self.group, property_dict

    def _build_jmx_properties(self, service_properties: dict) -> tuple:
        monitoring_details = self.get_monitoring_details(self.input_context, self.service, self.hosts,
                                                         'SCHEMA_REGISTRY_OPTS')
        service_monitoring_details = dict()
        group_name = self.service.value.get("group")

        for key, value in monitoring_details.items():
            service_monitoring_details[f"{group_name}_{key}"] = value

        return group_name, service_monitoring_details


class SchemaRegistryServicePropertyBaseBuilder60(SchemaRegistryServicePropertyBaseBuilder):
    pass


class SchemaRegistryServicePropertyBaseBuilder61(SchemaRegistryServicePropertyBaseBuilder):
    pass


class SchemaRegistryServicePropertyBaseBuilder62(SchemaRegistryServicePropertyBaseBuilder):
    pass


class SchemaRegistryServicePropertyBaseBuilder70(SchemaRegistryServicePropertyBaseBuilder):
    pass


class SchemaRegistryServicePropertyBaseBuilder71(SchemaRegistryServicePropertyBaseBuilder):
    pass


class SchemaRegistryServicePropertyBaseBuilder72(SchemaRegistryServicePropertyBaseBuilder):
    pass
