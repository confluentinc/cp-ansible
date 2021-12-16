#!/bin/bash

set -e

## Variables
export END_BRANCH=$(git rev-parse --abbrev-ref HEAD)
export KSQL_INVALID_VERSION=5.4

## Change to molecule directory
cd ..

## Checkout starting branch
echo "Checking out $START_BRANCH branch"
git checkout $START_BRANCH

## Run Molecule Converge on scenario
echo "Running molecule converge on $SCENARIO_NAME"
molecule converge -s $SCENARIO_NAME

## Change to base of cp-ansible
cd ../..

## Checkout ending branch
echo "Checkout $END_BRANCH branch"
git checkout $END_BRANCH

## Upgrade Zookeeper
echo "Upgrade Zookeeper"
ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_zookeeper.yml

## Upgrade kafka Brokers
echo "Upgrade Kafka Brokers"
ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_broker.yml -e kafka_broker_upgrade_start_version=$START_UPGRADE_VERSION

## Upgrade Schema Restiry
echo "Upgrade Schema Registry"
ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_schema_registry.yml

## Upgrade Kafka Connect
echo "Upgrade Kafka Connect"
ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_connect.yml

## Upgrade KSQL
if (( ${KSQL_INVALID_VERSION%%.*} < ${START_UPGRADE_VERSION%%.*} || ( ${KSQL_INVALID_VERSION%%.*} == ${START_UPGRADE_VERSION%%.*} && ${KSQL_INVALID_VERSION##*.} < ${START_UPGRADE_VERSION##*.} ) )) ; then
    echo "Upgrade KSQL"
    ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_ksql.yml
fi

## Upgrade Kafka Rest
echo "Upgrade Kafka Rest"
ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_rest.yml

## Upgrade Control Center
echo "Upgrade Control Center"
ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_control_center.yml

## Upgrade Kafka Broker Log Format
echo "Upgrade Kafka Broker Log Format"
ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_broker_log_format.yml

## Configure Kafka Admin API
echo "Configure Kafka Admin API"
ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_broker_rest_configuration.yml

## Destroy Infrastructure
cd roles/confluent.test
molecule destroy -s $SCENARIO_NAME
