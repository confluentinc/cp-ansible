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

    def get_inventory_data(self) -> dict:

        self.reconcile_inventory()
        if not self._groups_dict_cache:
            for (group_name, group) in iteritems(self.groups):
                if group_name in ['ungrouped']:
                    continue
                self._groups_dict_cache[group_name] = {}
                if group_name not in ['all', 'ungrouped']:
                    for h in group.get_hosts():
                        host_name = h.name
                        host_vars = h.vars
                        host_vars.pop("inventory_file", None)
                        host_vars.pop("inventory_dir", None)
                    self._groups_dict_cache[group_name]['hosts'] = {host_name: host_vars}
                self._groups_dict_cache[group_name]['vars'] = group.get_vars()

        return self._groups_dict_cache

    def put_inventory_data(self, data):
        # file_name = self.input_context.output_file if self.input_context.output_file else "inventory.yml"
        file_name = 'inventory.yml'
        with open(file_name, 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False, indent=2)

        logger.info(f"Inventory file successfully generated at {os.path.join(os.getcwd(), file_name)}")
        return data


if __name__ == "__main__":
    inventory = CPInventoryManager()
    inventory.add_group('kafka_broker')
    inventory.add_host('kafka-host1', 'kafka_broker')
    inventory.add_host('kafka-host2', 'kafka_broker')
    inventory.set_variable('kafka_broker', 'memory_limit', '30mb')

    kafka_custom_properties = {
        "broker": {
            "name": "BROKER",
            "port": 9091
        }
    }
    inventory.set_variable('all', 'kafka_broker_custom_listeners', kafka_custom_properties)
    data = inventory.get_inventory_data()
    print(inventory.put_inventory_data(data))
