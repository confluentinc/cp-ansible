import base64
import json
import re

import ansible_runner

from discovery.utils.constants import ConfluentServices, DEFAULT_KEY
from discovery.utils.utils import Logger, InputContext, load_properties_to_dict

logger = Logger.get_logger()


class AnsibleRunnerUtils:
    result_ok = None
    filter = None

    def __init__(self, filter=None):
        self.result_ok = dict()
        self.filter = filter

    def my_event_handler(self, event):
        # Do something here
        if event.get('event', None) == 'runner_on_ok':
            event_data = event.get('event_data')
            self.result_ok[event_data.get('host')] = event_data.get('res').get(
                self.filter) if self.filter else event_data.get('res')

    @staticmethod
    def get_ansible_vars_from_input_context(input_context: InputContext) -> dict:
        vars = dict()
        vars['ansible_user'] = input_context.ansible_user
        vars['ansible_become'] = input_context.ansible_become
        vars['ansible_connection'] = input_context.ansible_connection
        vars['ansible_become_user'] = input_context.ansible_become_user
        vars['ansible_become_method'] = input_context.ansible_become_method
        vars['ansible_ssh_extra_args'] = input_context.ansible_ssh_extra_args
        vars['ansible_python_interpreter'] = input_context.ansible_python_interpreter
        vars['ansible_ssh_private_key_file'] = input_context.ansible_ssh_private_key_file
        return vars

    @staticmethod
    def get_host_and_pattern_from_host_list(input_hosts: list) -> tuple:
        hosts = dict()
        host_pattern = ""
        for host in input_hosts:
            hosts[host] = None
            host_pattern = host + ',' + host_pattern

        return hosts, host_pattern

    @staticmethod
    def get_host_and_pattern_from_input_context(input_context: InputContext) -> tuple:
        return AnsibleRunnerUtils.get_host_and_pattern_from_host_list(input_context.ansible_hosts)

    @staticmethod
    def get_inventory_dict(input_context: InputContext, input_hosts: list = None):
        if input_hosts:
            hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(input_hosts)
        else:
            hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_input_context(input_context)
        return {
            'all':
                {
                    'vars': AnsibleRunnerUtils.get_ansible_vars_from_input_context(input_context),
                    'hosts': hosts
                }
        }


