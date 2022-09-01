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
        from urllib.parse import urlparse
        parsed_uri = urlparse(service_prop.get(key))
        return "all", {
            "kafka_rest_http_protocol": parsed_uri.scheme,
            "kafka_rest_port": parsed_uri.port
        }

    def _build_monitoring_interceptor_propperty(self, service_prop:dict)->tuple:
        key = "confluent.monitoring.interceptor.topic"
        self.mapped_service_properties.add(key)
        return "all", { "kakfa_rest_monitoring_interceptors_enabled": key in service_prop}

    def _build_tls_properties(self, service_prop: dict) -> tuple:
        key = "listeners"
        kafka_rest_listener = service_prop.get(key)

        if kafka_rest_listener.find('https') < 0:
            return "all", {}

        property_list = ["ssl.keystore.location", "ssl.keystore.password", "ssl.key.password",
                            "ssl.truststore.location", "ssl.truststore.password"]
        for property_key in property_list:
            self.mapped_service_properties.add(property_key)

        property_dict = dict()
        property_dict['ssl_enabled'] = True
        property_dict['ssl_provided_keystore_and_truststore'] = True
        property_dict['ssl_provided_keystore_and_truststore_remote_src'] = True
        property_dict['ssl_keystore_filepath'] = service_prop.get('ssl.keystore.location')
        property_dict['ssl_keystore_store_password'] = service_prop.get('ssl.keystore.password')
        property_dict['ssl_keystore_key_password'] = service_prop.get('ssl.key.password')
        property_dict['ssl_truststore_ca_cert_alias'] = ''

        if service_prop.get('ssl.truststore.location') is not None:
            property_dict['ssl_truststore_filepath'] = service_prop.get('ssl.truststore.location')
            property_dict['ssl_truststore_password'] = service_prop.get('ssl.truststore.password')

        return "kafka_rest", property_dict

    def _build_mtls_property(self, service_prop: dict) -> tuple:
        key = 'ssl.client.auth'
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        if value is not None and value == 'true':
            return "kafka_rest", {'ssl_mutual_auth_enabled': True}
        return "all", {}

    def _build_authentication_property(self, service_prop: dict) -> tuple:
        key = 'authentication.method'
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        if value is not None and value == 'BASIC':
            return "all", {'kafka_rest_authentication_type': 'basic'}
        return "all", {}

    def _build_secret_protection_property(self, service_prop: dict) -> tuple:
        key = 'client.config.providers'
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        if value is not None and value == 'securepass':
            return "all", {'kafka_rest_secrets_protection_enabled': True}
        return "all", {}

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
