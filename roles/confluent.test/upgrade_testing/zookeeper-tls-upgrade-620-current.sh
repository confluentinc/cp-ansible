#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=zookeeper-tls-rhel
export START_BRANCH=6.1.x
export START_UPGRADE_VERSION=6.1

export POST_70=false
export CURRENT_VERSION=true

## If upgrading from 6.2.0 or later, this should be false as upgrade playbooks no longer exist.  Upgrades are handled via reconfiguration.
export UPGRADE_PLAYBOOK=false

## Set to true if testing 6.0.0 or later.  Will run admin API upgrade.
export ADMIN_API=false

echo "Call upgrade script"
sh ./upgrade.sh