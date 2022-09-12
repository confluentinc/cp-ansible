import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices, DEFAULT_KEY
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, FileUtils

logger = Logger.get_logger()


class SchemaRegistryServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        obj = get_service_builder_class(modules=sys.modules[__name__],
                                        default_class_name="SchemaRegistryServicePropertyBaseBuilder",
                                        version=input_context.from_version)
        obj(input_context, inventory).build_properties()


class SchemaRegistryServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()

    def build_properties(self):

        # Get the hosts for given service
        service = ConfluentServices.SCHEMA_REGISTRY
        hosts = self.get_service_host(service, self.inventory)
        if not hosts:
            logger.error(f"Could not find any host with service {service.value.get('name')} ")
            return

        host_service_properties = self.get_property_mappings(self.input_context, service, hosts)
        service_properties = host_service_properties.get(hosts[0]).get(DEFAULT_KEY)

        # Build service user group properties
        self.__build_daemon_properties(self.input_context, service, hosts)

        # Build service properties
        self.__build_service_properties(service_properties)

        # Add custom properties
        self.__build_custom_properties(service_properties, self.mapped_service_properties)

        # Build Command line properties
        self.__build_runtime_properties(service_properties)

    def __build_daemon_properties(self, input_context: InputContext, service: ConfluentServices, hosts: list):

        # User group information
        response = self.get_service_user_group(input_context, service, hosts)
        self.update_inventory(self.inventory, response)

    def __build_service_properties(self, service_properties):
        for key, value in vars(SchemaRegistryServicePropertyBaseBuilder).items():
            if callable(getattr(SchemaRegistryServicePropertyBaseBuilder, key)) and key.startswith("_build"):
                func = getattr(SchemaRegistryServicePropertyBaseBuilder, key)
                logger.debug(f"Calling SchemaRegistry property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, service_properties: dict, mapped_properties: set):

        group = "schema_registry_custom_properties"
        skip_properties = set(FileUtils.get_schema_registry_configs("skip_properties"))
        self.build_custom_properties(inventory=self.inventory,
                                     group= group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties)

    def __build_runtime_properties(self, service_properties: dict):
        pass

    def _build_ssl_properties(self, service_prop: dict) -> tuple:

        ssl_props = dict()
        key = "inter.instance.protocol"
        protocol = service_prop.get(key)
        self.mapped_service_properties.add(key)
        self.mapped_service_properties.add("security.protocol")
        is_ssl = bool(f"{protocol == 'https'}")

        ssl_props["ssl_enabled"] =  is_ssl
        if is_ssl == False:
            return "all", {}

        property_list = ["ssl.truststore.location", "ssl.truststore.password", "ssl.keystore.location",
                            "ssl.keystore.password", "ssl.key.password"]
        for property_key in property_list:
            self.mapped_service_properties.add(property_key)
            
        ssl_props['ssl_provided_keystore_and_truststore'] = True
        ssl_props['ssl_provided_keystore_and_truststore_remote_src'] = True

        ssl_props["ssl_keystore_filepath"] = service_prop.get("ssl.keystore.location")
        ssl_props["ssl_keystore_store_password"] = service_prop.get("ssl.keystore.password")
        ssl_props["ssl_keystore_key_password"] = service_prop.get("ssl.key.password")
        ssl_props["ssl_truststore_filepath"] = service_prop.get("ssl.truststore.location")
        ssl_props["ssl_truststore_password"] = service_prop.get("ssl.truststore.password")
        ssl_props['ssl_truststore_ca_cert_alias'] = ''

        return "schema_registry", ssl_props

    def _build_mtls_property(self, service_prop: dict) -> tuple:
        key = 'ssl.client.auth'
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        if value is not None and value == 'true':
            return "schema_registry", {'ssl_mutual_auth_enabled': True}
        return "all", {}

    def _build_authentication_property(self, service_prop: dict) -> tuple:
        key = 'authentication.method'
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        if value is not None and value == 'BASIC':
            return "all", {'schema_registry_authentication_type': 'basic'}
        return "all", {}

    def _build_replication_property(self, service_prop: dict) -> tuple:
        key = "kafkastore.topic.replication.factor"
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        return "all", {"schema_registry_default_internal_replication_factor": int(value)}

    def _build_service_port_property(self, service_prop: dict) -> tuple:
        key = "listeners"
        self.mapped_service_properties.add(key)
        listeners = service_prop.get(key, "").split(',')[0]
        *_, port = listeners.split(':')
        return "all", {"schema_registry_listener_port": int(port)}

    def _build_rbac_properties(self, service_prop: dict) -> tuple:
        key1 = 'confluent.schema.registry.authorizer.class'
        self.mapped_service_properties.add(key1)
        if service_prop.get(key1) is None:
            return 'schema_registry', {'rbac_enabled': False}
        property_dict = dict()
        property_dict['rbac_enabled'] = True
        property_dict['rbac_enabled_public_pem_path'] = service_prop.get('public.key.path')
        property_dict['mds_bootstrap_server_urls'] = service_prop.get('confluent.metadata.bootstrap.server.urls')
        self.mapped_service_properties.add('public.key.path')
        self.mapped_service_properties.add('confluent.metadata.bootstrap.server.urls')
        return 'schema_registry', property_dict

    def _build_ldap_properties(self, service_prop: dict) -> tuple:
        property_dict = dict()
        key = 'confluent.metadata.basic.auth.user.info'
        self.mapped_service_properties.add(key)
        if service_prop.get(key) is not None:
            metadata_user_info = service_prop.get(key)
            property_dict['schema_registry_ldap_user'] = metadata_user_info.split(':')[0]
            property_dict['schema_registry_ldap_password'] = metadata_user_info.split(':')[1]
        return 'all', property_dict

class SchemaRegistryServicePropertyBuilder60(SchemaRegistryServicePropertyBaseBuilder):
    pass


class SchemaRegistryServicePropertyBuilder61(SchemaRegistryServicePropertyBaseBuilder):
    pass


class SchemaRegistryServicePropertyBuilder62(SchemaRegistryServicePropertyBaseBuilder):
    pass


class SchemaRegistryServicePropertyBuilder70(SchemaRegistryServicePropertyBaseBuilder):
    pass


class SchemaRegistryServicePropertyBuilder71(SchemaRegistryServicePropertyBaseBuilder):
    pass


class SchemaRegistryServicePropertyBuilder72(SchemaRegistryServicePropertyBaseBuilder):
    pass
