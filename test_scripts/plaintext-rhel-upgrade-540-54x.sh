#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=plaintext-rhel
export START_BRANCH=5.4.0-post
export START_UPGRADE_VERSION=5.4

## Comment out END_BRANCH and set CURRENT_VERSION=true to test upgrading to latest CP version.
export END_BRANCH=5.4.3-post
export CURRENT_VERSION=false

echo "Call upgrade script"
sh ./upgrade.sh