import inspect

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.utils import Logger

logger = Logger.get_logger()


def get_service_builder_class(modules, default_class_name:str, version: str = None) -> AbstractPropertyBuilder:

    members = inspect.getmembers(modules, inspect.isclass)
    if version:
        major, minor, *_ = version.split('.')
        class_name = f"{default_class_name}{major}{minor}"
        for name, obj in members:
            if class_name == name:
                return obj
        logger.warning(f"Cannot find {default_class_name} specific class for version {version}")

    for name, obj in members:
        if name == default_class_name:
            return obj
