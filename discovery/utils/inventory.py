import collections
import os

import yaml
from ansible.inventory.data import InventoryData
from ansible.module_utils.six import iteritems

from discovery.utils.utils import Logger, InputContext, singleton

logger = Logger.get_logger()


@singleton
class CPInventoryManager(InventoryData):
    input_context = None

    def __init__(self, input_context: InputContext = None):
        self.input_context = input_context
        super().__init__()

    def generate_final_inventory(self):
        data = self.get_inventory_data()
        self.put_inventory_data(data)

    def get_inventory_data(self) -> dict:
        """
        This method changes the internal structure of inventory to make it more readable. We should not be using
        this method to get the inventory data anywhere in the script
        :return:
        """
        self.reconcile_inventory()
        if not self._groups_dict_cache:
            for (group_name, group) in iteritems(self.groups):
                if group_name in ['ungrouped']:
                    continue
                self._groups_dict_cache[group_name] = {}
                if group_name not in ['all', 'ungrouped']:
                    hosts_dictionary = self._groups_dict_cache[group_name].get('hosts', dict())
                    for h in group.get_hosts():
                        host_name = h.name
                        host_vars = h.vars
                        host_vars.pop("inventory_file", None)
                        host_vars.pop("inventory_dir", None)
                        hosts_dictionary.update({host_name: host_vars})
                    self._groups_dict_cache[group_name]['hosts'] = hosts_dictionary
                self._groups_dict_cache[group_name]['vars'] = group.get_vars()

        return self._groups_dict_cache

    def put_inventory_data(self, data):
        # file_name = self.input_context.output_file if self.input_context.output_file else "inventory.yml"
        file_name = 'inventory.yml'
        with open(file_name, 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False, indent=2)

        logger.info(f"Inventory file successfully generated at {os.path.join(os.getcwd(), file_name)}")
        return data


class InventorySanitizer:

    @staticmethod
    def sanatize(inventory_data: dict) -> dict:
        pass

    @staticmethod
    def sort(invnetory_data: dict):
        from discovery.utils.constants import ConfluentServices
        group_list = [
            'all',
            ConfluentServices.ZOOKEEPER.value.get('group'),
            ConfluentServices.KAFKA_BROKER.value.get('group'),
            ConfluentServices.SCHEMA_REGISTRY.value.get('group'),
            ConfluentServices.KAFKA_REST.value.get('group'),
            ConfluentServices.KAFKA_CONNECT.value.get('group'),
            ConfluentServices.KSQL.value.get('group'),
            ConfluentServices.KAFKA_REPLICATOR.value.get('group'),
            ConfluentServices.CONTROL_CENTER.value.get('group'),
        ]

        ordered_dict = collections.OrderedDict(invnetory_data)

        for group in group_list:
            if group in ordered_dict.keys():
                ordered_dict.move_to_end(group)

        return ordered_dict
