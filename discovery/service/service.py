import abc
import base64
import re
from abc import ABC

from discovery.system.system import SystemPropertyManager
from discovery.utils.constants import ConfluentServices, DEFAULT_KEY
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, PythonAPIUtils, load_properties_to_dict, Logger

logger = Logger.get_logger()


class AbstractPropertyBuilder(ABC):

    @abc.abstractmethod
    def build_properties(self):
        pass

    def get_service_host(self, service: ConfluentServices, inventory: CPInventoryManager):
        group_name = service.value.get("group")
        hosts = inventory.get_groups_dict().get(group_name)

        if group_name not in inventory.get_groups_dict() or not hosts:
            logger.debug(f"Either the service {group_name} doesn't exist in inventory or has no associated host")

        if not isinstance(hosts, list):
            logger.debug(f"Unrecognized hosts format: {hosts}")
            return None

        return hosts

    @staticmethod
    def get_secret_protection_key(input_context: InputContext, service: ConfluentServices, hosts: list):
        env_details = AbstractPropertyBuilder._get_env_details(input_context, service, hosts)
        return env_details.get("CONFLUENT_SECURITY_MASTER_KEY", None)

    @staticmethod
    def get_jvm_arguments(input_context: InputContext, service: ConfluentServices, hosts: list):
        # Build Java runtime overrides
        env_details = AbstractPropertyBuilder._get_env_details(input_context, service, hosts)
        heap_ops = env_details.get('KAFKA_HEAP_OPTS', None)
        kafka_ops= env_details.get('KAFKA_OPTS', None)
        jvm_str = ""
        if heap_ops:
            jvm_str = f"{jvm_str} {heap_ops}"

        if kafka_ops:
            jvm_str = f"{jvm_str} {kafka_ops}"

        return jvm_str

    @staticmethod
    def _get_env_details(input_context: InputContext, service: ConfluentServices, hosts: list):
        service_facts = AbstractPropertyBuilder.get_service_facts(input_context, service, hosts)
        environment = service_facts.get("Environment", None)
        return AbstractPropertyBuilder.parse_environment_details(environment)

    @staticmethod
    def __get_service_properties_file(input_context: InputContext,
                                      service: ConfluentServices,
                                      hosts: list):
        if not hosts:
            logger.error(f"Host list is empty for service {service.value.get('name')}")
            return None

        host = hosts[0]
        service_details = SystemPropertyManager.get_service_details(input_context, service, host)
        execution_command = service_details.get(host).get("status").get("ExecStart")

        # check if we have flag based configs
        property_files = dict()
        matches = re.findall('(--[\w\.]+\.config)*\s+([\w\/-]+\.properties)', execution_command)
        for match in matches:
            key, path = match
            key = key.strip('--') if key else DEFAULT_KEY
            property_files[key] = path

        if not property_files:
            logger.error(f"Cannot find associated properties file for service {service.value.get('name')}")
        return property_files

    @staticmethod
    def get_property_mappings(input_context: InputContext, service: ConfluentServices, hosts: list) -> dict:

        mappings = dict()
        property_file_dict = AbstractPropertyBuilder.__get_service_properties_file(input_context, service, hosts)
        if not property_file_dict:
            logger.error(f"Could not get the service seed property file.")
            return mappings

        for key, file in property_file_dict.items():
            play = dict(
                name="Slurp properties file",
                hosts=hosts,
                gather_facts='no',
                tasks=[
                    dict(action=dict(module='slurp', args=dict(src=file)))
                ]
            )
            response = PythonAPIUtils.execute_play(input_context, play)
            for host in hosts:
                properties = base64.b64decode(response[host]._result['content']).decode('utf-8')
                host_properites = mappings.get(host, dict())
                host_properites.update({key: load_properties_to_dict(properties)})
                mappings[host] = host_properites

        return mappings

    @staticmethod
    def get_keystore_alias_names(input_context: InputContext, hosts: list, keystorepass: str, keystorepath: str) -> str:

        if not keystorepath or not keystorepass:
            return []

        play = dict(
            name="Get keystore alias name",
            hosts=hosts,
            gather_facts='no',
            tasks=[
                dict(action=dict(module='shell',
                                 args=f"keytool -list -v -storepass {keystorepass} -keystore "
                                      f"{keystorepath} | grep 'Alias name' "
                                      "| awk '{print $3}'"))
            ]
        )

        response = PythonAPIUtils.execute_play(input_context, play)
        if response[hosts[0]]._result['rc'] == 0:
            stdout = response[hosts[0]]._result['stdout']
            aliases = [y for y in (x.strip() for x in stdout.splitlines()) if y]
            return aliases
        else:
            return []

    @staticmethod
    def parse_environment_details(env_command: str) -> dict:
        env_details = dict()
        for token in env_command.split():
            # special condition for java runtime arguments
            if token == '[unprintable]':
                continue
            if not '=' in token and token.startswith('-X'):
                env_details['KAFKA_HEAP_OPTS'] = f"{env_details.get('KAFKA_HEAP_OPTS', '')} {token}"
            else:
                key, value = token.split('=', 1)
                env_details[key] = value

        return env_details

    @staticmethod
    def get_service_facts(input_context: InputContext, service: ConfluentServices, hosts: list) -> dict:
        # Get the service details
        from discovery.system.system import SystemPropertyManager
        response = SystemPropertyManager.get_service_details(input_context, service, [hosts[0]])

        # Don't fail for empty response continue with other properties
        if not response:
            logger.error(f"Could not get service details for {service}")
            return dict()

        return response.get(hosts[0]).get("status")

    @staticmethod
    def get_service_user_group(input_context: InputContext, service: ConfluentServices, hosts: list) -> tuple:
        service_facts = AbstractPropertyBuilder.get_service_facts(input_context, service, hosts)

        user = service_facts.get("User", None)
        group = service_facts.get("Group", None)
        environment = service_facts.get("Environment", None)
        env_details = AbstractPropertyBuilder.parse_environment_details(environment)

        # Useful information for future usages
        service_file = service_facts.get("FragmentPath", None)
        service_override = service_facts.get("DropInPaths", None)
        description = service_facts.get("Description", None)

        service_group = service.value.get("group")
        return 'all', {
            f"{service_group}_user": str(user),
            f"{service_group}_group": str(group),
            f"{service_group}_log_dir": str(env_details.get("LOG_DIR", None))
        }

    @staticmethod
    def update_inventory(inventory: CPInventoryManager, data: tuple):

        # Check for the data
        if not data or type(data) is not tuple:
            logger.error(f"The properties to add in inventory is either null or not type of a tuple")
            return

        group_name = data[0]
        mapped_properties = data[1]

        for key, value in mapped_properties.items():
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


