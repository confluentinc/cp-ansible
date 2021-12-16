#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=zookeeper-tls-rhel
export START_BRANCH=6.1.x
export START_UPGRADE_VERSION=6.1

export POST_70=false
export CURRENT_VERSION=true

#Add tags to select specific component installation.
export TAGS=true
export TAG_NAME="-- --tags zookeeper"

## If upgrading from 6.2.0 or later, this should be false as upgrade playbooks no longer exist.  Upgrades are handled via reconfiguration.
export UPGRADE_PLAYBOOK=false

## Set to true if testing 6.0.0 or later.  Will run admin API upgrade.
export ADMIN_API=false

# echo "Call upgrade script"
# sh ./upgrade.sh

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
if [[ $TAGS == true ]]
then
echo "Running molecule converge on $SCENARIO_NAME with tags $TAG_NAME"
molecule converge -s $SCENARIO_NAME $TAG_NAME
else
echo "Running molecule converge on $SCENARIO_NAME"
molecule converge -s $SCENARIO_NAME
fi

## Change to base of cp-ansible
cd ../..

## Checkout ending branch
echo "Checkout $END_BRANCH branch"
git checkout $END_BRANCH

echo "Upgrade Zookeeper"
ansible-playbook --extra-vars "deployment_strategy: rolling" -i ~/.cache/molecule/platform/$SCENARIO_NAME/inventory all.yml --tags zookeeper
