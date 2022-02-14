#!/bin/bash

set -e

## Variables

## If current version is set to true, will change END_BRANCH to be equal to the latest CP BRANCH.
if [[ $CURRENT_VERSION == true ]]
then
  export END_BRANCH=$(git rev-parse --abbrev-ref HEAD)
fi

export START_UPGRADE_VERSION=${START_BRANCH:0:3}
export END_UPGRADE_VERSION=${END_BRANCH:0:3}

if [[ $START_BRANCH > 7* ]]
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
if [[ $START_BRANCH < 7* ]]
then
  cd roles/confluent.test/
fi

## Run Molecule Converge on scenario
echo "Running molecule converge on $SCENARIO_NAME"
molecule converge -s $SCENARIO_NAME

## Change to base of cp-ansible
if [[ $START_BRANCH < 7* ]]
then
  cd ../..
fi

## Checkout ending branch
echo "Checkout $END_BRANCH branch"
git checkout $END_BRANCH

## With 7.0.x onwards, cp-ansible is packaged as an ansible collection and hence we need to specify collection path to enable running playbooks
## https://docs.ansible.com/ansible/latest/reference_appendices/config.html#collections-paths
export ANSIBLE_COLLECTIONS_PATH=../../

## For 6.2.x onwards, this alias function will be used for running the upgrades
run_playbook_62x+() {
  if [[ $1 == 6.[2-9].* ]]
  then
    ansible-playbook --extra-vars "deployment_strategy=rolling" -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory all.yml --tags "$2" ;
  else
    ansible-playbook --extra-vars "deployment_strategy=rolling" -i ~/.cache/molecule/$MOLECULE_DIR/$SCENARIO_NAME/inventory confluent.platform.all --tags "$2" ;
  fi
}

## For branches till 6.1.x, this alias function will be used for running the upgrades
run_playbook_61x-() { ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory $1 ; }


## For 6.2.x onwards, we don't use upgrade playbooks
if [[ $END_BRANCH =~ 6.[2-9].*|[7-9].[0-9].* ]]

then

## Upgrade Zookeeper via reconfiguration
echo "Upgrade Zookeeper"
run_playbook_62x+ $END_BRANCH zookeeper

## Upgrade Brokers via reconfiguration
echo "Upgrade Kafka Brokers"
ansible-playbook -i ~/.cache/molecule/$MOLECULE_DIR/$SCENARIO_NAME/inventory upgrade_broker_props.yml --tags first -e kafka_broker_upgrade_start_version=$START_UPGRADE_VERSION
run_playbook_62x+ $END_BRANCH kafka_broker
ansible-playbook -i ~/.cache/molecule/$MOLECULE_DIR/$SCENARIO_NAME/inventory upgrade_broker_props.yml --tags second -e kafka_broker_upgrade_end_version=$END_UPGRADE_VERSION

## Upgrade Schema Registry via reconfiguration
echo "Upgrade Schema Registry"
run_playbook_62x+ $END_BRANCH schema_registry

## Upgrade Kafka Connect via reconfiguration
echo "Upgrade Kafka Connect"
run_playbook_62x+ $END_BRANCH kafka_connect

## Upgrade KSQL via reconfiguration
if (( ${KSQL_INVALID_VERSION%%.*} < ${START_UPGRADE_VERSION%%.*} || ( ${KSQL_INVALID_VERSION%%.*} == ${START_UPGRADE_VERSION%%.*} && ${KSQL_INVALID_VERSION##*.} < ${START_UPGRADE_VERSION##*.} ) )) ; then
echo "Upgrade KSQLDB"
run_playbook_62x+ $END_BRANCH ksql
fi

## Upgrade Kafka Rest
echo "Upgrade Kafka Rest"
run_playbook_62x+ $END_BRANCH kafka_rest

## Upgrade Control Center via reconfiguration
echo "Upgrade Control Center"
run_playbook_62x+ $END_BRANCH control_center

## Upgrade Kafka Broker Log format via reconfiguration
echo "Upgrade Kafka Broker Log Format"
ansible-playbook -i ~/.cache/molecule/$MOLECULE_DIR/$SCENARIO_NAME/inventory upgrade_broker_props.yml --tags second -e kafka_broker_upgrade_end_version=$END_UPGRADE_VERSION

## Destroy Infrastructure, change dir if 6.*
if [[ $END_BRANCH == 6.* ]]
then
  cd roles/confluent.test
  molecule destroy -s $SCENARIO_NAME
else 
  molecule destroy -s $SCENARIO_NAME
fi

# For branches till 6.1.x, we use upgrade playbooks
else

## Upgrade Zookeeper
echo "Upgrade Zookeeper"
run_playbook_61x- upgrade_zookeeper.yml

## Upgrade kafka Brokers
echo "Upgrade Kafka Brokers"
ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory upgrade_kafka_broker.yml -e kafka_broker_upgrade_start_version=$START_UPGRADE_VERSION

## Configure Kafka Admin API
if [[ $END_BRANCH == 6.0.* ]]
then
  echo "Configure Kafka Admin API"
  run_playbook_61x- upgrade_kafka_broker_rest_configuration.yml
fi

## Upgrade Schema Restiry
echo "Upgrade Schema Registry"
run_playbook_61x- upgrade_schema_registry.yml

## Upgrade Kafka Connect
echo "Upgrade Kafka Connect"
run_playbook_61x- upgrade_kafka_connect.yml

## Upgrade KSQL
if (( ${KSQL_INVALID_VERSION%%.*} < ${START_UPGRADE_VERSION%%.*} || ( ${KSQL_INVALID_VERSION%%.*} == ${START_UPGRADE_VERSION%%.*} && ${KSQL_INVALID_VERSION##*.} < ${START_UPGRADE_VERSION##*.} ) )) ; then
  echo "Upgrade KSQL"
  run_playbook_61x- upgrade_ksql.yml
fi

## Upgrade Kafka Rest
echo "Upgrade Kafka Rest"
run_playbook_61x- upgrade_kafka_rest.yml

## Upgrade Control Center
echo "Upgrade Control Center"
run_playbook_61x- upgrade_control_center.yml

## Upgrade Kafka Broker Log Format
echo "Upgrade Kafka Broker Log Format"
run_playbook_61x- upgrade_kafka_broker_log_format.yml -e kafka_broker_upgrade_end_version=$END_UPGRADE_VERSION

## Destroy Infrastructure
cd roles/confluent.test
molecule destroy -s $SCENARIO_NAME

fi
