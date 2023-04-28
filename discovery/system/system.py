#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import re

from discovery.manager.manager import SystemPropertyManager
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.services import ConfluentServices
from discovery.utils.utils import InputContext, Logger, terminate_script

logger = Logger.get_logger()


class SystemPropertyBuilder:
    inventory = None
    input_context = None

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context

    def with_service_host_mappings(self):

        mappings = SystemPropertyManager.get_service_host_mapping(self.input_context)

        for group, hosts in mappings.items():
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
        hosts = self.input_context.ansible_hosts
        any_defined_group = res = next(iter(hosts))
        host = hosts.get(any_defined_group, [])[0]
        if not host:
            terminate_script(f"No host found in group: {any_defined_group}")
        mappings = SystemPropertyManager.get_package_facts(self.input_context, hosts=[host])
        installation_method = 'package' if mappings.get(host, None) else 'archive'
        self.inventory.set_variable('all', 'installation_method', installation_method)

        return self

    def with_archive_properties(self):
        if 'installation_method' in self.inventory.groups.get('all').vars and \
                self.inventory.groups.get('all').vars.get('installation_method') != 'archive':
            return

        service_facts = SystemPropertyManager.get_service_facts(self.input_context)
        if not service_facts:
            logger.error("Cannot find any CP service up and running. Cannot proceed for archive property details")
            return

        confluent_services = ConfluentServices(self.input_context)
        # check if we have kafka broker hosts available.
        aHost = None
        zk_service_name = confluent_services.ZOOKEEPER().name
        bk_service_name = confluent_services.KAFKA_BROKER().name

        for host, data in service_facts.items():
            service_keys = service_facts.get(host).get('services').keys()
            if zk_service_name in service_keys or bk_service_name in service_keys:
                aHost = host
                break

        if not aHost:
            logger.error(f"Cannot find any host with either Broker or Zookeeper service running.\n"
                         f"Cannot proceed with service property mappings.")
            return

        service_details = SystemPropertyManager.get_service_details(self.input_context,
                                                                    confluent_services.KAFKA_BROKER(),
                                                                    [aHost])
        exec_start = service_details.get(aHost).get('status', {}).get('ExecStart', '')
        pattern = '.*path=(.*?)[\w\-\d\.]*\/bin'
        match = re.search(pattern, exec_start)

        if match:
            self.inventory.set_variable('all', 'archive_destination_path', match[1].rstrip("/"))
