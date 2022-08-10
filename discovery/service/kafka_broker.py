import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices
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

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()

    def build_properties(self):

        service = ConfluentServices.KAFKA_BROKER
        # Get the hosts for given service
        hosts = self.get_service_host(service, self.inventory)
        if not hosts:
            logger.error(f"Could not find any host with service {service.value.get('name')} ")

        host_service_properties = self.get_property_mappings(self.input_context, service, hosts)
        service_properties = host_service_properties.get(hosts[0])

        # Build service user group properties
        self.__build_daemon_properties(self.input_context, service, hosts)

        # Build broker id mappings
        self.__build_broker_host_properties(host_service_properties)

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
        for key, value in vars(KafkaServicePropertyBaseBuilder).items():
            if callable(getattr(KafkaServicePropertyBaseBuilder, key)) and key.startswith("_build"):
                func = getattr(KafkaServicePropertyBaseBuilder, key)
                logger.debug(f"Calling KafkaBroker property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_broker_host_properties(self, host_service_properties):
        for hostname, properties in host_service_properties.items():
            key = "broker.id"
            host = self.inventory.get_host(hostname)
            host.set_variable(key, int(properties.get(key)))
            self.mapped_service_properties.add(key)

    def __build_custom_properties(self, service_properties: dict, mapped_properties: set):

        group = "kafka_broker_custom_properties"
        skip_properties = set(FileUtils.get_kafka_broker_configs("skip_properties"))
        self.build_custom_properties(inventory=self.inventory,
                                     group= group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties)


    def __build_runtime_properties(self, service_properties: dict):
        pass

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

    def _build_default_listeners(self, service_prop: dict) -> tuple:

        default_listeners = dict()
        default_scram_users = dict()
        default_scram256_users = dict()
        default_plain_users = dict()

        key = "listeners"
        self.mapped_service_properties.add(key)

        listeners = service_prop.get(key).split(",")
        for listener in listeners:
            from urllib.parse import urlparse
            parsed_uri = urlparse(listener)
            name = parsed_uri.scheme
            port = parsed_uri.port

            key = f"listener.name.{name}.sasl.enabled.mechanisms"
            self.mapped_service_properties.add(key)

            sasl_protocol = service_prop.get(key)
            default_listeners[name] = {
                "name": name.upper(),
                "port": port,
                "sasl_protocol": sasl_protocol
            }

            # Add the users to corresponding sasl mechanism
            key = f"listener.name.{name.lower()}.{sasl_protocol.lower()}.sasl.jaas.config"
            _dict = locals()[f"default_{sasl_protocol.lower()}_users"]
            _dict.update(self.__get_user_dict(service_prop, key))
            self.mapped_service_properties.add(key)

        return 'all', {
            "kafka_broker_default_listeners": default_listeners,
            "sasl_scram_users": default_scram_users,
            "sasl_scram256_users": default_scram256_users,
            "sasl_plain_users": default_plain_users
        }

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


class KafkaServicePropertyBuilder60(KafkaServicePropertyBaseBuilder):
    pass


class KafkaServicePropertyBuilder61(KafkaServicePropertyBaseBuilder):
    pass


class KafkaServicePropertyBuilder62(KafkaServicePropertyBaseBuilder):
    pass


class KafkaServicePropertyBuilder70(KafkaServicePropertyBaseBuilder):
    pass


class KafkaServicePropertyBuilder71(KafkaServicePropertyBaseBuilder):
    pass


class KafkaServicePropertyBuilder72(KafkaServicePropertyBaseBuilder):
    pass
