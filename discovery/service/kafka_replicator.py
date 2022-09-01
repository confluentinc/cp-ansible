import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, FileUtils

logger = Logger.get_logger()


class KafkaReplicatorServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        obj = get_service_builder_class(modules=sys.modules[__name__],
                                        default_class_name="KafkaReplicatorServicePropertyBaseBuilder",
                                        version=input_context.from_version)
        obj(input_context, inventory).build_properties()


class KafkaReplicatorServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None

    CONSUMER_CONFIG = "consumer.config"
    PRODUCER_CONFIG = "producer.config"
    REPLICATION_CONFIG = "replication.config"
    CONSUMER_MONITORING_CONFIG = "consumer.monitoring.config"
    PRODUCER_MONITORING_CONFIG = "producer.monitoring.config"

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()

    def build_properties(self):

        # Get the hosts for given service
        service = ConfluentServices.KAFKA_REPLICATOR
        hosts = self.get_service_host(service, self.inventory)
        if not hosts:
            logger.error(f"Could not find any host with service {service.value.get('name')} ")
            return

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
        for key, value in vars(KafkaReplicatorServicePropertyBaseBuilder).items():
            if callable(getattr(KafkaReplicatorServicePropertyBaseBuilder, key)) and key.startswith("_build"):
                func = getattr(KafkaReplicatorServicePropertyBaseBuilder, key)
                logger.debug(f"Calling KafkaReplicator property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, service_properties: dict, mapped_properties: set):
        skip_properties = set(FileUtils.get_kafka_replicator_configs("skip_properties"))
        self.__build_custom_properties_replication(service_properties, mapped_properties, skip_properties)
        self.__build_custom_properties_consumer(service_properties, mapped_properties, skip_properties)
        self.__build_custom_properties_producer(service_properties, mapped_properties, skip_properties)
        self.__build_custom_properties_monitoring(service_properties, mapped_properties, skip_properties)

    def __build_custom_properties_replication(self, service_properties: dict,
                                              mapped_properties: set,
                                              skip_properties: set):
        group = "kafka_connect_replicator_custom_properties"
        self.build_custom_properties(inventory=self.inventory,
                                     group=group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties.get(self.REPLICATION_CONFIG))

    def __build_custom_properties_consumer(self, service_properties: dict,
                                           mapped_properties: set,
                                           skip_properties: set):
        group = "kafka_connect_replicator_consumer_custom_properties"
        self.build_custom_properties(inventory=self.inventory,
                                     group=group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties.get(self.CONSUMER_CONFIG))

    def __build_custom_properties_producer(self, service_properties: dict,
                                           mapped_properties: set,
                                           skip_properties: set):
        group = "kafka_connect_replicator_producer_custom_properties"
        self.build_custom_properties(inventory=self.inventory,
                                     group=group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties.get(self.PRODUCER_CONFIG))

    def __build_custom_properties_monitoring(self, service_properties: dict,
                                             mapped_properties: set,
                                             skip_properties: set):
        group = "kafka_connect_replicator_monitoring_interceptor_custom_properties"
        self.build_custom_properties(inventory=self.inventory,
                                     group=group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties.get(self.CONSUMER_MONITORING_CONFIG) |
                                                        service_properties.get(self.PRODUCER_MONITORING_CONFIG))

    def __build_runtime_properties(self, service_properties: dict):
        pass

    def _build_consumer_listener_properties(self, service_prop: dict):
        consumer_properties = service_prop.get(self.CONSUMER_CONFIG)
        properties_dict = dict()
        listener_dict = dict()

        trust_store_location_key = "ssl.truststore.location"
        self.mapped_service_properties.add(trust_store_location_key)

        trust_store_pass_key = "ssl.truststore.password"
        self.mapped_service_properties.add(trust_store_pass_key)

        if trust_store_location_key in consumer_properties and trust_store_pass_key in consumer_properties:
            properties_dict["kafka_connect_replicator_consumer_truststore_path"] = \
                consumer_properties.get(trust_store_location_key)
            properties_dict["kafka_connect_replicator_consumer_truststore_storepass"] = \
                consumer_properties.get(trust_store_pass_key)

            # Build listener properties
            listener_dict["sasl_enabled"] = True

            # Get the SASL protocol
            key = "sasl.mechanism"
            protocol = consumer_properties.get(key, "PLAIN").lower()
            listener_dict["ssl_enabled"] = protocol
            self.mapped_service_properties.add(key)

            # TODO Get mtls mechanism
            listener_dict["ssl_mutual_auth_enabled"] = False
            properties_dict["kafka_connect_replicator_consumer_listener"] = listener_dict

        return "all", properties_dict

    def _build_replicator_kerberos_property(self, service_prop: dict) -> tuple:
        monitoring_properties = service_prop.get(service_prop.get(self.REPLICATION_CONFIG))

        kerberos_details = self.__get_kerberos_key_principal(monitoring_properties)
        kerberos_props = dict()
        if kerberos_details:
            kerberos_props["kerberos_kafka_broker_primary"] = kerberos_details.get("service_name")
            kerberos_props["kafka_connect_replicator_keytab_path"] =  kerberos_details.get("key_tab")
            kerberos_props["kafka_connect_replicator_kerberos_principal"] = kerberos_details.get("kerberos_principal")

        return "all", kerberos_props

    def __get_kerberos_key_principal(self, properties:dict)->dict:
        key = "sasl.mechanism"
        sasl_mechanism = properties.get(key)
        self.mapped_service_properties.add(key)

        key = "sasl.jaas.config"
        user_dict = self.get_values_from_jaas_config(properties.get(key))
        self.mapped_service_properties.add(key)

        # Username and password for other sasl mechanism would be driven from listeners build from Kafka service
        kerberos_props = dict()
        if sasl_mechanism == "GSSAPI":
            key_tab = user_dict.get("keyTab")
            principal = user_dict.get("principal")
            kerberos_props["service_name"] = properties.get("sasl.kerberos.service.name")
            kerberos_props["keytab_path"] = key_tab
            kerberos_props["kerberos_principal"] = principal

        return kerberos_props

    def _build_config_storage_topic(self, service_prop: dict) -> tuple:
        replication_props = service_prop.get(self.REPLICATION_CONFIG)
        key = "config.storage.topic"
        self.mapped_service_properties.add(key)
        value = replication_props.get(key)
        return "all", {"kafka_replicator_group_id": value.rstrip("-configs")}

    def _build_replicator_group_id(self, service_prop: dict)->tuple:
        replication_props = service_prop.get(self.REPLICATION_CONFIG)
        key = "config.storage.topic"
        self.mapped_service_properties.add(key)
        value = replication_props.get(key)
        return "all", {"kafka_connect_replicator_group_id": value }

    def build_replicator_ssl_config(self, service_prop: dict)->tuple:
        replication_props = service_prop.get(self.REPLICATION_CONFIG)
        ssl_props = dict()

        key = "listeners.https.ssl.keystore.location"
        self.mapped_service_properties.add(key)
        if key in replication_props:
            ssl_props["kafka_connect_replicator_ssl_enabled"] = True
            ssl_props["kafka_connect_replicator_keystore_path"] = replication_props.get(key)

            key = "listeners.https.ssl.keystore.password"
            self.mapped_service_properties.add(key)
            ssl_props["kafka_connect_replicator_keystore_storepass"] = replication_props.get(key)

            key = "listeners.https.ssl.key.password"
            self.mapped_service_properties.add(key)
            ssl_props["kafka_connect_replicator_keystore_keypass"] = replication_props.get(key)

            key = "listeners.https.ssl.truststore.location"
            self.mapped_service_properties.add(key)
            ssl_props["kafka_connect_replicator_truststore_path"] = replication_props.get(key)

            key = "listeners.https.ssl.truststore.password"
            self.mapped_service_properties.add(key)
            ssl_props["kafka_connect_replicator_truststore_storepass"] = replication_props.get(key)

        return "all", ssl_props

    def _build_replicator_offset_config(self, service_prop:dict)->tuple:
        replication_props = service_prop.get(self.REPLICATION_CONFIG)
        offset_dict = dict()
        key = "offset.start"
        self.mapped_service_properties.add(key)
        offset_dict["kafka_connect_replicator_offset_start"] = replication_props.get(key)

        key = "offset.storage.topic"
        self.mapped_service_properties.add(key)
        offset_dict["kafka_connect_replicator_offsets_topic"] = replication_props.get(key)

        return "all", offset_dict

    def _build_rest_advertised_config(self, service_prop:dict)->tuple:
        replication_props = service_prop.get(self.REPLICATION_CONFIG)
        rest_dict = dict()

        key = "rest.advertised.listener"
        self.mapped_service_properties.add(key)
        rest_dict["kafka_connect_replicator_http_protocol"] = replication_props.get(key)

        key = "rest.advertised.port"
        self.mapped_service_properties.add(key)
        rest_dict["kafka_connect_replicator_port"] = replication_props.get(key)

        return "all", rest_dict

    def _build_topic_conig(self, service_prop: dict) -> tuple:
        replication_props = service_prop.get(self.REPLICATION_CONFIG)
        topic_dict = dict()

        key = "topic.auto.create"
        self.mapped_service_properties.add(key)
        topic_dict["kafka_connect_replicator_topic_auto_create"] = replication_props.get(key)

        key = "topic.whitelist"
        self.mapped_service_properties.add(key)
        topic_dict["kafka_connect_replicator_white_list"] = replication_props.get(key)

        return "all", topic_dict


class KafkaReplicatorServicePropertyBuilder60(KafkaReplicatorServicePropertyBaseBuilder):
    pass


class KafkaReplicatorServicePropertyBuilder61(KafkaReplicatorServicePropertyBaseBuilder):
    pass


class KafkaReplicatorServicePropertyBuilder62(KafkaReplicatorServicePropertyBaseBuilder):
    pass


class KafkaReplicatorServicePropertyBuilder70(KafkaReplicatorServicePropertyBaseBuilder):
    pass


class KafkaReplicatorServicePropertyBuilder71(KafkaReplicatorServicePropertyBaseBuilder):
    pass


class KafkaReplicatorServicePropertyBuilder72(KafkaReplicatorServicePropertyBaseBuilder):
    pass