class SystemPropertyManager:

    @staticmethod
    def get_service_facts(input_context: InputContext) -> dict:
        runner_utils = AnsibleRunnerUtils('ansible_facts')
        hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_input_context(input_context)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context),
            module='service_facts',
            event_handler=runner_utils.my_event_handler
        )
        return runner_utils.result_ok

    @staticmethod
    def get_service_host_mapping(input_context: InputContext, **kwargs) -> dict:
        logger.info(f"Getting the service<->host mapping for {input_context.ansible_hosts}")
        service_mappings = SystemPropertyManager.get_service_facts(input_context)
        mapping = dict()

        for host, service_facts in service_mappings.items():
            services = service_facts.get("services")
            for cservice in ConfluentServices.get_all_service_names():

                if cservice in services:
                    logger.debug(
                        f"Host {host} has a confluent service {cservice} in {services[cservice].get('state')} state")

                    if services[cservice].get('status', None) == 'enabled' and \
                            services[cservice].get('state', None) == 'running':
                        service_key = ConfluentServices.get_service_key_value(cservice)
                        host_list = mapping.get(service_key, list())
                        host_list.append(host)
                        mapping[service_key] = list(host_list)

        if not mapping:
            logger.error("Could not get the service mappings. Please see the logs for details.")

        logger.info(f"Host service mappings:\n{json.dumps(mapping)}")
        return mapping

    @staticmethod
    def get_service_details(input_context: InputContext, service: ConfluentServices, hosts: list = None):

        runner_utils = AnsibleRunnerUtils()
        ansible_hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
            module='ansible.builtin.systemd',
            module_args=f"name={service.value.get('name')}",
            event_handler=runner_utils.my_event_handler
        )

        mappings = dict()
        for host, result in runner_utils.result_ok.items():
            mappings[host] = result

        logger.debug(json.dumps(mappings, indent=4))
        return mappings

    @staticmethod
    def get_ansible_facts(input_context: InputContext, hosts: list = None):

        runner_utils = AnsibleRunnerUtils('ansible_facts')
        hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_input_context(input_context)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context),
            module='ansible_facts',
            event_handler=runner_utils.my_event_handler
        )

        mappings = dict()
        for host, result in runner_utils.result_ok.items():
            mappings[host] = result._result

        logger.debug(json.dumps(mappings, indent=4))
        return mappings

    @staticmethod
    def get_package_facts(input_context: InputContext, hosts: list = None):
        runner_utils = AnsibleRunnerUtils('ansible_facts')
        hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_input_context(input_context)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context),
            module='package_facts',
            event_handler=runner_utils.my_event_handler
        )

        mappings = dict()
        for host, result in runner_utils.result_ok.items():
            confluent_packages = dict()
            for package, details in result.get("packages").items():
                if package.startswith("confluent"):
                    confluent_packages[package] = details
            mappings[host] = confluent_packages

        logger.debug(json.dumps(mappings, indent=4))
        return mappings

    @staticmethod
    def get_java_facts(input_context: InputContext, hosts: list = None):
        runner_utils = AnsibleRunnerUtils('ansible_facts')
        hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_input_context(input_context)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context),
            module="shell",
            module_args="cmd='dirname $(dirname $(readlink -f $(which java)))'",
            event_handler=runner_utils.my_event_handler
        )

        mappings = dict()
        for host, result in runner_utils.result_ok.items():
            if result._result.get('rc') == 0:
                mappings[host] = result._result.get('stdout')
            else:
                logger.error(f"Could not get java home for host {host}. Got error {result._result.get('msg')}")

        logger.debug(json.dumps(mappings, indent=4))
        return mappings


