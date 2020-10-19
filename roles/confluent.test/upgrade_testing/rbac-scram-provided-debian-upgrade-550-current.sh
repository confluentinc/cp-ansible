#!/bin/bash

set -e

## variables

SCENARIO_NAME=rbac-scram-provided-debian

## Checkout 5.5.0-post branch

echo "Checking out 5.5.0-post branch"
git checkout 5.5.0-post

## Run Molecule Converge on 5.5.0-post

echo "Running molecule converge"
(cd ../ && molecule converge -s rbac-scram-provided-debian)

## Checkout 6.0.0-post branch

echo "Checkout 6.0.0-post branch"
(cd ../ && git checkout 6.0.0-post)

## Upgrade Zookeeper

echo "Upgrade Zookeeper"
(cd ../../../ && ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_zookeeper.yml -e kafka_broker_upgrade_start_version=5.5)

## Upgrade kafka Brokers from 5.5.0 to 6.0.0

echo "Upgrade Kafka Brokers"
(cd ../../../ && ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_broker.yml -e kafka_broker_upgrade_start_version=5.5)

## Upgrade Schema Restiry from 5.5.0 to 6.0.0

echo "Upgrade Schema Registry"
(cd ../../../ && ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_schema_registry.yml)

## Upgrade Kafka Connect

echo "Upgrade Kafka Connect"
(cd ../../../ && ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_connect.yml)

## Upgrade KSQL

echo "Upgrade KSQL"
(cd ../../../ && ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_ksql.yml)

## Upgrade Kafka Rest

echo "Upgrade Kafka Rest"
(cd ../../../ && ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_rest.yml)

## Upgrade Control Center

echo "Upgrade Control Center"
(cd ../../../ && ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_control_center.yml)

## Upgrade Kafka Broker Log Format

echo "Upgrade Kafka Broker Log Format"
(cd ../../../ && ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_broker_log_format.yml)