#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=rbac-scram-custom-rhel
export START_BRANCH=5.5.0-post
export START_UPGRADE_VERSION=5.5

## Comment out END_BRANCH and set CURRENT_VERSION=true to test upgrading to latest CP version.
export END_BRANCH=5.5.5-post
export CURRENT_VERSION=false

echo "Call upgrade script"
sh ./upgrade.sh