class ServicePropertyManager:

    @staticmethod
    def __get_service_properties_file(input_context: InputContext, service: ConfluentServices, hosts: list):
        if not hosts:
            logger.error(f"Host list is empty for service {service.value.get('name')}")
            return None

        host = hosts[0]
        service_details = SystemPropertyManager.get_service_details(input_context, service, [host])
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
        seed_properties_file = ServicePropertyManager.__get_service_properties_file(input_context, service, hosts)
        if not seed_properties_file:
            logger.error("Could not get the service seed property file.")
            return mappings

        for key, file in seed_properties_file.items():

            runner_utils = AnsibleRunnerUtils()
            hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
            ansible_runner.run(
                host_pattern=host_pattern,
                inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
                module="slurp",
                module_args=f"src={file}",
                event_handler=runner_utils.my_event_handler
            )

            response = runner_utils.result_ok
            for host in hosts:
                properties = base64.b64decode(response[host]['content']).decode('utf-8')
                host_properties = mappings.get(host, dict())
                host_properties.update({key: load_properties_to_dict(properties)})
                mappings[host] = host_properties

        return mappings

    @staticmethod
    def get_keystore_alias_names(input_context: InputContext, hosts: list, keystorepass: str,
                                 keystorepath: str) -> list:

        if not keystorepath or not keystorepass:
            return []

        runner_utils = AnsibleRunnerUtils()
        ansilble_hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
            module="shell",
            module_args=f"keytool -list -v -storepass {keystorepass} -keystore "
                        f"{keystorepath} | grep -m1 'Alias name' "
                        "| awk '{print $3}'",
            event_handler=runner_utils.my_event_handler
        )

        response = runner_utils.result_ok
        if len(response) != 0 and response[list(hosts)[0]]['rc'] == 0:
            stdout = response[list(hosts)[0]]['stdout']
            aliases = [y for y in (x.strip() for x in stdout.splitlines()) if y]
            return aliases
        else:
            return []

    @staticmethod
    def get_jaas_file_path(input_context: InputContext, service: ConfluentServices, hosts: list):
        # check if overriden as env var
        env_details = ServicePropertyManager.get_env_details(input_context, service, hosts)
        kafka_opts = env_details.get('KAFKA_OPTS', None)
        if kafka_opts is not None:
            if "-Djava.security.auth.login.config=" in kafka_opts:
                jaas_file_path = kafka_opts.split('-Djava.security.auth.login.config=')[1].split(' ')[0]
                return jaas_file_path
        return None

    @staticmethod
    def get_log_file_path(input_context: InputContext, service: ConfluentServices, hosts: list, log4j_opts_env_var):
        # check if overriden as env var
        env_details = ServicePropertyManager.get_env_details(input_context, service, hosts)
        log4j_opts = env_details.get(log4j_opts_env_var, None)
        if log4j_opts is not None:
            if "-Dlog4j.configuration=file:" in log4j_opts:
                log4j_path = log4j_opts.split("-Dlog4j.configuration=file:", 1)[1].split(" ", 1)[0]
                return log4j_path

        runner_utils = AnsibleRunnerUtils()
        ansible_hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
            module="shell",
            module_args="ps aux | grep java | grep log4j",
            event_handler=runner_utils.my_event_handler
        )

        response = runner_utils.result_ok
        if len(response) == 0:
            return None
        if response[hosts[0]]['rc'] == 0:
            process_details = response[hosts[0]]['stdout']
            if "-Dlog4j.configuration=file:" in process_details:
                log4j_path = process_details.split("-Dlog4j.configuration=file:", 1)[1].split(" ", 1)[0]
                return log4j_path

        return None

    @staticmethod
    def parse_environment_details(env_command: str) -> dict:
        env_details = dict()
        if not env_command:
            return env_details

        tokens = ['KAFKA_HEAP_OPTS', 'KAFKA_OPTS', 'KAFKA_LOG4J_OPTS', 'LOG_DIR']
        for token in tokens:
            pattern = f"{token}=(.*?) ([A-Z]{{3}}|$)"
            match = re.search(pattern, env_command)
            if match:
                env_details[token] = match.group(1).rstrip()
        return env_details

    @staticmethod
    def get_env_details(input_context: InputContext, service: ConfluentServices, hosts: list):
        service_facts = SystemPropertyManager.get_service_details(input_context, service, hosts)
        environment = service_facts.get("Environment", None)
        return ServicePropertyManager.parse_environment_details(environment)

    @staticmethod
    def get_kerberos_configurations(input_context: InputContext, hosts: list, kerberos_config_file):
        realm, kdc, admin = "", "", ""

        runner_utils = AnsibleRunnerUtils()
        ansible_hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
            module="shell",
            module_args=f"grep default_realm {kerberos_config_file}",
            event_handler=runner_utils.my_event_handler
        )
        response1 = runner_utils.result_ok
        if len(response1) != 0 and response1[hosts[0]]['rc'] == 0:
            std_out = response1[hosts[0]]['stdout']
            realm = std_out.split('default_realm')[1].strip().split('=')[1].strip()

        runner_utils = AnsibleRunnerUtils()
        ansible_hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
            module="shell",
            module_args=f"grep kdc {kerberos_config_file} | grep 88",
            event_handler=runner_utils.my_event_handler
        )
        response2 = runner_utils.result_ok
        if len(response2) != 0 and response2[hosts[0]]['rc'] == 0:
            std_out = response2[hosts[0]]['stdout']
            kdc = std_out.split('kdc')[1].strip().split('=')[1].strip().split(':88')[0]

        runner_utils = AnsibleRunnerUtils()
        ansible_hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
            module="shell",
            module_args=f"grep admin_server {kerberos_config_file}",
            event_handler=runner_utils.my_event_handler
        )
        response3 = runner_utils.result_ok
        if len(response3) != 0 and response3[hosts[0]]['rc'] == 0:
            std_out = response3[hosts[0]]['stdout']
            admin = std_out.split('admin_server')[1].strip().split('=')[1].strip().split(':749')[0]

        return realm, kdc, admin

    @staticmethod
    def get_kerberos_properties(input_context: InputContext, hosts: list, jaas_file):
        principal, keytab_path = "", ""

        runner_utils = AnsibleRunnerUtils()
        ansible_hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
            module="shell",
            module_args=f"grep keyTab= {jaas_file}",
            event_handler=runner_utils.my_event_handler
        )
        response1 = runner_utils.result_ok
        if len(response1) != 0 and response1[hosts[0]]['rc'] == 0:
            std_out = response1[hosts[0]]['stdout']
            if 'keyTab="' in std_out:
                keytab_path = std_out.split('keyTab="')[1].split('"')[0]

        runner_utils = AnsibleRunnerUtils()
        ansible_hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
            module="shell",
            module_args=f"grep principal= {jaas_file}",
            event_handler=runner_utils.my_event_handler
        )
        response2 = runner_utils.result_ok
        if len(response2) != 0 and response2[hosts[0]]['rc'] == 0:
            std_out = response2[hosts[0]]['stdout']
            if 'principal="' in std_out:
                principal = std_out.split('principal="')[1].split('"')[0]

        return principal, keytab_path

    @staticmethod
    def get_root_logger(input_context: InputContext, hosts: list, log4j_file, default_log4j_file):

        for file in [log4j_file, default_log4j_file]:
            if file is None:
                continue

            runner_utils = AnsibleRunnerUtils()
            ansible_hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
            ansible_runner.run(
                host_pattern=host_pattern,
                inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
                module="shell",
                module_args=f"grep ^log4j.rootLogger {file}",
                event_handler=runner_utils.my_event_handler
            )

            response = runner_utils.result_ok

            if len(response) == 0:
                continue
            if response[hosts[0]]['rc'] == 0:
                logger_def = response[hosts[0]]['stdout']
                return logger_def.split("log4j.rootLogger=", 1)[1].strip(), file

        return None, None

    @staticmethod
    def get_audit_log_properties(input_context: InputContext, hosts: str, mds_user: str, mds_password: str) -> tuple:

        # returns list of all clusters in the registry
        hosts = hosts.split(',')
        runner_utils = AnsibleRunnerUtils()
        ansible_hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
        ansible_runner.run(
            host_pattern=host_pattern,
            inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
            module="shell",
            module_args=f"curl -ku '{mds_user}:{mds_password}' "
                        f"https://localhost:8090/security/1.0/registry/clusters",
            event_handler=runner_utils.my_event_handler
        )

        response = runner_utils.result_ok

        if len(response) == 0:
            return "", ""
        cluster_list = ""
        if response[hosts]['rc'] == 0:
            cluster_list = response[hosts]['stdout']
        if cluster_list == "":
            return "", ""
        try:
            res = json.loads(cluster_list)
        except Exception as e:
            res = ""

        for cluster in res:
            cluster_name = cluster['clusterName']
            payload = f'{{"clusterName":"{cluster_name}"}}'
            # Look up the Principals who have the given role ResourceOwner on the specified resource
            # (Topic:confluent-audit-log-events) for the given cluster.
            runner_utils = AnsibleRunnerUtils()
            ansible_hosts, host_pattern = AnsibleRunnerUtils.get_host_and_pattern_from_host_list(hosts)
            ansible_runner.run(
                host_pattern=host_pattern,
                inventory=AnsibleRunnerUtils.get_inventory_dict(input_context, hosts),
                module="shell",
                module_args=f"curl -ku '{mds_user}:{mds_password}' "
                            f"https://localhost:8090/security/1.0/lookup/role/ResourceOwner/resource"
                            f"/Topic/name/confluent-audit-log-events "
                            f"-H 'Content-Type: application/json' "
                            f"-d '{payload}'",
                event_handler=runner_utils.my_event_handler
            )

            response2 = runner_utils.result_ok

            if len(response2) == 0:
                continue

            if response2[hosts]['rc'] == 0:
                stdout = response2[hosts]['stdout']
                try:
                    role = json.loads(stdout)
                except Exception as e:
                    role = []
                if len(role) == 0:
                    continue
                principal_name = role[0].split(";")[0].split("User:")[1]
                # If a principal exists for this cluster, this is the destination kafka cluster for audit logs
                return cluster, principal_name

        return "", {}
