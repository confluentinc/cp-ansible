#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=mtls-customcerts-rhel
export START_BRANCH=6.0.1-post
export START_UPGRADE_VERSION=6.0

echo "Call upgrade script"
sh ./upgrade.sh
