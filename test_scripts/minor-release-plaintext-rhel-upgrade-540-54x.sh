#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=plaintext-rhel
export START_BRANCH=5.4.0-post
export START_UPGRADE_VERSION=5.4

## Comment out END_BRANCH and set CURRENT_VERSION=true to test upgrading to latest CP version.
export END_BRANCH=5.4.5-post
export CURRENT_VERSION=false

## Set to true if testing 6.0.0 or later.  Will run admin API upgrade.
export ADMIN_API=false

echo "Call upgrade script"
sh ./upgrade.sh