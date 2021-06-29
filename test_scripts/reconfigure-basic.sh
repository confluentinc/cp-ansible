#!/bin/bash

set -e

SCENARIO_NAME=plaintext-rhel
cd ..

echo "Running molecule converge on $SCENARIO_NAME"
molecule converge -s $SCENARIO_NAME -- --skip-tags package,kafka_connect,kafka_rest,ksql,control_center

cd ../..
echo "Reconfigure with New Properties"
ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory all.yml --skip-tags package,kafka_connect,kafka_rest,ksql,control_center --extra-vars '{"jmxexporter_enabled":"false","jolokia_enabled":"false","zookeeper_custom_properties":{"this":"that"},"kafka_broker_custom_properties":{"this":"that"},"schema_registry_custom_properties":{"this":"that"}}'

echo "Validate New Properties"
ansible -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory zookeeper -m import_role -a "name=confluent.test tasks_from=check_property.yml" --extra-vars '{"file_path": "/etc/kafka/zookeeper.properties", "property": "this", "expected_value": "that"}'
ansible -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory kafka_broker -m import_role -a "name=confluent.test tasks_from=check_property.yml" --extra-vars '{"file_path": "/etc/kafka/server.properties", "property": "this", "expected_value": "that"}'
ansible -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory schema_registry -m import_role -a "name=confluent.test tasks_from=check_property.yml" --extra-vars '{"file_path": "/etc/schema-registry/schema-registry.properties", "property": "this", "expected_value": "that"}'

echo "Destroy containers"
cd roles/confluent.test
molecule destroy -s $SCENARIO_NAME
