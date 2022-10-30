from discovery.api.ansible_internal import AnsibleInternalSystemAPI, AnsibleInternalServiceAPI
from discovery.utils.utils import Logger

logger = Logger.get_logger()


class SystemPropertyManager(AnsibleInternalSystemAPI):
    pass


class ServicePropertyManager(AnsibleInternalServiceAPI):
    pass
