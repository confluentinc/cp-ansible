#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=rbac-scram-custom-rhel
export START_BRANCH=6.2.0-post
export START_UPGRADE_VERSION=6.2

## Comment out END_BRANCH and set CURRENT_VERSION=true to test upgrading to latest CP version.
export END_BRANCH=6.2.1-post
export CURRENT_VERSION=false

## Set to true if testing 6.0.0 or later.  Will run admin API upgrade.
export ADMIN_API=true

echo "Call upgrade script"
sh ./upgrade.sh