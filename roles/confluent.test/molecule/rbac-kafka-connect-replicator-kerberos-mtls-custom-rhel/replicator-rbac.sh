#!/bin/bash

set -e

## Variables

export SCENARIO_NAME=rbac-kafka-connect-replicator-kerberos-mtls-custom-rhel


## Phase 1: Setup two clusters with RBAC enabled

cd ../..

### Run Molecule Converge on scenario to setup two clusters with RBAC
echo "Running molecule converge on $SCENARIO_NAME"
molecule --debug converge -s $SCENARIO_NAME|tee test1.txt

## Phase 2: Retrieve Environment information 

### Get Cluster UUID from MDS
echo "Retrieving ClusterID"
curl -vvv -u mds:password http://localhost:8090/kafka/v3/clusters 


## update inventory file for replicator with uuid

### Print clusterID of Cluster1 into inventory file
echo "Print MDS Cluster UUID in Inventory file"
awk '/master.mplayer.com/ { print; print "new line"; next }1'


## Phase 3: Install Replicator with updated environment information