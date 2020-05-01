# How to test

Starting with CP-Ansible 5.5.0, we have included testing via the [Molecule](https://molecule.readthedocs.io/en/latest/) framework, and strongly advise it's usage before submitting a Pull Request.

## Prerequisites

1. Python3 installed with PIP
2. Docker installed
3. Install the Molecule and Docker libraries

```pip install molecule docker```

## Using Molecule

The following is a list of the most common commands used with Molecule.

### Running a role

We have created a ```confluent.test``` role which contains all current scenarios for CP-Ansible under the ```molecule``` directory.  Each scenario named using the following format:

```<functionality tested>-<security mechanism>-<OS>```

To run a role do the following:

```ls roles/confluent.test/molecule```
```cd roles/confluent.test```
```molecule converge <rolename>```


### SSHing into a container

Each docker container is named inside the molecule.yml file, copy the name and run:

```molecule login -h <container-name>```

### Running Role Tests

To run the test cases, which are defined in the verify.yml playbooks, run:

```molecule verify```

### Destroying the Containers

Simply run:

```molecule destroy```

## Creating Scenarios

Within ```roles/confluent.test/molecule``` you can find a series of directories, which can be referred to as scenarios. Use a scenario as an inventory file, you can configure docker containers, ansible groups, variables, etc. When developing new features for the role you can create a new scenario simply by duplicating the default one and customizing. Edit the verify.yml to have test assertions for your scenario.

All of the above commands can be run against your scenario, ie:
```
molecule converge -s <scenario-name>
```

More details on building scenarios can be found [here](https://molecule.readthedocs.io/en/latest/getting-started.html?highlight=scenarios#molecule-scenarios).


## Running a full test suite

To confirm that your code does not break any tests make sure to test all scenarios for a role with:
```
molecule test --all
```