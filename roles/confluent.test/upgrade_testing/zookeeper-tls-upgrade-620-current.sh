#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=zookeeper-tls-rhel
export START_BRANCH=6.1.x
export START_UPGRADE_VERSION=6.1
export CURRENT_VERSION=true

#Add tags to select specific component installation.
export TAG_NAME="-- --tags zookeeper"


## If current version is set to true, will change END_BRANCH to be equal to the latest CP BRANCH.
if [[ $CURRENT_VERSION == true ]]
then
  export END_BRANCH=$(git rev-parse --abbrev-ref HEAD)
fi

## Change to project root
cd ..

## Checkout starting branch
echo "Checking out $START_BRANCH branch"
git checkout $START_BRANCH

## Run Molecule Converge on scenario
echo "Running molecule converge on $SCENARIO_NAME with tags $TAG_NAME"
molecule converge -s $SCENARIO_NAME $TAG_NAME

## Change to base of cp-ansible
cd ../..

## Checkout ending branch
echo "Checkout $END_BRANCH branch"
git checkout $END_BRANCH

echo "Upgrade Zookeeper"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags zookeeper

## Destroy Infrastructure
cd roles/confluent.test
molecule destroy -s $SCENARIO_NAME
