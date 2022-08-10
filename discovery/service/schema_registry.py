import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices
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

        host_service_properties = self.get_property_mappings(self.input_context, service, hosts)
        service_properties = host_service_properties.get(hosts[0])

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

        ssl_props["schema_registry_ssl_enabled"] =  is_ssl

        if is_ssl:
            key = "ssl.keystore.location"
            self.mapped_service_properties.add(key)
            ssl_props["schema_registry_keystore_path"] = service_prop.get(key)

            key = "ssl.keystore.password"
            self.mapped_service_properties.add(key)
            ssl_props["schema_registry_keystore_storepass"] = service_prop.get(key)

            key = "ssl.key.password"
            self.mapped_service_properties.add(key)
            ssl_props["schema_registry_keystore_keypass"] = service_prop.get(key)

        return "all", ssl_props

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
