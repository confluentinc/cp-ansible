import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices, DEFAULT_KEY
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, FileUtils

logger = Logger.get_logger()

class_name = ""


class ZookeeperServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        builder_class = get_service_builder_class(modules=sys.modules[__name__],
                                                  default_class_name="ZookeeperServicePropertyBaseBuilder",
                                                  version=input_context.from_version)
        global class_name
        class_name = builder_class
        builder_class(input_context, inventory).build_properties()


class ZookeeperServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None
    hosts = []

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()
        self.service = ConfluentServices.ZOOKEEPER
        self.group = self.service.value.get('group')

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

        response = self.get_service_user_group(input_context, service, hosts)
        self.update_inventory(self.inventory, response)

    def __build_service_properties(self, service_properties):

        for key, value in vars(class_name).items():
            if callable(getattr(class_name, key)) and key.startswith("_build"):
                func = getattr(class_name, key)
                logger.info(f"Calling Zookeeper property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, host_service_properties: dict, mapped_properties: set):

        custom_group = "zookeeper_custom_properties"
        skip_properties = set(FileUtils.get_zookeeper_configs("skip_properties"))

        # Get host server properties dictionary
        _host_service_properties = dict()
        for host in host_service_properties.keys():
            _host_service_properties[host] = host_service_properties.get(host).get(DEFAULT_KEY)
        self.build_custom_properties(inventory=self.inventory, group=self.service.value.get('group'),
                                     custom_properties_group_name=custom_group,
                                     host_service_properties=_host_service_properties, skip_properties=skip_properties,
                                     mapped_properties=mapped_properties)

    def __build_runtime_properties(self, hosts: list):
        # Build Java runtime overrides
        data = (self.group, {
            'zookeeper_custom_java_args': self.get_jvm_arguments(self.input_context, self.service, hosts)
        })
        self.update_inventory(self.inventory, data)

    def __get_user_dict(self, service_prop: dict, key: str) -> dict:
        pass

    def _build_service_port_properties(self, service_prop: dict) -> tuple:
        key = "clientPort"
        self.mapped_service_properties.add(key)
        if service_prop.get(key) is not None:
            return self.group, {"zookeeper_client_port": int(service_prop.get(key))}
        return self.group, {}

    def _build_ssl_properties(self, service_properties: dict) -> tuple:

        property_dict = dict()
        property_list = ["secureClientPort", "ssl.keyStore.location", "ssl.keyStore.password",
                         "ssl.trustStore.location", "ssl.trustStore.password"]

        for property_key in property_list:
            self.mapped_service_properties.add(property_key)

        zookeeper_ssl_enabled = bool(service_properties.get('secureClientPort', False))

        if not zookeeper_ssl_enabled:
            return self.group, {}

        property_dict['ssl_enabled'] = True
        property_dict['zookeeper_keystore_path'] = service_properties.get('ssl.keyStore.location')
        property_dict['ssl_keystore_store_password'] = service_properties.get('ssl.keyStore.password')
        property_dict['zookeeper_truststore_path'] = service_properties.get('ssl.trustStore.location')
        property_dict['ssl_truststore_password'] = service_properties.get('ssl.trustStore.password')
        property_dict['ssl_provided_keystore_and_truststore'] = True
        property_dict['ssl_provided_keystore_and_truststore_remote_src'] = True
        property_dict['ssl_truststore_ca_cert_alias'] = ''

        keystore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                         keystorepass=property_dict['ssl_keystore_store_password'],
                                                         keystorepath=property_dict['zookeeper_keystore_path'],
                                                         hosts=self.hosts)
        truststore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                           keystorepass=property_dict['ssl_truststore_password'],
                                                           keystorepath=property_dict['zookeeper_truststore_path'],
                                                           hosts=self.hosts)
        if keystore_aliases:
            # Set the first alias name
            property_dict["ssl_keystore_alias"] = keystore_aliases[0]
        if truststore_aliases:
            property_dict["ssl_truststore_ca_cert_alias"] = truststore_aliases[0]

        return "zookeeper", property_dict

    def _build_mtls_properties(self, service_properties: dict) -> tuple:
        zookeeper_client_authentication_type = service_properties.get('ssl.clientAuth')
        if zookeeper_client_authentication_type == 'need':
            return "zookeeper", {'ssl_mutual_auth_enabled': True}

        return self.group, {}

    def _build_jmx_properties(self, service_properties: dict) -> tuple:
        monitoring_details = self.get_monitoring_details(self.input_context, self.service, self.hosts, 'KAFKA_OPTS')
        service_monitoring_details = dict()
        group_name = self.service.value.get("group")

        for key, value in monitoring_details.items():
            service_monitoring_details[f"{group_name}_{key}"] = value

        return group_name, service_monitoring_details

    def _build_log4j_properties(self, service_properties: dict) -> tuple:
        log4j_file = self.get_log_file_path(self.input_context, self.service, self.hosts, "KAFKA_LOG4J_OPTS")
        default_log4j_file = "/etc/kafka/zookeeper-log4j.properties"
        root_logger, file = self.get_root_logger(self.input_context, self.hosts, log4j_file, default_log4j_file)

        if root_logger is None or file is None:
            return self.group, {'zookeeper_custom_log4j': False}

        return self.group, {
            'log4j_file': file,
            'zookeeper_log4j_root_logger': root_logger
        }

    def _build_kerberos_properties(self, service_prop: dict) -> tuple:
        jaas_file = self.get_jaas_file_path(self.input_context, self.service, self.hosts)
        if jaas_file is None:
            jaas_file = 'etc/kafka/zookeeper_jaas.conf'

        principal, keytab_path = self.get_kerberos_properties(self.input_context, self.hosts, jaas_file)
        if principal == "" and keytab_path == "":
            return 'all', {}
        return self.group, {
            'sasl_protocol': 'kerberos',
            'zookeeper_kerberos_principal': principal,
            'zookeeper_kerberos_keytab_path': keytab_path
        }


class ZookeeperServicePropertyBaseBuilder60(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBaseBuilder61(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBaseBuilder62(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBaseBuilder70(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBaseBuilder71(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBaseBuilder72(ZookeeperServicePropertyBaseBuilder):
    pass
