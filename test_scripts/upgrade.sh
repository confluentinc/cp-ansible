#!/bin/bash

set -e

## Variables

## If current version is set to true, will change END_BRANCH to be equal to the latest CP BRANCH.
if [[ $CURRENT_VERSION == true ]]
then
  export END_BRANCH=$(git rev-parse --abbrev-ref HEAD)
fi

if [[ $START_BRANCH == 7* ]]
then
  export MOLECULE_DIR=platform
else
  export MOLECULE_DIR=confluent.test
fi

export KSQL_INVALID_VERSION=5.4

## Change to project root
cd ..

## Checkout starting branch
echo "Checking out $START_BRANCH branch"
git checkout $START_BRANCH

## Change to molecule directory on pre 7.0 branches

cd roles/confluent.test/

## Run Molecule Converge on scenario
echo "Running molecule converge on $SCENARIO_NAME"
molecule converge -s $SCENARIO_NAME

## Change to base of cp-ansible
cd ../..

## Checkout ending branch
echo "Checkout $END_BRANCH branch"
git checkout $END_BRANCH

## With 7.0.x onwards, cp-ansible is packaged as an ansible collection and hence we need to specify collection path to enable running playbooks
## https://docs.ansible.com/ansible/latest/reference_appendices/config.html#collections-paths
export ANSIBLE_COLLECTIONS_PATH=../../

## With the 6.2.x release, we have removed upgrade playbooks and now handle everything via reconfiguration.  We've added an if statement so that
## this single script can handle all scenarios.

if [[ $UPGRADE_PLAYBOOK == false ]]
then

## Upgrade Zookeeper via reconfiguration
echo "Upgrade Zookeeper"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/$MOLECULE_DIR/$SCENARIO_NAME/inventory confluent.platform.all --tags zookeeper

## Upgrade Brokers via reconfiguration
echo "Upgrade Kafka Brokers"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/$MOLECULE_DIR/$SCENARIO_NAME/inventory confluent.platform.all --tags kafka_broker

## Upgrade Schema Registry via reconfiguration
echo "Upgrade Schema Registry"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/$MOLECULE_DIR/$SCENARIO_NAME/inventory confluent.platform.all --tags schema_registry

## Upgrade Kafka Connect via reconfiguration
echo "Upgrade Kafka Connect"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/$MOLECULE_DIR/$SCENARIO_NAME/inventory confluent.platform.all --tags kafka_connect

## Upgrade KSQL via reconfiguration
if (( ${KSQL_INVALID_VERSION%%.*} < ${START_UPGRADE_VERSION%%.*} || ( ${KSQL_INVALID_VERSION%%.*} == ${START_UPGRADE_VERSION%%.*} && ${KSQL_INVALID_VERSION##*.} < ${START_UPGRADE_VERSION##*.} ) )) ; then
echo "Upgrade KSQLDB"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/$MOLECULE_DIR/$SCENARIO_NAME/inventory confluent.platform.all --tags ksql
fi

## Upgrade Kafka Rest
echo "Upgrade Kafka Rest"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i /.cache/molecule/$MOLECULE_DIR/$SCENARIO_NAME/inventory confluent.platform.all --tags kafka_rest

## Upgrade Control Center via reconfiguration
echo "Upgrade Control Center"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/$MOLECULE_DIR/$SCENARIO_NAME/inventory confluent.platform.all --tags control_center

## Upgrade Kafka Broker Log format via reconfiguration
# echo "Upgrade Kafka Broker Log Format"

## Destroy Infrastructure
molecule destroy -s $SCENARIO_NAME

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

## Destroy Infrastructure
cd roles/confluent.test
molecule destroy -s $SCENARIO_NAME

fi
