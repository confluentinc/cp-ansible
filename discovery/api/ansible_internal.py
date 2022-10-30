import base64
import json
import re

from ansible import context
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager

from discovery.utils.constants import ConfluentServices, DEFAULT_KEY
from discovery.utils.utils import Logger, InputContext, load_properties_to_dict

logger = Logger.get_logger()


class AnsibleInternalSystemAPI:

    @staticmethod
    def get_service_host_mapping(input_context: InputContext, **kwargs) -> dict:

        logger.info(f"Getting the service<->host mapping for {input_context.ansible_hosts}")
        mappings = AnsibleInternalSystemAPI.get_service_facts(input_context)
        if not mappings:
            logger.error(f"Could not get the service mappings. Please see the logs for details.")

        logger.info(f"Host service mappings:\n{json.dumps(mappings)}")
        return mappings

    @classmethod
    def get_service_facts(cls, input_context: InputContext) -> dict:

        # Play dict for Ansible service facts
        play = dict(
            name="Ansible Service Facts",
            hosts=input_context.ansible_hosts,
            gather_facts='yes',
            tasks=[
                dict(action=dict(module='service_facts'))
            ]
        )
        response = InternalAPIUtils.execute_play(input_context, play)

        # Create a service host mapping
        mapping = dict()
        for host, result in response.items():
            services = result._result.get("ansible_facts").get("services")
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

        return mapping

    @classmethod
    def get_service_details(cls, input_context: InputContext, service: ConfluentServices, hosts: list = None):

        hosts = hosts if hosts is not None else input_context.ansible_hosts
        play = dict(
            name="Get service details",
            hosts=hosts,
            gather_facts='no',
            tasks=[
                dict(action=dict(module='ansible.builtin.systemd', args=dict(name=service.value.get("name"))))
            ]
        )
        mappings = dict()
        response = InternalAPIUtils.execute_play(input_context, play)
        for host, result in response.items():
            mappings[host] = result._result

        logger.debug(json.dumps(mappings, indent=4))
        return mappings

    @classmethod
    def get_ansible_facts(cls, input_context: InputContext, hosts: list = None):
        if not hosts:
            hosts = list()

        hosts = hosts if hosts is not None else input_context.ansible_hosts
        play = dict(
            name="Ansible facts",
            hosts=hosts,
            gather_facts='yes',
            tasks=[
                dict(action=dict(module='ansible_facts'))
            ]
        )

        mappings = dict()
        response = InternalAPIUtils.execute_play(input_context, play)
        for host, result in response.items():
            mappings[host] = result._result

        logger.debug(json.dumps(mappings, indent=4))
        return mappings

    @classmethod
    def get_package_facts(cls, input_context: InputContext, hosts: list = None):
        if not hosts:
            hosts = list()

        hosts = hosts if hosts is not None else input_context.ansible_hosts
        play = dict(
            name="Get host package facts",
            hosts=hosts,
            gather_facts='yes',
            tasks=[
                dict(action=dict(module='package_facts'))
            ]
        )

        mappings = dict()
        response = InternalAPIUtils.execute_play(input_context, play)
        for host, result in response.items():
            confluent_packages = dict()
            for package, details in result._result.get("ansible_facts").get("packages").items():
                if package.startswith("confluent"):
                    confluent_packages[package] = details
            mappings[host] = confluent_packages

        logger.debug(json.dumps(mappings, indent=4))
        return mappings

    @classmethod
    def get_java_facts(cls, input_context: InputContext, hosts: list = None):
        if not hosts:
            hosts = list()

        hosts = hosts if hosts is not None else input_context.ansible_hosts
        play = dict(
            name="Ansible Play",
            hosts=hosts,
            gather_facts='no',
            tasks=[
                dict(action=dict(module='shell', cmd='dirname $(dirname $(readlink -f $(which java)))'))
            ]
        )

        mappings = dict()
        response = InternalAPIUtils.execute_play(input_context, play)

        for host, result in response.items():
            if result._result.get('rc') == 0:
                mappings[host] = result._result.get('stdout')
            else:
                logger.error(f"Could not get java home for host {host}. Got error {result._result.get('msg')}")

        logger.debug(json.dumps(mappings, indent=4))
        return mappings


