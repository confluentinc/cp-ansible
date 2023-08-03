import argparse
import logging
import sys
from collections import OrderedDict
from os.path import dirname
from os.path import exists
from os.path import realpath

import yaml
from jproperties import Properties


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


class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super(MultiOrderedDict, self).__setitem__(key, value)
            super().__setitem__(key, value)


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
    ansible_password = None
    ansible_hosts = None
    ansible_become_user = 'root'
    ansible_become_method = 'sudo'
    ansible_ssh_private_key_file = None
    ansible_ssh_extra_args = None
    ansible_python_interpreter = 'auto'
    output_file = None
    from_version = None
    verbosity = 0
    service_overrides = dict()
    skip_validation = False
    ansible_become_password = None
    ansible_common_remote_group = None
    multi_threaded = True

    def __init__(self,
                 ansible_hosts,
                 ansible_connection,
                 ansible_user,
                 ansible_password,
                 ansible_become,
                 ansible_become_user,
                 ansible_become_method,
                 ansible_become_password,
                 ansible_common_remote_group,
                 ansible_ssh_private_key_file,
                 verbosity,
                 ansible_ssh_extra_args,
                 ansible_python_interpreter,
                 from_version,
                 output_file,
                 service_overrides,
                 skip_validation,
                 multi_threaded):
        self.ansible_hosts = ansible_hosts
        self.ansible_connection = ansible_connection
        self.ansible_user = ansible_user
        self.ansible_password = ansible_password
        self.ansible_become = ansible_become
        self.ansible_become_user = ansible_become_user
        self.ansible_become_method = ansible_become_method
        self.ansible_become_password = ansible_become_password
        self.ansible_common_remote_group = ansible_common_remote_group
        self.ansible_ssh_private_key_file = ansible_ssh_private_key_file
        self.from_version = from_version
        self.ansible_ssh_extra_args = ansible_ssh_extra_args
        self.ansible_python_interpreter = ansible_python_interpreter
        self.verbosity = verbosity
        self.output_file = output_file
        self.service_overrides = service_overrides
        self.skip_validation = skip_validation
        self.multi_threaded = multi_threaded


class Arguments:
    input_context: InputContext = None

    @staticmethod
    def parse_arguments():
        # Initialize parser

        parser = argparse.ArgumentParser()

        # Adding optional argument
        parser.add_argument("--input", type=str, required=True, help="Input Inventory file")
        parser.add_argument("--limit", type=str, nargs="*", help="Limit to list of hosts")
        parser.add_argument("--from_version", type=str, help="Target cp cluster version")
        parser.add_argument("--verbosity", type=int, default=1, help="Log level")
        parser.add_argument("--output_file", type=str, help="Generated output inventory file")
        parser.add_argument("--skip_validation", type=bool, default=False, help="Skip validations")
        parser.add_argument("--multi_threaded", type=bool, default=True, help="Use multi threaded environment")

        # Read arguments from command line
        return parser.parse_args()

    @classmethod
    def validate_args(cls, args):

        vars = cls.get_vars(args)
        cls.__validate_variables(vars)

        # Set the default verbosity to INFO level
        log_level = vars.get("verbosity")
        verbosity = log_level if log_level and log_level >= 0 and log_level <= 4 else 3
        logger.setLevel((5 - verbosity) * 10)

    @classmethod
    def get_input_context(cls, args) -> InputContext:

        if Arguments.input_context:
            return Arguments.input_context

        hosts = cls.get_hosts(args)
        vars = cls.get_vars(args)
        Arguments.input_context = InputContext(ansible_hosts=hosts,
                                               ansible_connection=vars.get("ansible_connection"),
                                               ansible_become=vars.get("ansible_become", False),
                                               ansible_become_user=vars.get("ansible_become_user"),
                                               ansible_become_method=vars.get("ansible_become_method", 'sudo'),
                                               ansible_become_password=vars.get("ansible_become_password", None),
                                               ansible_common_remote_group=vars.get("ansible_common_remote_group",
                                                                                    None),
                                               ansible_ssh_private_key_file=vars.get("ansible_ssh_private_key_file"),
                                               ansible_user=vars.get("ansible_user"),
                                               ansible_password=vars.get("ansible_password"),
                                               ansible_ssh_extra_args=vars.get("ansible_ssh_extra_args"),
                                               ansible_python_interpreter=vars.get("ansible_python_interpreter",
                                                                                   'auto'),
                                               output_file=vars.get("output_file"),
                                               verbosity=vars.get("verbosity", 3),
                                               from_version=vars.get("from_version"),
                                               service_overrides=vars.get("service_overrides", dict()),
                                               skip_validation=vars.get('skip_validation'),
                                               multi_threaded=vars.get('multi_threaded'))
        return Arguments.input_context

    @classmethod
    def __validate_variables(cls, vars):
        logger.debug(vars)

        # Validate the connection type
        valid_connection_types = ["ssh", "docker"]
        if vars.get("ansible_connection") not in valid_connection_types:
            message = f"Invalid value for ansible_connection {vars.get('ansible_connection')}. " \
                      f"it has to be {valid_connection_types}"
            terminate_script(message)

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
        if not inventory:
            terminate_script(f"Could not load or parse inventory to get host list")

        hosts = inventory.get('hosts', {})

        # Limit the hosts list based on command line argument
        if args.limit:
            selected_hosts = args.limit.split(',')
            for group, group_hosts in hosts:
                group_hosts = list(set(group_hosts) & set(selected_hosts))
                hosts[group] = group_hosts

        return hosts

    @classmethod
    def get_vars(cls, args) -> dict:
        inventory = cls.__parse_inventory_file(args)
        vars = dict()

        # Check vars in the inventory file
        if inventory:
            vars = inventory.get('vars')

        if args.limit:
            vars['limit'] = args.limit

        if args.from_version:
            vars['from_version'] = args.from_version

        if args.verbosity:
            vars['verbosity'] = args.verbosity

        if args.output_file:
            vars['output_file'] = args.output_file

        if args.skip_validation:
            vars['skip_validation'] = bool(args.skip_validation)

        if args.skip_validation:
            vars['multi_threaded'] = bool(args.multi_threaded)

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
        parent_dir = dirname(dirname(realpath(__file__)))
        file_path = f"{parent_dir}/service/config/{file_name}"
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


def _host_group_declared_in_inventory(hosts: dict, input_context: InputContext) -> bool:
    from discovery.utils.services import ConfluentServices
    from discovery.utils.constants import DEFAULT_GROUP_NAME

    defined_groups = set(ConfluentServices(input_context).get_all_group_names())
    defined_groups.add(DEFAULT_GROUP_NAME)

    declared_groups = hosts.keys()
    extra_groups = defined_groups.difference(defined_groups)
    if extra_groups:
        terminate_script(f"Unrecognised group: {extra_groups}. Valid group names are {defined_groups}")

    return False if DEFAULT_GROUP_NAME in declared_groups else True


def terminate_script(message: str = None):
    logger.error(message)
    sys.exit(message)
