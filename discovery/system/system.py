#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import json

from discovery.utils.constants import ConfluentServices
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, PythonAPIUtils

logger = Logger.get_logger()


class SystemPropertyBuilder:
    inventory = None
    input_context = None

    def __init__(self,  input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context

    def with_service_host_mappings(self):

        mappings = SystemPropertyManager.get_service_host_mapping(self.input_context)

        for service, hosts in mappings.items():
            group = ConfluentServices.get_group_by_key(service)
            self.inventory.add_group(group)
            for host in hosts:
                self.inventory.add_host(host, group)

        return self

    def with_ansible_variables(self):

        self.inventory.set_variable('all', 'ansible_user', self.input_context.ansible_user)
        self.inventory.set_variable('all', 'ansible_become', self.input_context.ansible_become)
        self.inventory.set_variable('all', 'ansible_connection', self.input_context.ansible_connection)

        return self

    def with_installation_method(self):
        mappings = SystemPropertyManager.get_package_facts(self.input_context, self.input_context.ansible_hosts[0])
        installation_method = 'package' if mappings else 'archive'
        self.inventory.set_variable('all', 'installation_method', installation_method)

        return self


class SystemPropertyManager:

    @staticmethod
    def get_service_host_mapping(input_context: InputContext, **kwargs) -> dict:

        logger.info(f"Getting the service<->host mapping for {input_context.ansible_hosts}")
        mappings = SystemPropertyManager.get_service_facts(input_context)
        if not mappings:
            logger.error(f"Could not get the service mappings. Please see the logs for details.")

        logger.debug(mappings)
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
        response = PythonAPIUtils.execute_play(input_context, play)

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
                        # host_list = mapping.get(service_key, list())
                        # host_list.append(host)
                        host_list = mapping.get(service_key, set())
                        host_list.add(host)
                        mapping[service_key] = list(host_list)

        return mapping

    @classmethod
    def get_service_details(cls, input_context: InputContext, service: ConfluentServices, hosts: list = None):

        hosts = hosts if hosts is not None else input_context.ansible_hosts
        play = dict(
            name="Ansible Play",
            hosts=hosts,
            gather_facts='no',
            tasks=[
                dict(action=dict(module='ansible.builtin.systemd', args=dict(name=service.value.get("name"))))
            ]
        )
        mappings = dict()
        response = PythonAPIUtils.execute_play(input_context, play)
        for host, result in response.items():
            mappings[host] = result._result

        logger.debug(json.dumps(mappings, indent=4))
        return mappings

    @classmethod
    def get_ansible_facts(cls, input_context: InputContext, hosts: list = []):

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
        response = PythonAPIUtils.execute_play(input_context, play)
        for host, result in response.items():
            mappings[host] = result._result

        logger.debug(json.dumps(mappings, indent=4))
        return mappings

    @classmethod
    def get_package_facts(cls, input_context: InputContext, hosts: list = []):

        hosts = hosts if hosts is not None else input_context.ansible_hosts
        play = dict(
            name="Ansible Play",
            hosts=hosts,
            gather_facts='yes',
            tasks=[
                dict(action=dict(module='package_facts'))
            ]
        )

        mappings = dict()
        response = PythonAPIUtils.execute_play(input_context, play)
        for host, result in response.items():
            confluent_packages = dict()
            for package, details in result._result.get("ansible_facts").get("packages").items():
                if package.startswith("confluent"):
                    confluent_packages[package] = details
            mappings[host] = confluent_packages

        logger.debug(json.dumps(mappings, indent=4))
        return mappings

    @classmethod
    def get_java_facts(cls, input_context: InputContext, hosts: list = []):

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
        response = PythonAPIUtils.execute_play(input_context, play)

        for host, result in response.items():
            if result._result.get('rc') == 0:
                mappings[host] = result._result.get('stdout')
            else:
                logger.error(f"Could not get java home for host {host}. Got error {result._result.get('msg')}")

        logger.debug(json.dumps(mappings, indent=4))
        return mappings


if __name__ == "__main__":
    input_context = InputContext(['zookeeper1'], 'docker', False, None, 4)
    SystemPropertyManager.get_java_facts(input_context, ['zookeeper1'])
