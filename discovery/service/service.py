import abc
import base64
import json
import re
from abc import ABC

from discovery.system.system import SystemPropertyManager
from discovery.utils.constants import ConfluentServices
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

        return hosts

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

        match = re.search('[\w\/-]*\.properties', execution_command)
        if match:
            return match.group(0)
        else:
            logger.error(f"Cannot find associated properties file for service {service.value.get('name')}")

    @staticmethod
    def get_property_mappings(input_context: InputContext, service: ConfluentServices, hosts: list) -> dict:

        file = AbstractPropertyBuilder.__get_service_properties_file(input_context, service, hosts)
        if not file:
            logger.error(f"Could not get the service seed property file.")
            return dict()

        play = dict(
            name="Ansible Play",
            hosts=hosts,
            gather_facts='no',
            tasks=[
                dict(action=dict(module='slurp', args=dict(src=file)))
            ]
        )
        response = PythonAPIUtils.execute_play(input_context, play)
        mappings = dict()

        for host in hosts:
            properties = base64.b64decode(response[host]._result['content']).decode('utf-8')
            mappings[host] = load_properties_to_dict(properties)
            logger.debug(json.dumps(mappings, indent=4))
        return mappings

    @staticmethod
    def parse_environment_details(env_command: str) -> dict:
        env_details = dict()
        for token in env_command.split():
            # special condition for java runtime arguments
            if not '=' in token and token.startswith('-X'):
                env_details['KAFKA_HEAP_OPTS'] = f"{env_details.get('KAFKA_HEAP_OPTS', '')} {token}"
            else:
                key, value = token.split('=', 1)
                env_details[key] = value

        return env_details

    @staticmethod
    def get_service_details(input_context: InputContext, service: ConfluentServices, hosts: list) -> dict:
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
        service_facts = AbstractPropertyBuilder.get_service_details(input_context, service, hosts)

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
    def build_custom_properties(inventory: CPInventoryManager,
                                group: str,
                                service_properties: dict,
                                skip_properties: set,
                                mapped_properties:set):

        custom_properties = dict()

        inventory.set_variable('all', group, service_properties)
        for key, value in service_properties.items():
            if key not in mapped_properties and key not in skip_properties:
                custom_properties[key] = value

        inventory.set_variable('all', group, custom_properties)


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
        return self

