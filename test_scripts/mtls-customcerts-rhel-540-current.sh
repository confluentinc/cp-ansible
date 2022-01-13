#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=mtls-customcerts-rhel
export START_BRANCH=5.4.0-post
export START_UPGRADE_VERSION=5.4

export CURRENT_VERSION=true

## Set to true if testing 6.0.0 or later.  Will run admin API upgrade.
export ADMIN_API=false

echo "Call upgrade script"
sh ./upgrade.sh
