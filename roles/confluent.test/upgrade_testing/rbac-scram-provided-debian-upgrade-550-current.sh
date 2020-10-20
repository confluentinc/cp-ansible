#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=rbac-scram-provided-debian
export START_BRANCH=upgrade_testing
export END_BRANCH=6.0.0-post
export START_UPGRADE_VERSION=5.5
export END_UPGRADE_VERSION=6.0

echo "Call upgrade script"

sh ./upgrade.sh
