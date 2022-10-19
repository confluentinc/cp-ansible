import collections
import os

import yaml
from ansible.inventory.data import InventoryData
from ansible.module_utils.six import iteritems

from discovery.utils.utils import Logger, InputContext, singleton
from discovery.utils.constants import ConfluentServices

logger = Logger.get_logger()


@singleton
class CPInventoryManager(InventoryData):
    input_context = None

    def __init__(self, input_context: InputContext = None):
        self.input_context = input_context
        super().__init__()

    def generate_final_inventory(self):
        data = self.get_inventory_data()
        InventorySanitizer.sanitize(data)
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
    def sanitize(inventory_data: dict) -> dict:
        InventorySanitizer.typecast(inventory_data)
        list_groups = ConfluentServices.get_all_group_names()
        list_aggregator = ['ssl_enabled', 'rbac_enabled', 'rbac_enabled_public_pem_path',
                           'ssl_keystore_alias', 'ssl_keystore_key_password', 'ssl_keystore_store_password',
                           'ssl_mutual_auth_enabled', 'ssl_provided_keystore_and_truststore',
                           'ssl_provided_keystore_and_truststore_remote_src', 'ssl_truststore_ca_cert_alias',
                           'ssl_truststore_password']

        # check if the given var:value is defined under vars for all component group
        for item in list_aggregator:
            value = None
            aggregate = False
            for group in list_groups:
                aggregate = True
                if group in inventory_data:
                    group_vars = inventory_data[group]['vars']
                    if item not in group_vars:
                        aggregate = False
                        break
                    if value is None:
                        value = group_vars[item]
                    else:
                        if group_vars[item] != value:
                            aggregate = False
                            break
            # aggregate the var:value, remove from all groups and bring under all:vars:
            if aggregate is True:
                inventory_data['all']['vars'][item] = value
                for group in list_groups:
                    if group in inventory_data:
                        del inventory_data[group]['vars'][item]

    def typecast(inventory_data) -> dict:
        for values in InventorySanitizer.nested_dict_values_iterator(inventory_data):
            pass

    def nested_dict_values_iterator(dict_obj):
        ''' This function accepts a nested dictionary as argument
            and iterate over all values of nested dictionaries
        '''
        # Iterate over all values of given dictionary
        for key, value in dict_obj.items():
            # Check if value is of dict type
            if isinstance(value, dict):
                # If value is dict then iterate over all its values
                for v in InventorySanitizer.nested_dict_values_iterator(value):
                    yield v
            else:
                # If value is not dict type then yield the value
                if isinstance(value, str) and value.isnumeric():
                    dict_obj[key] = int(value)
                yield value

    @staticmethod
    def sort(inventory_data: dict):
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

        ordered_dict = collections.OrderedDict(inventory_data)

        for group in group_list:
            if group in ordered_dict.keys():
                ordered_dict.move_to_end(group)

        return ordered_dict
