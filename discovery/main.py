from discovery.service.service import ServicePropertyBuilder
from discovery.system.system import SystemPropertyBuilder
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import Arguments, Logger, InputContext

logger = Logger.get_logger()


def build_system_properties(input_context: InputContext, inventory: CPInventoryManager):
    system_property_builder = SystemPropertyBuilder(input_context, inventory)

    system_property_builder. \
        with_service_host_mappings(). \
        with_ansible_variables(). \
        with_installation_method()


def build_service_properties(input_context: InputContext, inventory: CPInventoryManager):
    service_property_builder = ServicePropertyBuilder(input_context, inventory)
    service_property_builder.\
        with_zookeeper_properties().\
        with_kafka_broker_properties().\
        with_mds_properties().\
        with_schema_registry_properties().\
        with_kafka_rest_properties().\
        with_ksql_properties().\
        with_connect_properties().\
        with_replicator_properties().\
        with_control_center_properties()


def main():
    # Parse the input variables and build input context
    args = Arguments.parse_arguments()
    Arguments.validate_args(args)
    input_context = Arguments.get_input_context(args)

    # Create inventory placeholder and fill with system and service properties
    inventory = CPInventoryManager(input_context)

    build_system_properties(input_context, inventory)
    build_service_properties(input_context, inventory)

    # Write final inventory file
    data = inventory.get_inventory_data()
    inventory.put_inventory_data(data)


if __name__ == "__main__":
    main()
