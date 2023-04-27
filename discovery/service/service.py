import abc
import re
import string
from abc import ABC

from discovery.manager.manager import ServicePropertyManager
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.services import ConfluentServices, ServiceData
from discovery.utils.utils import InputContext, Logger, load_properties_to_dict, MultiOrderedDict

logger = Logger.get_logger()


class AbstractPropertyBuilder(ABC):

    @abc.abstractmethod
    def build_properties(self):
        pass

    @staticmethod
    def get_keystore_alias_names(input_context: InputContext, hosts: list, keystorepass: str, keystorepath: str):
        return ServicePropertyManager.get_keystore_alias_names(input_context, hosts, keystorepass, keystorepath)

    @staticmethod
    def get_kerberos_properties(input_context: InputContext, hosts: list, jaas_file):
        return ServicePropertyManager.get_kerberos_properties(input_context, hosts, jaas_file)

    @staticmethod
    def get_kerberos_configurations(input_context: InputContext, hosts: list, kerberos_config_file):
        return ServicePropertyManager.get_kerberos_configurations(input_context, hosts, kerberos_config_file)

    @staticmethod
    def get_root_logger(input_context: InputContext, hosts: list, log4j_file, default_log4j_file):
        return ServicePropertyManager.get_root_logger(input_context, hosts, log4j_file, default_log4j_file)

    @staticmethod
    def get_log_file_path(input_context: InputContext, service: ServiceData, hosts: list, log4j_opts_env_var):
        return ServicePropertyManager.get_log_file_path(input_context, service, hosts, log4j_opts_env_var)

    @staticmethod
    def get_jaas_file_path(input_context: InputContext, service: ServiceData, hosts: list):
        return ServicePropertyManager.get_jaas_file_path(input_context, service, hosts)

    @staticmethod
    def get_property_mappings(input_context: InputContext, service: ServiceData, hosts: list):
        if not hosts:
            return dict()
        return ServicePropertyManager.get_property_mappings(input_context, service, hosts)

    @staticmethod
    def get_service_host(service: ServiceData, inventory: CPInventoryManager):
        group_name = service.group
        hosts = inventory.get_groups_dict().get(group_name)

        if group_name not in inventory.get_groups_dict() or not hosts:
            logger.debug(f"Either the service {group_name} doesn't exist in inventory or has no associated host")

        if not isinstance(hosts, list):
            logger.debug(f"Unrecognized hosts format: {hosts}")
            return None

        return hosts

    @staticmethod
    def get_rocksdb_path(input_context: InputContext, service: ServiceData, hosts: list):
        env_details = AbstractPropertyBuilder.get_service_environment_variable(input_context=input_context,
                                                                               service=service, hosts=hosts)
        return env_details.get("ROCKSDB_SHAREDLIB_DIR", "")

    @staticmethod
    def get_jvm_arguments(input_context: InputContext, service: ServiceData, hosts: list):
        # Build Java runtime overrides
        env_details = AbstractPropertyBuilder.get_service_environment_variable(input_context=input_context,
                                                                               service=service, hosts=hosts)
        heap_ops = env_details.get('KAFKA_HEAP_OPTS', '')
        kafka_ops = env_details.get('KAFKA_OPTS', '')
        # Remove java agent configurations. These will be populated by other configs.
        kafka_ops = re.sub('-javaagent.*?( |$)', '', kafka_ops).strip()

        jvm_str = ""
        if heap_ops:
            jvm_str = f"{jvm_str} {heap_ops}"

        if kafka_ops:
            jvm_str = f"{jvm_str} {kafka_ops}"

        return jvm_str

    @staticmethod
    def build_telemetry_properties(service_prop: dict) -> dict:
        property_dict = dict()
        key = 'confluent.telemetry.enabled'
        if service_prop.get(key) is not None and service_prop.get(key) == 'true':
            property_dict['telemetry_enabled'] = True
            property_dict['telemetry_api_key'] = service_prop.get('confluent.telemetry.api.key')
            property_dict['telemetry_api_secret'] = service_prop.get('confluent.telemetry.api.secret')
            if service_prop.get('confluent.telemetry.proxy.url') is not None:
                property_dict['telemetry_proxy_url'] = service_prop.get('confluent.telemetry.proxy.url')
                property_dict['telemetry_proxy_username'] = service_prop.get('confluent.telemetry.proxy.username')
                property_dict['telemetry_proxy_password'] = service_prop.get('confluent.telemetry.proxy.password')
        return property_dict

    @staticmethod
    def get_service_facts(input_context: InputContext, service: ServiceData, hosts: list) -> dict:
        # Get the service details
        from discovery.system.system import SystemPropertyManager
        response = SystemPropertyManager.get_service_details(input_context, service, [hosts[0]])

        # Don't fail for empty response continue with other properties
        if not response:
            logger.error(f"Could not get service details for {service}")
            return dict()

        return response.get(hosts[0]).get("status")

    @staticmethod
    def _get_systemd_env_details(file_content) -> dict:
        import configparser
        env_dict = dict()
        if not file_content:
            return env_dict

        configParser = configparser.RawConfigParser(dict_type=MultiOrderedDict, strict=False)
        configParser.read_string(file_content)
        try:
            env_details = configParser.get(section='Service', option='Environment')
            for line in env_details.splitlines():
                key, value = line.split('=', maxsplit=1)
                env_dict[key.strip('"')] = value.strip('"')
        except Exception:
            pass
        return env_dict

    @staticmethod
    def get_service_environment_variable(input_context: InputContext, service: ServiceData, hosts: list) -> dict:
        # Large values in service environment are getting truncated. As an alternate method, we will get
        # it from service and override variables
        env_map = dict()

        service_facts = AbstractPropertyBuilder.get_service_facts(input_context, service, hosts)
        service_file = service_facts.get('FragmentPath')
        override_file = service_facts.get('DropInPaths')

        content = ServicePropertyManager.slurp_remote_file(input_context=input_context, hosts=hosts, file=service_file)
        env_map.update(AbstractPropertyBuilder._get_systemd_env_details(content.get(hosts[0])))

        content = ServicePropertyManager.slurp_remote_file(input_context=input_context, hosts=hosts, file=override_file)
        env_map.update(AbstractPropertyBuilder._get_systemd_env_details(content.get(hosts[0])))
        return env_map

    @staticmethod
    def get_service_user_group(input_context: InputContext, service: ServiceData, hosts: list) -> tuple:
        service_facts = AbstractPropertyBuilder.get_service_facts(input_context, service, hosts)

        user = service_facts.get("User", None)
        group = service_facts.get("Group", None)
        env_details = AbstractPropertyBuilder.get_service_environment_variable(input_context, service, hosts)

        # Useful information for future usages
        # service_file = service_facts.get("FragmentPath", None)
        # service_override = service_facts.get("DropInPaths", None)
        # description = service_facts.get("Description", None)

        service_group = service.group
        return service_group, {
            f"{service_group}_user": str(user),
            f"{service_group}_group": str(group),
            f"{service_group}_log_dir": str(env_details.get("LOG_DIR", ''))
        }

    @staticmethod
    def update_inventory(inventory: CPInventoryManager, data: tuple):

        # Check for the data
        if not data or type(data) is not tuple:
            logger.error("The properties to add in inventory is either null or not type of a tuple")
            return

        group_name = data[0]
        mapped_properties = data[1]

        for key, value in mapped_properties.items():
            # Sanitise key value to ASCII values
            if isinstance(value, str):
                value = ''.join(filter(lambda x: x in string.printable, value))

            inventory.set_variable(group_name, key, value)

    @staticmethod
    def build_custom_properties(inventory: CPInventoryManager, group: str, custom_properties_group_name: str,
                                host_service_properties: dict, skip_properties: set, mapped_properties: set):

        host_custom_properties = dict()
        for host in host_service_properties:
            temp = dict()
            for key, value in host_service_properties[host].items():
                if key not in mapped_properties and key not in skip_properties:
                    temp[key] = value
            host_custom_properties[host] = temp

        # Get common custom properties for all hosts
        common_custom_properties = dict()
        common_keys = host_custom_properties.get(next(iter(host_custom_properties)), dict()).keys()
        for host in host_custom_properties.keys():
            common_keys & host_custom_properties.get(host).keys()

        # Populate the common custom properties for group
        for key in common_keys:
            # check if values are same for all hosts
            temp = set()
            for host in host_custom_properties.keys():
                temp.add(host_custom_properties.get(host).get(key))
            if len(temp) == 1:
                common_custom_properties[key] = temp.pop()

        # Set the common custom properties
        inventory.set_variable(group, custom_properties_group_name, common_custom_properties)

        # Get the host specific properties
        for host, properties in host_custom_properties.items():
            for key, value in properties.items():
                if key not in common_custom_properties.keys():
                    _host = inventory.get_host(host)
                    _host.set_variable(key, value)

    @staticmethod
    def get_values_from_jaas_config(jaas_config: str) -> dict:
        user_dict = dict()
        for token in jaas_config.split():
            if "=" in token:
                key, value = token.split('=')
                user_dict[key] = value
        return user_dict

    @staticmethod
    def _get_jolokia_props(env_str: str, service: ServiceData) -> dict:
        monitoring_props = dict()
        if 'jolokia.jar' not in env_str:
            return monitoring_props

        monitoring_props['jolokia_enabled'] = True

        # Parse the jolokia jar location
        pattern = 'javaagent:(\S+jolokia.jar)'
        match = re.search(pattern, env_str)
        if match:
            monitoring_props['jolokia_jar_path'] = match.group(1)

        # Parse the jolokia properties
        pattern = 'javaagent:\S+jolokia.jar\S+config=(\S+)'
        match = re.search(pattern, env_str)
        if match:
            jolokia_file_path = match.group(1)
            monitoring_props[f"{service.group}_jolokia_config"] = jolokia_file_path
            jolokia_props = load_properties_to_dict(jolokia_file_path)
            if "port" in jolokia_props:
                monitoring_props[f"{service.group}_jolokia_port"] = jolokia_props.get("port")

        return monitoring_props

    @staticmethod
    def _get_prometheus_props(env_str: str, service: ServiceData) -> dict:
        monitoring_props = dict()
        if 'jmx_prometheus_javaagent.jar' not in env_str:
            return monitoring_props

        monitoring_props['jmxexporter_enabled'] = True

        # Parse the jar location. Ansible supports a single path for all components
        pattern = 'javaagent:(\S+prometheus\S+.jar)'
        match = re.search(pattern, env_str)
        if match:
            monitoring_props['jmxexporter_jar_path'] = match.group(1)

        # Parse the port number
        pattern = "\S+prometheus\S+.jar=([0-9]+):"
        match = re.search(pattern, env_str)
        if match:
            monitoring_props[f'{service.group}_jmxexporter_port'] = int(match.group(1))

        # Parse the properties file
        pattern = '\S+prometheus\S+.jar=[0-9]+:(\S+)'
        match = re.search(pattern, env_str)
        if match:
            jmx_file_path = match.group(1)
            monitoring_props[f'{service.group}_jmxexporter_config_path'] = jmx_file_path

        return monitoring_props

    @staticmethod
    def get_monitoring_details(input_context: InputContext, service: ServiceData, hosts: list, key: str) -> dict:
        monitoring_props = dict()
        env_details = AbstractPropertyBuilder.get_service_environment_variable(input_context=input_context,
                                                                               service=service, hosts=hosts)
        env_str = env_details.get(key, '')

        monitoring_props.update(AbstractPropertyBuilder._get_jolokia_props(env_str, service))
        monitoring_props.update(AbstractPropertyBuilder._get_prometheus_props(env_str, service))

        return monitoring_props

    @staticmethod
    def get_secret_protection_master_key(input_context: InputContext, service: ServiceData, hosts: list):
        env_dict = AbstractPropertyBuilder.get_service_environment_variable(input_context=input_context,
                                                                            service=service, hosts=hosts)
        return env_dict.get('CONFLUENT_SECURITY_MASTER_KEY', None)

    @staticmethod
    def get_audit_log_properties(input_context: InputContext, hosts: str, mds_user: str, mds_password: str) -> tuple:
        return ServicePropertyManager.get_audit_log_properties(input_context=input_context,
                                                               hosts=hosts,
                                                               mds_user=mds_user,
                                                               mds_password=mds_password)


