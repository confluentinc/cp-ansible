#!/bin/bash

set -e

SCENARIO_NAME=mtls-debian
cd ..

echo "Running molecule converge on $SCENARIO_NAME"
molecule converge -s $SCENARIO_NAME -- --skip-tags package

cd ../..
echo "Reconfigure with New Properties"
ansible-playbook -i ~/.cache/molecule/confluent.test/$SCENARIO_NAME/inventory all.yml --skip-tags package --extra-vars '{"regenerate_keystore_and_truststore":"true"}'


echo "Destroy containers"
cd roles/confluent.test
molecule destroy -s $SCENARIO_NAME
