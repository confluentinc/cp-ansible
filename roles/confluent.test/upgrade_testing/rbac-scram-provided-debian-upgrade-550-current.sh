#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=rbac-scram-provided-debian
export START_BRANCH=5.5.0-post
export START_UPGRADE_VERSION=5.5

echo "Call upgrade script"
sh ./upgrade.sh
