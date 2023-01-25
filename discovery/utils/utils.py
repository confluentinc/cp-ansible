import argparse
import logging
import sys
from collections import OrderedDict
from os.path import exists
from jproperties import Properties

import yaml


def singleton(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


def load_properties_to_dict(content):
    """
    Read the file passed as parameter as a properties file.
    """
    configs = Properties()
    configs.load(content)
    prop_view = configs.items()
    props = {}
    for item in prop_view:
        key = item[0]
        val = item[1][0]
        props[key] = val
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
    ansible_python_interpreter = 'auto'
    output_file = None
    from_version = None
    verbosity = 0

    def __init__(self,
                 ansible_hosts,
                 ansible_connection,
                 ansible_user,
                 ansible_become,
                 ansible_become_user,
                 ansible_become_method,
                 ansible_ssh_private_key_file,
                 verbosity,
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
        self.verbosity = verbosity
        self.output_file = output_file


class Arguments:

    @staticmethod
    def parse_arguments():
        # Initialize parser

        parser = argparse.ArgumentParser()

        # Adding optional argument
        parser.add_argument("--input", type=str, help="Input Inventory file")
        parser.add_argument("--hosts", type=str, action="extend", nargs="*", help="List of hosts")
        parser.add_argument("--from_version", type=str, help="Target cp cluster version")
        parser.add_argument("--verbosity", type=int, help="Log level")
        parser.add_argument("--ansible_connection", type=str, default=None,
                            help="The connection plugin actually used for the task on the target host.")

        parser.add_argument("--ansible_user", type=str, default=None, help="The user Ansible ‘logs in’ as.")
        parser.add_argument("--ansible_become", type=bool, default=False, help="Boolean to use privileged ")
        parser.add_argument("--ansible_become_method", type=str, default='sudo', help="Method to become privileged")
        parser.add_argument("--ansible_become_user", type=str, default=None,
                            help="The user Ansible ‘becomes’ after using privilege escalation.")
        parser.add_argument("--ansible_ssh_private_key_file", type=str, default=None, help="Private key for ssh login")
        parser.add_argument("--ansible_ssh_extra_args", type=str, default=None, help="Extra arguments for ssh")
        parser.add_argument("--ansible_python_interpreter", type=str, default='auto', help="Python interpreter path")
        parser.add_argument("--output_file", type=str, default='inventory.yml', help="Generated output inventory file")

        # Read arguments from command line
        return parser.parse_args()

    @classmethod
    def validate_args(cls, args):

        # Set the default verbosity to INFO level
        verbosity = args.verbosity if args.verbosity and args.verbosity >= 0 and args.verbosity <= 4 else 3
        logger.setLevel((5 - verbosity) * 10)

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
                            verbosity=args.verbosity,
                            output_file=args.output_file,
                            from_version=vars.get("from_version"))

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
                logger.error("Invalid version for from_version. It should be in form of x.y.z or z.y")
                vars["from_version"] = None
                return

            for version in versions:
                if not version.isnumeric():
                    logger.error("Major, minor and patch versions should be of numbers.")
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

        if args.from_version:
            vars['from_version'] = args.from_version

        return vars

    @classmethod
    def __parse_inventory_file(cls, args):
        # Parse the input inventory file if present
        try:
            return yaml.safe_load(open(args.input))
        except Exception as e:
            logger.warning(f"Input inventory file '{args.input}' not provided or its incorrect")
            return None


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
