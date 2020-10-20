#!/bin/bash

set -e


## Checkout starting branch

echo "Checking out $START_BRANCH branch"
git checkout $START_BRANCH

## Run Molecule Converge on scenario

echo "Running molecule converge on $SCENARIO_NAME"
(cd ../ && molecule converge -s $SCENARIO_NAME)

## Checkout ending branch

echo "Checkout $END_BRANCH branch"
(cd ../ && git checkout $END_BRANCH)

## Upgrade Zookeeper

echo "Upgrade Zookeeper"
(cd ../../../ && ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_zookeeper.yml -e kafka_broker_upgrade_start_version=$START_UPGRADE_VERSION)

## Upgrade kafka Brokers

echo "Upgrade Kafka Brokers"
(cd ../../../ && ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_broker.yml -e kafka_broker_upgrade_start_version=$START_UPGRADE_VERSION)

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