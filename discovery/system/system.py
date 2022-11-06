#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import re

from discovery.manager.manager import SystemPropertyManager
from discovery.utils.constants import ConfluentServices
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger

logger = Logger.get_logger()


class SystemPropertyBuilder:
    inventory = None
    input_context = None

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
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
        self.inventory.set_variable('all', 'ansible_become_user', self.input_context.ansible_become_user)
        self.inventory.set_variable('all', 'ansible_become_method', self.input_context.ansible_become_method)
        self.inventory.set_variable('all', 'ansible_ssh_extra_args', self.input_context.ansible_ssh_extra_args)
        self.inventory.set_variable('all', 'ansible_ssh_private_key_file',
                                    self.input_context.ansible_ssh_private_key_file)
        self.inventory.set_variable('all', 'ansible_python_interpreter', self.input_context.ansible_python_interpreter)
        return self

    def with_installation_method(self):
        host = self.input_context.ansible_hosts[0]
        mappings = SystemPropertyManager.get_package_facts(self.input_context, host)
        installation_method = 'package' if mappings.get(host, None) else 'archive'
        self.inventory.set_variable('all', 'installation_method', installation_method)

        return self

    def with_archive_properties(self):
        if self.inventory.groups.get('all').vars.get('installation_method') != 'archive':
            return

        service_facts = SystemPropertyManager.get_service_facts(self.input_context)
        if not service_facts:
            logger.error(f"Cannot find any CP service up and running. Cannot proceed for archive property details")
            return

        host = service_facts.get(ConfluentServices.KAFKA_BROKER.name)[0]
        service_details = SystemPropertyManager.get_service_details(self.input_context, ConfluentServices.KAFKA_BROKER,
                                                                    [host])
        exec_start = service_details.get(host).get('status', {}).get('ExecStart', '')
        pattern = '.*path=(.*?)[\w\-\d\.]*\/bin'
        match = re.search(pattern, exec_start)

        if match:
            self.inventory.set_variable('all', 'archive_destination_path', match[1].rstrip("/"))
