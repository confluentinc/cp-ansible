import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, FileUtils

logger = Logger.get_logger()


class ZookeeperServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        obj = get_service_builder_class(modules=sys.modules[__name__],
                                        default_class_name="ZookeeperServicePropertyBaseBuilder",
                                        version=input_context.from_version)
        obj(input_context, inventory).build_properties()


class ZookeeperServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()

    def build_properties(self):

        # Get the hosts for given service
        hosts = self.get_service_host(ConfluentServices.ZOOKEEPER, self.inventory)
        if not hosts:
            logger.error(f"Could not find any host with service {ConfluentServices.ZOOKEEPER.value.get('name')} ")

        host_service_properties = self.get_property_mappings(self.input_context,
                                                             ConfluentServices.ZOOKEEPER,
                                                             hosts)
        service_properties = host_service_properties.get(hosts[0])

        # Build service user group properties
        self.__build_daemon_properties(self.input_context, ConfluentServices.ZOOKEEPER, hosts)

        # Build service properties
        self.__build_service_properties(service_properties)

        # Add custom properties
        self.__build_custom_properties(service_properties, self.mapped_service_properties)

        # Build Command line properties
        self.__build_runtime_properties(service_properties)

    def __build_daemon_properties(self, input_context: InputContext, service: ConfluentServices, hosts: list):

        response = self.get_service_user_group(input_context, service, hosts)
        self.update_inventory(self.inventory, response)

    def __build_service_properties(self, service_properties):

        for key, value in vars(ZookeeperServicePropertyBaseBuilder).items():
            if callable(getattr(ZookeeperServicePropertyBaseBuilder, key)) and key.startswith("_build"):
                func = getattr(ZookeeperServicePropertyBaseBuilder, key)
                logger.debug(f"Calling zookeeper property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, service_properties: dict, mapped_properties: set):

        group = "zookeeper_custom_properties"
        skip_properties = set(FileUtils.get_zookeeper_configs("skip_properties"))
        self.build_custom_properties(inventory=self.inventory,
                                     group= group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties)

    def __build_runtime_properties(self, service_properties: dict):
        pass

    def __get_user_dict(self, service_prop: dict, key: str) -> dict:
        pass

    def _build_service_port_properties(self, service_prop: dict) -> tuple:
        key = "clientPort"
        self.mapped_service_properties.add(key)
        return 'all', {"zookeeper_client_port": int(service_prop.get(key, 2181))}


class ZookeeperServicePropertyBuilder60(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBuilder61(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBuilder62(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBuilder70(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBuilder71(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBuilder72(ZookeeperServicePropertyBaseBuilder):
    pass
