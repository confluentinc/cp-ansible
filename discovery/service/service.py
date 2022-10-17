import abc
import base64
import re
from abc import ABC
import string
import json

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
    def get_rocksdb_path(input_context: InputContext, service: ConfluentServices, hosts: list):
        env_details = AbstractPropertyBuilder._get_env_details(input_context, service, hosts)
        return env_details.get("ROCKSDB_SHAREDLIB_DIR", "")

    @staticmethod
    def get_jvm_arguments(input_context: InputContext, service: ConfluentServices, hosts: list):
        # Build Java runtime overrides
        env_details = AbstractPropertyBuilder._get_env_details(input_context, service, hosts)
        heap_ops = env_details.get('KAFKA_HEAP_OPTS', '')
        kafka_ops= env_details.get('KAFKA_OPTS', '')
        # Remove java agent configurations. These will be populated by other configs.
        kafka_ops = re.sub('-javaagent.*?( |$)', '', kafka_ops).strip()

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
    def get_log_file_path(input_context: InputContext, service: ConfluentServices, hosts: list, log4j_opts_env_var):
        # check if overriden as env var
        env_details = AbstractPropertyBuilder._get_env_details(input_context, service, hosts)
        log4j_opts = env_details.get(log4j_opts_env_var, None)
        if log4j_opts is not None:
            if "-Dlog4j.configuration=file:" in log4j_opts:
                log4j_path = log4j_opts.split("-Dlog4j.configuration=file:",1)[1].split(" ",1)[0]
                return log4j_path

        # if not overridden, read from java process details
        play = dict(
            name="Get java process details for cp component",
            hosts=hosts,
            gather_facts='no',
            tasks=[
                dict(action=dict(module='shell',
                                 args=f"ps aux | grep java | grep log4j"))
            ]
        )
        response = PythonAPIUtils.execute_play(input_context, play)
        if len(response)==0:
            return None
        if response[hosts[0]]._result['rc'] == 0:
            process_details = response[hosts[0]]._result['stdout']
            if "-Dlog4j.configuration=file:" in process_details:
                log4j_path = process_details.split("-Dlog4j.configuration=file:",1)[1].split(" ",1)[0]
                return log4j_path

        return None

    @staticmethod
    def get_root_logger(input_context: InputContext, service: ConfluentServices, hosts: list, log4j_file, default_log4j_file):
        for file in [log4j_file, default_log4j_file]:
            if file is None:
                continue
            play = dict(
                name="Get root logger definition from log4j file",
                hosts=hosts,
                gather_facts='no',
                tasks=[
                    dict(action=dict(module='shell',
                                    args=f"grep ^log4j.rootLogger {file}"))
                ]
            )
            response = PythonAPIUtils.execute_play(input_context, play)
            if len(response)==0:
                continue
            if response[hosts[0]]._result['rc'] == 0:
                logger_def = response[hosts[0]]._result['stdout']
                return logger_def.split("log4j.rootLogger=",1)[1].strip(), file

        return None, None

    @staticmethod
    def get_audit_log_properties(input_context: InputContext, hosts: string, mds_user: str, mds_password: str) -> str:
        # returns list of all clusters in the registry
        play1 = dict(
            name="Get list of clusters",
            hosts=hosts,
            gather_facts='no',
            tasks=[
                dict(action=dict(module='shell',
                                 args=f"curl -ku '{mds_user}:{mds_password}' "
                                      f"https://localhost:8090/security/1.0/registry/clusters"))
            ]
        )

        response = PythonAPIUtils.execute_play(input_context, play1)
        if len(response)==0:
            return "", ""
        cluster_list = ""
        if response[hosts]._result['rc'] == 0:
            cluster_list = response[hosts]._result['stdout']
        if cluster_list == "":
            return "", ""
        try:
            res = json.loads(cluster_list)
        except:
            res = ""

        for cluster in res:
            cluster_name = cluster['clusterName']
            payload = f'{{"clusterName":"{cluster_name}"}}'
            # Look up the Principals who have the given role ResourceOwner on the specified resource (Topic:confluent-audit-log-events) for the given cluster.
            play2 = dict(
                name="Check rolebinding to get principal name",
                hosts=hosts,
                gather_facts='no',
                tasks=[
                    dict(action=dict(module='shell',
                                    args=f"curl -ku '{mds_user}:{mds_password}' "
                                        f"https://localhost:8090/security/1.0/lookup/role/ResourceOwner/resource/Topic/name/confluent-audit-log-events "
                                        f"-H 'Content-Type: application/json' "
                                        f"-d '{payload}'"))
                ]
            )
            response2 = PythonAPIUtils.execute_play(input_context, play2)
            if len(response2)==0:
                continue
            if response2[hosts]._result['rc'] == 0:
                stdout = response2[hosts]._result['stdout']
                try:
                    role = json.loads(stdout)
                except:
                    role = []
                if len(role) == 0:
                    continue
                principal_name = role[0].split(";")[0].split("User:")[1]
                # If a principal exists for this cluster, this is the destination kafka cluster for audit logs
                return cluster, principal_name

        return "", ""

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
    def parse_environment_details(env_command: str) -> dict:
        env_details = dict()
        tokens = ['KAFKA_HEAP_OPTS', 'KAFKA_OPTS', 'KAFKA_LOG4J_OPTS', 'LOG_DIR']
        for token in tokens:
            pattern = f"{token}=(.*?) ([A-Z]{{3}}|$)"
            match = re.search(pattern, env_command)
            if match:
                env_details[token] = match.group(1).rstrip()
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
        return service_group, {
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


    @staticmethod
    def get_monitoring_details(input_context, service, hosts, key)->dict:
        monitoring_props = dict()
        env_details = AbstractPropertyBuilder._get_env_details(input_context, service, hosts)
        ops_str= env_details.get(key, '')

        if 'jolokia.jar' in ops_str:
            monitoring_props['jolokia_enabled'] = True
            # jolokia properies will be managed by cp-ansible plays

        if 'jmx_prometheus_javaagent.jar' in ops_str:
            monitoring_props['jmxexporter_enabled'] = True
            pattern = f"jmx_prometheus_javaagent.jar=([0-9]+):"
            match = re.search(pattern, ops_str)
            if match:
                monitoring_props['jmxexporter_port'] = int(match.group(1))

        return monitoring_props

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