class AnsibleInternalServiceAPI:

    @staticmethod
    def __get_service_properties_file(input_context: InputContext,
                                      service: ConfluentServices,
                                      hosts: list):
        if not hosts:
            logger.error(f"Host list is empty for service {service.value.get('name')}")
            return None

        host = hosts[0]
        service_details = AnsibleInternalSystemAPI.get_service_details(input_context, service, host)
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
        service_facts = AnsibleInternalSystemAPI.get_service_details(input_context, service, hosts)
        environment = service_facts.get("Environment", None)
        return AnsibleInternalServiceAPI.parse_environment_details(environment)

    @staticmethod
    def get_property_mappings(input_context: InputContext, service: ConfluentServices, hosts: list) -> dict:

        mappings = dict()
        property_file_dict = AnsibleInternalServiceAPI.__get_service_properties_file(input_context, service, hosts)
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
            response = InternalAPIUtils.execute_play(input_context, play)
            for host in hosts:
                properties = base64.b64decode(response[host]._result['content']).decode('utf-8')
                host_properites = mappings.get(host, dict())
                host_properites.update({key: load_properties_to_dict(properties)})
                mappings[host] = host_properites

        return mappings

    @staticmethod
    def get_keystore_alias_names(input_context: InputContext, hosts: list, keystorepass: str,
                                 keystorepath: str) -> list:

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

        response = InternalAPIUtils.execute_play(input_context, play)
        if response[hosts[0]]._result['rc'] == 0:
            stdout = response[hosts[0]]._result['stdout']
            aliases = [y for y in (x.strip() for x in stdout.splitlines()) if y]
            return aliases
        else:
            return []

    @staticmethod
    def get_log_file_path(input_context: InputContext, service: ConfluentServices, hosts: list, log4j_opts_env_var):
        # check if overriden as env var
        env_details = AnsibleInternalServiceAPI.get_env_details(input_context, service, hosts)
        log4j_opts = env_details.get(log4j_opts_env_var, None)
        if log4j_opts is not None:
            if "-Dlog4j.configuration=file:" in log4j_opts:
                log4j_path = log4j_opts.split("-Dlog4j.configuration=file:", 1)[1].split(" ", 1)[0]
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
        response = InternalAPIUtils.execute_play(input_context, play)
        if len(response) == 0:
            return None
        if response[hosts[0]]._result['rc'] == 0:
            process_details = response[hosts[0]]._result['stdout']
            if "-Dlog4j.configuration=file:" in process_details:
                log4j_path = process_details.split("-Dlog4j.configuration=file:", 1)[1].split(" ", 1)[0]
                return log4j_path

        return None

    @staticmethod
    def get_root_logger(input_context: InputContext, hosts: list, log4j_file, default_log4j_file):
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
            response = InternalAPIUtils.execute_play(input_context, play)
            if len(response) == 0:
                continue
            if response[hosts[0]]._result['rc'] == 0:
                logger_def = response[hosts[0]]._result['stdout']
                return logger_def.split("log4j.rootLogger=", 1)[1].strip(), file

        return None, None

    @staticmethod
    def get_audit_log_properties(input_context: InputContext, hosts: str, mds_user: str, mds_password: str) -> tuple:
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

        response = InternalAPIUtils.execute_play(input_context, play1)
        if len(response) == 0:
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
            # Look up the Principals who have the given role ResourceOwner on the specified resource
            # (Topic:confluent-audit-log-events) for the given cluster.
            play2 = dict(
                name="Check rolebinding to get principal name",
                hosts=hosts,
                gather_facts='no',
                tasks=[
                    dict(action=dict(module='shell',
                                     args=f"curl -ku '{mds_user}:{mds_password}' "
                                          f"https://localhost:8090/security/1.0/lookup/role/ResourceOwner/resource"
                                          f"/Topic/name/confluent-audit-log-events "
                                          f"-H 'Content-Type: application/json' "
                                          f"-d '{payload}'"))
                ]
            )
            response2 = InternalAPIUtils.execute_play(input_context, play2)
            if len(response2) == 0:
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

        return "", {}


class InternalAPIUtils:

    @staticmethod
    def execute_play(input_context: InputContext, play: dict):

        # since the API is constructed for CLI it expects certain options to always be set in the context object
        context.CLIARGS = ImmutableDict(connection=input_context.ansible_connection, module_path=[], diff=False,
                                        become=input_context.ansible_become, remote_user=input_context.ansible_user,
                                        verbosity=input_context.verbosity, host_key_checking=False,
                                        become_user=input_context.ansible_become_user,
                                        private_key_file=input_context.ansible_ssh_private_key_file,
                                        ssh_extra_args=input_context.ansible_ssh_extra_args, forks=10, check=False,
                                        become_method=input_context.ansible_become_method)

        list_of_hosts = input_context.ansible_hosts
        sources = ','.join(list_of_hosts)
        if len(list_of_hosts) == 1:
            sources += ','

        # initialize needed objects
        loader = DataLoader()  # Takes care of finding and reading yaml, json and ini files
        passwords = dict(vault_pass='secret')

        # Instantiate our ResultsCollectorJSONCallback for handling results as they come in.
        # Ansible expects this to be one of its main display outlets
        results_callback = ResultsCollectorJSONCallback()

        # create inventory, use path to host config file as source or hosts in a comma separated string
        inventory = InventoryManager(loader=loader, sources=sources)

        # variable manager takes care of merging all the different sources to give you a unified
        # view of variables available in each context
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        # instantiate task queue manager, which takes care of forking and setting up
        # all objects to iterate over host list and tasks
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords=passwords,
            stdout_callback=results_callback
        )
        play = Play().load(play, variable_manager=variable_manager, loader=loader)

        # Actually run it
        try:
            tqm.run(play)  # most interesting data for a play is actually sent to the callback's methods

        finally:
            tqm.cleanup()
            if loader:
                loader.cleanup_all_tmp_files()

        return InternalAPIUtils.parse_ansible_api_response(results_callback)

    @staticmethod
    def parse_ansible_api_response(response) -> dict:

        for host, msg in response.host_failed.items():
            logger.error(f"Host {host} failed: {msg._result['msg']}")

        for host, msg in response.host_unreachable.items():
            logger.error(f"Host {host} failed: {msg._result['msg']}")

        return response.host_ok


class ResultsCollectorJSONCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in.

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin.
    """

    def __init__(self, *args, **kwargs):
        super(ResultsCollectorJSONCallback, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        host = result._host
        self.host_unreachable[host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """Print a json representation of the result.

        Also, store the result in an instance attribute for retrieval later
        """
        host = result._host
        self.host_ok[host.get_name()] = result
        # print(json.dumps({host.name: result._result}, indent=4))

    def v2_runner_on_failed(self, result, *args, **kwargs):
        host = result._host
        self.host_failed[host.get_name()] = result
