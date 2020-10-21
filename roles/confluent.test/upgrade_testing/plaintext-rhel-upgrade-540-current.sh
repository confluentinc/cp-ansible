#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=plaintext-rhel
export START_BRANCH=5.4.0-post
export END_BRANCH=upgrade_testing
export START_UPGRADE_VERSION=5.4
export END_UPGRADE_VERSION=6.0

echo "Call upgrade script"
sh ./upgrade.sh
