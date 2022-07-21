import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, FileUtils

logger = Logger.get_logger()


class KafkaRestServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        obj = get_service_builder_class(modules=sys.modules[__name__],
                                        default_class_name="KafkaRestServicePropertyBaseBuilder",
                                        version=input_context.from_version)
        obj(input_context, inventory).build_properties()


class KafkaRestServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()

    def build_properties(self):

        # Get the hosts for given service
        service = ConfluentServices.KAFKA_REST
        hosts = self.get_service_host(service, self.inventory)
        if not hosts:
            logger.error(f"Could not find any host with service {service.value.get('name')} ")

        host_service_properties = self.get_property_mappings(self.input_context, service, hosts)
        service_properties = host_service_properties.get(hosts[0])

        # Build service user group properties
        self.__build_daemon_properties(self.input_context, service, hosts)

        # Build service properties
        self.__build_service_properties(service_properties)

        # Add custom properties of Kafka broker
        self.__build_custom_properties(service_properties, self.mapped_service_properties)

        # Build Command line properties
        self.__build_runtime_properties(service_properties)

    def __build_daemon_properties(self, input_context: InputContext, service: ConfluentServices, hosts: list):

        # User group information
        response = self.get_service_user_group(input_context, service, hosts)
        self.update_inventory(self.inventory, response)

    def __build_service_properties(self, service_properties):
        for key, value in vars(KafkaRestServicePropertyBaseBuilder).items():
            if callable(getattr(KafkaRestServicePropertyBaseBuilder, key)) and key.startswith("_build"):
                func = getattr(KafkaRestServicePropertyBaseBuilder, key)
                logger.debug(f"Calling KafkaRest property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, service_properties: dict, mapped_properties: set):
        group = "kafka_rest_custom_properties"
        skip_properties = set(FileUtils.get_kafka_rest_configs("skip_properties"))
        self.build_custom_properties(inventory=self.inventory,
                                     group=group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties)

    def __build_runtime_properties(self, service_properties: dict):
        pass

    def _build_service_protocol_port(self, service_prop: dict) -> tuple:
        key = "listeners"
        self.mapped_service_properties.add(key)
        url = service_prop.get(key)
        protocol, host, port = url.split(":")

        return "all", {
            "kafka_rest_http_protocol": protocol,
            "kafka_rest_port": port
        }


class KafkaRestServicePropertyBuilder60(KafkaRestServicePropertyBaseBuilder):
    pass


class KafkaRestServicePropertyBuilder61(KafkaRestServicePropertyBaseBuilder):
    pass


class KafkaRestServicePropertyBuilder62(KafkaRestServicePropertyBaseBuilder):
    pass


class KafkaRestServicePropertyBuilder70(KafkaRestServicePropertyBaseBuilder):
    pass


class KafkaRestServicePropertyBuilder71(KafkaRestServicePropertyBaseBuilder):
    pass


class KafkaRestServicePropertyBuilder72(KafkaRestServicePropertyBaseBuilder):
    pass
