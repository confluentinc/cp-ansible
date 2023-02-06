from discovery.utils.utils import InputContext, singleton


class ServiceData:
    name: str
    group: str
    packages: list

    def __init__(self, name: str, group: str, packages: list):
        self.name = name
        self.group = group
        self.packages = packages


class ConfluentServices:
    service_overrides: dict = {}

    def __init__(self, input_context: InputContext):
        self.service_overrides = input_context.service_overrides

    def ZOOKEEPER(self) -> ServiceData:
        return ServiceData(
            name=self.service_overrides.get("zookeeper_service_name", "confluent-zookeeper.service"),
            group="zookeeper",
            packages=["confluent-common"])

    def SCHEMA_REGISTRY(self) -> ServiceData:
        return ServiceData(
            name=self.service_overrides.get("schema_registry_service_name", "confluent-schema-registry.service"),
            group="schema_registry",
            packages=["confluent-schema-registry", "confluent-schema-registry-plugins"]
        )

    def KAFKA_BROKER(self) -> ServiceData:
        return ServiceData(
            name=self.service_overrides.get("kafka_broker_service_name", "confluent-server.service"),
            group="kafka_broker",
            packages=["confluent-server", "confluent-rebalancer", "confluent-metadata-service"]
        )

    def KAFKA_CONNECT(self) -> ServiceData:
        return ServiceData(
            name=self.service_overrides.get("kafka_connect_service_name", "confluent-kafka-connect.service"),
            group="kafka_connect",
            packages=["confluent-hub-client"]
        )

    def KAFKA_REPLICATOR(self) -> ServiceData:
        return ServiceData(
            name=self.service_overrides.get("kafka_connect_replicator_service_name",
                                            "kafka-connect-replicator.service"),
            group="kafka_connect_replicator",
            packages=["confluent-kafka-connect-replicator", "confluent-hub-client"]
        )

    def KSQL(self) -> ServiceData:
        return ServiceData(
            name=self.service_overrides.get("ksql_service_name", "confluent-ksqldb.service"),
            group="ksql",
            packages=["confluent-ksqldb"])

    def KAFKA_REST(self) -> ServiceData:
        return ServiceData(
            name=self.service_overrides.get("kafka_rest_service_name", "confluent-kafka-rest.service"),
            group="kafka_rest",
            packages=["confluent-kafka-rest", "confluent-server-rest", "confluent-rest-utils"]
        )

    def CONTROL_CENTER(self) -> ServiceData:
        return ServiceData(
            name=self.service_overrides.get("control_center_service_name", "confluent-control-center.service"),
            group="control_center",
            packages=["confluent-control-center-fe", "confluent-control-center"]
        )

    def get_all_service_names(self) -> set:
        variables = set()
        clazz = ConfluentServices
        for key, value in vars(ConfluentServices).items():
            if callable(getattr(clazz, key)) and key.isupper():
                func = getattr(clazz, key)
                result = func(self)
                variables.add(result.name)
        return variables

    def get_service_group_mapping(self) -> dict:
        variables = dict()
        clazz = ConfluentServices
        for key, value in vars(ConfluentServices).items():
            if callable(getattr(clazz, key)) and key.isupper():
                func = getattr(clazz, key)
                result = func(self)
                variables[result.name] = result.group
        return variables

    def get_group_service_mapping(self) -> dict:
        variables = dict()
        clazz = ConfluentServices
        for key, value in vars(ConfluentServices).items():
            if callable(getattr(clazz, key)) and key.isupper():
                func = getattr(clazz, key)
                result = func(self)
                variables[result.group] = result.name
        return variables

    def get_all_group_names(self) -> set:
        variables = set()
        clazz = ConfluentServices
        for key, value in vars(ConfluentServices).items():
            if callable(getattr(clazz, key)) and key.isupper():
                func = getattr(clazz, key)
                result = func(self)
                variables.add(result.group)
        return variables

    def get_group_name(self, service_name: str) -> str:
        clazz = ConfluentServices
        for key, value in vars(ConfluentServices).items():
            if callable(getattr(clazz, key)) and key.isupper():
                func = getattr(clazz, key)
                result = func(self)
                if result.name == service_name:
                    return result.group
        return None

    def get_service_name(self, group_name: str) -> str:
        clazz = ConfluentServices
        for key, value in vars(ConfluentServices).items():
            if callable(getattr(clazz, key)) and key.isupper():
                func = getattr(clazz, key)
                result = func(self)
                if result.group == group_name:
                    return result.name
        return None
