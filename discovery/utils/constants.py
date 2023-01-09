from enum import Enum

DEFAULT_KEY = "Default"
"""
        "confluent-schema-registry-plugins",
        "confluent-rest-utils",
        "confluent-control-center",
        "confluent-metadata-service",
        "confluent-telemetry",
        "confluent-ksqldb",
        "confluent-rebalancer",
        "confluent-kafka-connect-replicator",
        "confluent-kafka-rest",
        "confluent-security",
        "confluent-server-rest",
        "confluent-schema-registry",
        "confluent-control-center-fe",
        "confluent-server",
        "confluent-ce-kafka-http-server",
        "confluent-common",
        "confluent-hub-client"

"""


class ConfluentServices(Enum):
    ZOOKEEPER = {
        "name": "confluent-zookeeper.service",
        "group": "zookeeper",
        "packages": ["confluent-common"]
    }
    SCHEMA_REGISTRY = {
        "name": "confluent-schema-registry.service",
        "group": "schema_registry",
        "packages": ["confluent-schema-registry", "confluent-schema-registry-plugins"]
    }
    KAFKA_BROKER = {
        "name": "confluent-server.service",
        "group": "kafka_broker",
        "packages": ["confluent-server", "confluent-rebalancer", "confluent-metadata-service"]
    }
    KAFKA_CONNECT = {
        "name": "confluent-kafka-connect.service",
        "group": "kafka_connect",
        "packages": ["confluent-hub-client"]
    }
    KAFKA_REPLICATOR = {
        "name": "kafka-connect-replicator.service",
        "group": "kafka_connect_replicator",
        "packages": ["confluent-kafka-connect-replicator", "confluent-hub-client"]
    }
    KSQL = {
        "name": "confluent-ksqldb.service",
        "group": "ksql",
        "packages": ["confluent-ksqldb"]
    }
    KAFKA_REST = {
        "name": "confluent-kafka-rest.service",
        "group": "kafka_rest",
        "packages": ["confluent-kafka-rest", "confluent-server-rest", "confluent-rest-utils"]
    }
    CONTROL_CENTER = {
        "name": "confluent-control-center.service",
        "group": "control_center",
        "packages": ["confluent-control-center-fe", "confluent-control-center"]
    }

    @staticmethod
    def get_all_service_names() -> set:

        variables = set()
        for key, value in ConfluentServices.__members__.items():
            variables.add(value.value.get("name"))
        return variables

    @staticmethod
    def get_service_key_mappings() -> dict:
        variables = dict()
        for key, value in ConfluentServices.__members__.items():
            variables[value.value.get("name")] = key
        return variables

    @staticmethod
    def get_key_service_mappings() -> dict:
        variables = dict()
        for key, value in ConfluentServices.__members__.items():
            variables[key] = value.value.get("name")
        return variables

    @staticmethod
    def get_service_key_value(service_name: str) -> str:
        for key, value in ConfluentServices.__members__.items():
            if value.value.get("name") == service_name:
                return key

    @staticmethod
    def get_group_by_key(key_name: str) -> str:
        for key, value in ConfluentServices.__members__.items():
            if key == key_name:
                return value.value.get("group")

    @staticmethod
    def get_all_group_names() -> set:
        groups = set()
        for key, value in ConfluentServices.__members__.items():
            groups.add(value.value.get("group"))
        return groups


if __name__ == "__main__":
    print(ConfluentServices.get_key_service_mappings())
