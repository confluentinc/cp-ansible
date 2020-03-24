#!/bin/bash

set -e

for d in roles/* ; do
    pushd $d
    if [ -d "molecule" ]
    then
        echo "Running Molecule Test for Role: $d"
        molecule test --all
    fi
    popd
done
