#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=mtls-customcerts-rhel
export START_BRANCH=5.4.0-post
export START_UPGRADE_VERSION=5.4

echo "Call upgrade script"
sh ./upgrade.sh