class ServicePropertyBuilder:
    inventory = None
    input_context = None
    confluent_services = None

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.confluent_services = ConfluentServices(input_context)

    def with_zookeeper_properties(self):
        if self.confluent_services.ZOOKEEPER().group in self.inventory.groups.keys():
            from discovery.service.zookeeper import ZookeeperServicePropertyBuilder
            ZookeeperServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_kafka_broker_properties(self):
        if self.confluent_services.KAFKA_BROKER().group in self.inventory.groups.keys():
            from discovery.service.kafka_broker import KafkaServicePropertyBuilder
            KafkaServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_schema_registry_properties(self):
        if self.confluent_services.SCHEMA_REGISTRY().group in self.inventory.groups.keys():
            from discovery.service.schema_registry import SchemaRegistryServicePropertyBuilder
            SchemaRegistryServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_kafka_rest_properties(self):
        if self.confluent_services.KAFKA_REST().group in self.inventory.groups.keys():
            from discovery.service.kafka_rest import KafkaRestServicePropertyBuilder
            KafkaRestServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_ksql_properties(self):
        if self.confluent_services.KSQL().group in self.inventory.groups.keys():
            from discovery.service.ksql import KsqlServicePropertyBuilder
            KsqlServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_control_center_properties(self):
        if self.confluent_services.CONTROL_CENTER().group in self.inventory.groups.keys():
            from discovery.service.control_center import ControlCenterServicePropertyBuilder
            ControlCenterServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_kafka_connect_properties(self):
        if self.confluent_services.KAFKA_CONNECT().group in self.inventory.groups.keys():
            from discovery.service.kafka_connect import KafkaConnectServicePropertyBuilder
            KafkaConnectServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_kafka_connect_replicator_properties(self):
        if self.confluent_services.KAFKA_REPLICATOR().group in self.inventory.groups.keys():
            from discovery.service.kafka_replicator import KafkaReplicatorServicePropertyBuilder
            KafkaReplicatorServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self
