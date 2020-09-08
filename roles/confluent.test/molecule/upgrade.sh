#!/bin/bash
cd ../../..

scenario_name=$1

echo "Upgrading Zookeeper"
ansible-playbook -i ~/.cache/molecule/confluent.test/$scenario_name/inventory upgrade_zookeeper.yml

echo "Upgrading Kafka"
ansible-playbook -i ~/.cache/molecule/confluent.test/$scenario_name/inventory upgrade_kafka_broker.yml -e kafka_broker_upgrade_start_version=5.4

echo "Upgrading Schema Regsitry"
ansible-playbook -i ~/.cache/molecule/confluent.test/$scenario_name/inventory upgrade_schema_registry.yml

echo "Upgrading Connect"
ansible-playbook -i ~/.cache/molecule/confluent.test/$scenario_name/inventory upgrade_kafka_connect.yml

echo "Upgrading Rest Proxy"
ansible-playbook -i ~/.cache/molecule/confluent.test/$scenario_name/inventory upgrade_kafka_rest.yml

echo "Upgrading KSQL"
ansible-playbook -i ~/.cache/molecule/confluent.test/$scenario_name/inventory upgrade_ksql.yml

echo "Upgrading Control Center"
ansible-playbook -i ~/.cache/molecule/confluent.test/$scenario_name/inventory upgrade_control_center.yml
