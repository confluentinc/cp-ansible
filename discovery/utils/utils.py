import argparse
import logging
import sys
from collections import OrderedDict
from os.path import exists

import yaml
from ansible import context
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager


def singleton(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


def load_properties_to_dict(content, sep='=', comment_char='#'):
    """
    Read the file passed as parameter as a properties file.
    """
    props = {}
    content = content.split("\n")
    for line in content:
        l = line.strip()
        if l and not l.startswith(comment_char):
            key_value = l.split(sep)
            key = key_value[0].strip()
            value = sep.join(key_value[1:]).strip().strip('"')
            props[key] = value
    return props


class Logger:
    """
    Logging levels - https://docs.python.org/3/howto/logging.html
    Level       Numeric value
    CRITICAL    50
    ERROR       40
    WARNING     30
    INFO        20
    DEBUG       10
    NOTSET      0

    """
    __logger = None

    @staticmethod
    def get_logger():
        if not Logger.__logger:
            Logger.__logger = Logger.__initialize()
        return Logger.__logger

    @staticmethod
    def __initialize():
        # create logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')

        # add formatter to ch
        ch.setFormatter(formatter)

        # add ch to logger
        logger.addHandler(ch)
        return logger


logger = Logger.get_logger()


@singleton
class InputContext:
    ansible_connection = None
    ansible_become = False
    ansible_user = None
    ansible_hosts = None
    ansible_become_user = None
    ansible_become_method = 'sudo'
    ansible_ssh_private_key_file = None
    ansible_ssh_extra_args = None
    ansible_python_interpreter = None
    output_file = None
    from_version = None
    log_level = 0

    def __init__(self,
                 ansible_hosts,
                 ansible_connection,
                 ansible_user,
                 ansible_become,
                 ansible_become_user,
                 ansible_become_method,
                 ansible_ssh_private_key_file,
                 log_level,
                 ansible_ssh_extra_args,
                 ansible_python_interpretor=None,
                 from_version=None,
                 output_file=None):
        self.ansible_hosts = ansible_hosts
        self.ansible_connection = ansible_connection
        self.ansible_user = ansible_user
        self.ansible_become = ansible_become
        self.ansible_become_user = ansible_become_user
        self.ansible_become_method = ansible_become_method
        self.ansible_ssh_private_key_file = ansible_ssh_private_key_file
        self.from_version = from_version
        self.ansible_ssh_extra_args = ansible_ssh_extra_args
        self.ansible_python_interpreter = ansible_python_interpretor
        self.log_level = log_level
        self.output_file = output_file


class Arguments:

    @staticmethod
    def parse_arguments():
        # Initialize parser

        parser = argparse.ArgumentParser()

        # Adding optional argument
        '''
        connection='docker', module_path=[], forks=10, become=None,
        become_method=None, become_user=null, check=False, diff=False, log_level=0
        '''
        parser.add_argument("--input", type=str, help="Input Inventory file")
        parser.add_argument("--hosts", type=str, action="extend", nargs="*", help="List of hosts")
        parser.add_argument("--log_level", type=int, default=2,
                            help="Log level. CRITICAL(5) ERROR(4) WARNING(3) INFO(2) DEBUG(1) NOTSET(0)")
        parser.add_argument("--ansible_connection", type=str, default=None,
                            help="The connection plugin actually used for the task on the target host.")

        parser.add_argument("--ansible_user", type=str, default=None, help="The user Ansible ‘logs in’ as.")
        parser.add_argument("--ansible_become", type=bool, default=False, help="Boolean to use privileged ")
        parser.add_argument("--ansible_become_method", type=str, default='sudo', help="Method to become privileged")
        parser.add_argument("--ansible_become_user", type=str, default=None,
                            help="The user Ansible ‘becomes’ after using privilege escalation.")
        parser.add_argument("--ansible_ssh_private_key_file", type=str, default=None, help="Private key for ssh login")
        parser.add_argument("--ansible_ssh_extra_args", type=str, default=None, help="Extra arguments for ssh")
        parser.add_argument("--ansible_python_interpreter", type=str, default=None, help="Python interpreter path")

        # Read arguments from command line
        return parser.parse_args()

    @classmethod
    def validate_args(cls, args):

        # Set the default log_level to INFO level
        log_level = args.log_level if args.log_level > 0 and args.log_level < 6 else 4
        logger.setLevel(log_level * 10)

        cls.__validate_hosts(cls.get_hosts(args))
        cls.__validate_variables(cls.get_vars(args))

    @classmethod
    def get_input_context(cls, args) -> InputContext:
        hosts = cls.get_hosts(args)
        vars = cls.get_vars(args)
        return InputContext(ansible_hosts=hosts,
                            ansible_connection=vars.get("ansible_connection"),
                            ansible_become=vars.get("ansible_become"),
                            ansible_become_user=vars.get("ansible_become_user"),
                            ansible_become_method=vars.get("ansible_become_method"),
                            ansible_ssh_private_key_file=vars.get("ansible_ssh_private_key_file"),
                            ansible_user=vars.get("ansible_user"),
                            ansible_ssh_extra_args=vars.get("ansible_ssh_extra_args"),
                            ansible_python_interpretor=vars.get("ansible_python_interpretor"),
                            from_version = vars.get("from_version"),
                            log_level=args.log_level)

    @classmethod
    def __validate_hosts(cls, hosts):
        # Validate list of hosts
        if len(hosts) < 1:
            message = "Please provide at least one host to proceed with discovery"
            logger.error(message)
            sys.exit(message)
        logger.debug(f"List of hosts: {hosts}")

    @classmethod
    def __validate_variables(cls, vars):
        logger.debug(vars)

        # Validate the connection type
        valid_connection_types = ["ssh", "docker"]
        if vars.get("ansible_connection") not in valid_connection_types:
            message = f"Invalid value for ansible_connection {vars.get('ansible_connection')}. " \
                      f"it has to be {valid_connection_types}"
            logger.error(message)
            sys.exit(message)

        # Validate from_version
        from_version = vars.get("from_version")
        if from_version:
            versions = from_version.split('.')
            if not versions or len(versions) > 3 or len(versions) < 2:
                logger.error(f"Invalid version for from_version. It should be in form of x.y.z or z.y")
                vars["from_version"] = None
                return

            for version in versions:
                if not version.isnumeric():
                    logger.error(f"Major, minor and patch versions should be of numbers.")
                    vars["from_version"] = None

    @classmethod
    def get_hosts(cls, args):
        inventory = cls.__parse_inventory_file(args)
        hosts = []

        # Check hosts in the inventory file
        if inventory:
            hosts.extend(inventory.get('all').get('hosts', []))

        # Check the command line options for hosts
        if args.hosts:
            hosts.extend(args.hosts)

        # Remove duplicates keeping the order
        return list(OrderedDict.fromkeys(hosts))

    @classmethod
    def get_vars(cls, args) -> dict:
        inventory = cls.__parse_inventory_file(args)
        vars = {}

        # Check vars in the inventory file
        if inventory:
            vars = inventory.get('all').get('vars')

        # Override the inventory vars with command line variables.
        if args.ansible_become:
            vars['ansible_become'] = args.ansible_become

        if args.ansible_user:
            vars['ansible_user'] = args.ansible_user

        if args.ansible_connection:
            vars['ansible_connection'] = args.ansible_connection

        if args.ansible_become_user:
            vars['ansible_become_user'] = args.ansible_become_user

        if args.ansible_become_method:
            vars['ansible_become_method'] = args.ansible_become_method

        if args.ansible_ssh_private_key_file:
            vars['ansible_ssh_private_key_file'] = args.ansible_ssh_private_key_file

        if args.ansible_ssh_extra_args:
            vars['ansible_ssh_extra_args'] = args.ansible_ssh_extra_args

        return vars

    @classmethod
    def __parse_inventory_file(cls, args):
        # Parse the input inventory file if present
        try:
            return yaml.safe_load(open(args.input))
        except:
            logger.warning(f"Input inventory file '{args.input}' not provided or its incorrect")
            return None


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


class PythonAPIUtils:

    @staticmethod
    def execute_play(input_context: InputContext, play: dict):

        # since the API is constructed for CLI it expects certain options to always be set in the context object
        context.CLIARGS = ImmutableDict(connection=input_context.ansible_connection, module_path=[], diff=False,
                                        become=input_context.ansible_become, remote_user=input_context.ansible_user,
                                        log_level=input_context.log_level, host_key_checking=False,
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

        return PythonAPIUtils.parse_ansible_api_response(results_callback)

    @staticmethod
    def parse_ansible_api_response(response) -> dict:

        for host, msg in response.host_failed.items():
            logger.error(f"Host {host} failed: {msg._result['msg']}")

        for host, msg in response.host_unreachable.items():
            logger.error(f"Host {host} failed: {msg._result['msg']}")

        return response.host_ok


class FileUtils:

    @staticmethod
    def __read_service_configuration_file(file_name):

        # Check if config file exists. We return an empty dictionary if there isn't any config
        file_path = f"service/config/{file_name}"
        if not exists(file_path):
            logger.error(f"Cannot find config file {file_name}. Returning an empty config.")
            return dict()

        with open(file_path, "r") as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logger.error(f"Cannot load configuration file {file_name}")

    @staticmethod
    def get_kafka_broker_configs(name):
        return FileUtils.__read_service_configuration_file("kafka_broker.yml").get(name, [])

    @staticmethod
    def get_zookeeper_configs(name):
        return FileUtils.__read_service_configuration_file("zookeeper.yml").get(name, [])

    @staticmethod
    def get_schema_registry_configs(name):
        return FileUtils.__read_service_configuration_file("schema_registry.yml").get(name, [])

    @staticmethod
    def get_kafka_rest_configs(name):
        return FileUtils.__read_service_configuration_file("kafka_rest.yml").get(name, [])

    @staticmethod
    def get_ksql_configs(name):
        return FileUtils.__read_service_configuration_file("ksql.yml").get(name, [])

    @staticmethod
    def get_control_center_configs(name):
        return FileUtils.__read_service_configuration_file("control_center.yml").get(name, [])

    @staticmethod
    def get_kafka_connect_configs(name):
        return FileUtils.__read_service_configuration_file("kafka_connect.yml").get(name, [])

    @staticmethod
    def get_kafka_replicator_configs(name):
        return FileUtils.__read_service_configuration_file("kafka_replicator.yml").get(name, [])
