# How to test

Starting with CP-Ansible 5.5.0, we have included testing via the [Molecule](https://molecule.readthedocs.io/en/latest/) framework, and strongly advise it's usage before submitting a Pull Request.

## Prerequisites

1. Python3 installed with PIP
2. Docker installed
3. Install the Molecule and Docker libraries

```pip install molecule docker```

Note: We recommend increasing your docker memory to at least 20GB of RAM and your CPU count to 10.

## Using Molecule

The following is a list of the most common commands used with Molecule.

### Running a role

Molecule allows for testing a role and will live inside a role's directory in a sub directory named molecule. Currently, most tests reside inside a special role called confluent.test in sub directories which use the following naming convention:

```<functionality tested>-<security mechanism>-<OS>```

To get a list of the scenarios:

```ls roles/confluent.test/molecule```

To the run scenarios: 

```cd roles/confluent.test```
```molecule converge -s <scenario name>```

#### RBAC Roles

With CP-Ansible 6.0, we have introduced scenarios for RBAC with a remote MDS installation.  For these scenarios to work, you will need to run two individual scenarios which work in tandem.  Order of operations for running the scenarios is import.

You will first need to start a scenario which setups up cluster1 with the minimum configuration for the Meta Data Server to be running on the Brokers.

The naming conventions for these scenarios are as follows:

```rbac-mds-<functionality tested>-<security mechanism>-<OS>```

Once Cluster1 has successfully started, you will then need to run a second scenario to setup cluster2.  Cluster2 will refer to cluster1 for it's Meta Data Server.

The naming conventions for these scenarios are as follows:

```rbac-centralized-mds-<functionality tested>-<security mechanism>-<OS>```

Note: The scenarios for cluster1 only setup the minimum viable configuration for MDS to run, the do not setup additional components, such as Schema Registry or Kafka Connect.  Scenarios for cluster2, setup all components.

### SSHing into a container

Each docker container is named inside the molecule.yml file, copy the name and run:

```molecule login -s <scenario name> -h <container-name>```

### Running Role Tests

To run the test cases, which are defined in the verify.yml playbooks, run:

```molecule verify -s <scenario name>```

### Destroying the Containers

Simply run:

```molecule destroy -s <scenario name>```

## Creating Scenarios

Within ```roles/confluent.test/molecule``` you can find a series of directories, which can be referred to as scenarios. Use a scenario as an inventory file, you can configure docker containers, ansible groups, variables, etc. When developing new features for the role you can create a new scenario simply by duplicating the default one and customizing. Edit the verify.yml to have test assertions for your scenario.

More details on building scenarios can be found [here](https://molecule.readthedocs.io/en/latest/getting-started.html?highlight=scenarios#molecule-scenarios).

## Running a full test suite

To confirm that your code does not break any tests make sure to test all scenarios for a role with:
```
molecule test --all
```