class ServicePropertyBuilder:
    inventory = None
    input_context = None

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context

    def with_zookeeper_properties(self):
        from discovery.service.zookeeper import ZookeeperServicePropertyBuilder
        ZookeeperServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_kafka_broker_properties(self):
        from discovery.service.kafka_broker import KafkaServicePropertyBuilder
        KafkaServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_schema_registry_properties(self):
        from discovery.service.schema_registry import SchemaRegistryServicePropertyBuilder
        SchemaRegistryServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_kafka_rest_properties(self):
        from discovery.service.kafka_rest import KafkaRestServicePropertyBuilder
        KafkaRestServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_ksql_properties(self):
        from discovery.service.ksql import KsqlServicePropertyBuilder
        KsqlServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_control_center_properties(self):
        from discovery.service.control_center import ControlCenterServicePropertyBuilder
        ControlCenterServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_mds_properties(self):
        return self

    def with_connect_properties(self):
        from discovery.service.kafka_connect import KafkaConnectServicePropertyBuilder
        KafkaConnectServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self

    def with_replicator_properties(self):
        from discovery.service.kafka_replicator import KafkaReplicatorServicePropertyBuilder
        KafkaReplicatorServicePropertyBuilder.build_properties(self.input_context, self.inventory)
        return self
