# Testing CP-Ansible

Each role has Molecule configuration which enable fast and easy development and testing with Docker containers.

## Prerequisites

Make sure Docker is running and install these python libraries:
```
pip install molecule docker
```

## Using Molecule

Molecule comes with a CLI. Below are instructions for a few of its commands:

### Running a role

Each role has a default scenario in it already so running a role locally is as easy as:
```
cd roles/<role-name>
molecule converge
```

### SSHing into a container

Each docker container is named inside the molecule.yml file, copy the name and run:
```
molecule login -h <container-name>
```

### Running Tests

To run the test cases, which are defined in the verify.yml playbooks, run:
```
molecule verify
```

### Destroying the Containers

Simply run:
```
molecule destroy
```

## Creating Scenarios

In some roles within the molecule directory you will find multiple subdirectories, which can be referred to as scenarios. Use a scenario as an inventory file, you can configure docker hosts, ansible groups, variables, etc. When developing new features for the role you can create a new scenario simply by duplicating the default one and customizing. Edit the verify.yml to have test assertions for your scenario.

All of the above commands can be run against your scenario, ie:
```
molecule converge -s <scenario-name>
```

## Running a full test suite

To confirm that your code does not break any tests make sure to test all scenarios pass for a role with:
```
molecule test --all
```
