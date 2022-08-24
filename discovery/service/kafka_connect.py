import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, FileUtils

logger = Logger.get_logger()


class KafkaConnectServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        obj = get_service_builder_class(modules=sys.modules[__name__],
                                        default_class_name="KafkaConnectServicePropertyBaseBuilder",
                                        version=input_context.from_version)
        obj(input_context, inventory).build_properties()


class KafkaConnectServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()

    def build_properties(self):

        # Get the hosts for given service
        service = ConfluentServices.KAFKA_CONNECT
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
        for key, value in vars(KafkaConnectServicePropertyBaseBuilder).items():
            if callable(getattr(KafkaConnectServicePropertyBaseBuilder, key)) and key.startswith("_build"):
                func = getattr(KafkaConnectServicePropertyBaseBuilder, key)
                logger.debug(f"Calling KafkaConnect property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, service_properties: dict, mapped_properties: set):
        group = "kafka_connect_custom_properties"
        skip_properties = set(FileUtils.get_kafka_connect_configs("skip_properties"))
        self.build_custom_properties(inventory=self.inventory,
                                     group=group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties)

    def __build_runtime_properties(self, service_properties: dict):
        pass

    def _build_service_replication_factor(self, service_prop: dict)->tuple:
        key = "config.storage.replication.factor"
        self.mapped_service_properties.add(key)
        return "all", {"kafka_connect_default_internal_replication_factor": int(service_prop.get(key))}

    def _build_config_storage_topic(self, service_prop:dict)->tuple:
        key = "config.storage.topic"
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        return "all", {"kafka_connect_group_id": value.rstrip("-configs")}

    def _build_monitoring_interceptor_propperty(self, service_prop:dict)->tuple:
        key = "confluent.monitoring.interceptor.topic"
        self.mapped_service_properties.add(key)
        return "all", { "kafka_connect_monitoring_interceptors_enabled": key in service_prop}

    def _build_connect_group_id(self, service_prop:dict)->tuple:
        key = "group.id"
        self.mapped_service_properties.add(key)
        return "all", {"kafka_connect_group_id": service_prop.get(key)}

    def _build_service_protocol_port(self, service_prop: dict) -> tuple:
        key = "listeners"
        self.mapped_service_properties.add(key)
        from urllib.parse import urlparse
        parsed_uri = urlparse(service_prop.get(key))
        return "all", {
            "kafka_connect_http_protocol": parsed_uri.scheme,
            "kafka_connect_rest_port": parsed_uri.port
        }

    def _build_advertised_protocol_port(self, service_prop:dict) -> tuple:
        key1 = "rest.advertised.listener"
        self.mapped_service_properties.add(key1)

        key2 = "rest.advertised.port"
        self.mapped_service_properties.add(key2)

        return "all", {
            "kafka_connect_http_protocol": service_prop.get(key1),
            "kafka_connect_rest_port": service_prop.get(key2)
        }

    def _build_ssl_properties(self, service_properties:dict) -> tuple:
        key = 'rest.advertised.listener'
        kafka_connect_http_protocol = service_properties.get(key)
        if kafka_connect_http_protocol != 'https':
            return "all", {}
        
        property_list = ["listeners.https.ssl.keystore.location", "listeners.https.ssl.keystore.password", "listeners.https.ssl.key.password",
                            "listeners.https.ssl.truststore.location", "listeners.https.ssl.truststore.password"]

        for property_key in property_list:
            self.mapped_service_properties.add(property_key)

        property_dict = dict()

        property_dict['ssl_enabled'] = True
        property_dict['ssl_provided_keystore_and_truststore'] = True
        property_dict['ssl_provided_keystore_and_truststore_remote_src'] = True
        property_dict['ssl_keystore_filepath'] = service_properties.get('listeners.https.ssl.keystore.location')
        property_dict['ssl_keystore_store_password'] = service_properties.get('listeners.https.ssl.keystore.password')
        property_dict['ssl_keystore_key_password'] = service_properties.get('listeners.https.ssl.key.password')
        property_dict['ssl_truststore_filepath'] = service_properties.get('listeners.https.ssl.truststore.location')
        property_dict['ssl_truststore_password'] = service_properties.get('listeners.https.ssl.truststore.password')
    
        return "kafka_connect", property_dict

class KafkaConnectServicePropertyBuilder60(KafkaConnectServicePropertyBaseBuilder):
    pass


class KafkaConnectServicePropertyBuilder61(KafkaConnectServicePropertyBaseBuilder):
    pass


class KafkaConnectServicePropertyBuilder62(KafkaConnectServicePropertyBaseBuilder):
    pass


class KafkaConnectServicePropertyBuilder70(KafkaConnectServicePropertyBaseBuilder):
    pass


class KafkaConnectServicePropertyBuilder71(KafkaConnectServicePropertyBaseBuilder):
    pass


class KafkaConnectServicePropertyBuilder72(KafkaConnectServicePropertyBaseBuilder):
    pass
