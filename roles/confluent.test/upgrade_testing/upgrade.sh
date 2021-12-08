#!/bin/bash

set -e

## Variables

## If current version is set to true, will change END_BRANCH to be equal to the latest CP BRANCH.
if [[ $CURRENT_VERSION == true ]]
then
  export END_BRANCH=$(git rev-parse --abbrev-ref HEAD)
fi

export KSQL_INVALID_VERSION=5.4

## Change to project root
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


## With the 6.2.x release, we have removed upgrade playbooks and now handle everything via reconfiguration.  We've added an if statement so that
## this single script can handle all scenarios.
##
## With the 7.0.x release the pathing for ansible cache has changed thus we have added an additional 

if [[ $UPGRADE_PLAYBOOK == false ]] || [[$POST_70 == true ]]
then

## Upgrade Zookeeper via reconfiguration
echo "Upgrade Zookeeper"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags zookeeper

## Upgrade Brokers via reconfiguration
echo "Upgrade Kafka Brokers"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags kafka_broker

## Upgrade Schema Registry via reconfiguration
echo "Upgrade Schema Registry"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags schema_registry

## Upgrade Kafka Connect via reconfiguration
echo "Upgrade Kafka Connect"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags kafka_connect

## Upgrade KSQL via reconfiguration
if (( ${KSQL_INVALID_VERSION%%.*} < ${START_UPGRADE_VERSION%%.*} || ( ${KSQL_INVALID_VERSION%%.*} == ${START_UPGRADE_VERSION%%.*} && ${KSQL_INVALID_VERSION##*.} < ${START_UPGRADE_VERSION##*.} ) )) ; then
echo "Upgrade KSQLDB"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags ksql
fi

## Upgrade Kafka Rest
echo "Upgrade Kafka Rest"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i /.cache/molecule/platform/$SCENARIO_NAME/inventory ansible_inventory.yml --tags kafka_rest

## Upgrade Control Center via reconfiguration
echo "Upgrade Control Center"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory ansible_inventory.yml --tags control_center

## Upgrade Kafka Broker Log format via reconfiguration
# echo "Upgrade Kafka Broker Log Format"

elif [[ $UPGRADE_PLAYBOOK == false ]] || [[$POST_70 == false ]]
then
## Upgrade Zookeeper via reconfiguration
echo "Upgrade Zookeeper"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags zookeeper

## Upgrade Brokers via reconfiguration
echo "Upgrade Kafka Brokers"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags kafka_broker

## Upgrade Schema Registry via reconfiguration
echo "Upgrade Schema Registry"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags schema_registry

## Upgrade Kafka Connect via reconfiguration
echo "Upgrade Kafka Connect"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags kafka_connect

## Upgrade KSQL via reconfiguration
if (( ${KSQL_INVALID_VERSION%%.*} < ${START_UPGRADE_VERSION%%.*} || ( ${KSQL_INVALID_VERSION%%.*} == ${START_UPGRADE_VERSION%%.*} && ${KSQL_INVALID_VERSION##*.} < ${START_UPGRADE_VERSION##*.} ) )) ; then
echo "Upgrade KSQLDB"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags ksql
fi

## Upgrade Kafka Rest
echo "Upgrade Kafka Rest"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i /.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags kafka_rest

## Upgrade Control Center via reconfiguration
echo "Upgrade Control Center"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags control_center

## Upgrade Kafka Broker Log format via reconfiguration
# echo "Upgrade Kafka Broker Log Format"

else

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
if [[ $ADMIN_API == true ]]
then
  echo "Configure Kafka Admin API"
  ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_broker_rest_configuration.yml
fi
fi

## Destroy Infrastructure
cd roles/confluent.test
molecule destroy -s $SCENARIO_NAME
