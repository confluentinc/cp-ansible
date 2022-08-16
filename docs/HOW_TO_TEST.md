# How to test

CP-Ansible's tests use the [Molecule](https://molecule.readthedocs.io/en/latest/) framework, and it is strongly advised to test this way before submitting a Pull Request.

## Prerequisites

1. Python3
2. [Ansible >= 2.11](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installing-ansible-with-pip). Use python3's pip for ansible installation to make sure ansible is not configured with Python2.7:
```
python3 -m pip install --user ansible
```
2. [Docker](https://docs.docker.com/get-docker/) *Note: We recommend increasing your docker memory to at least 20GB of RAM and your CPU count to 10.*
Due to some changes in Docker wrt systemd, the latest versions of Docker won't work with our molecule tests. Docker Desktop version 4.2.0 (having Docker Engine 20.10.10) or ealier should be used. 
3. [Molecule >= 3.3](https://molecule.readthedocs.io/en/latest/installation.html#install). Use python3's pip for installation: 
```
python3 -m pip install --user "molecule[docker,lint]"
```

## Cloning CP-Ansible

CP-Ansible is written as an [Ansible Collection](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html), which requires a rigid directory structure for development. In order for Molecule to succeed in finding custom filters and plugins, cp-ansible must be cloned into an `ansible_collections/confluent/platform` directory. To properly clone cp-ansible, run:

```
git clone https://github.com/confluentinc/cp-ansible.git ansible_collections/confluent/platform
cd ansible_collections/confluent/platform
```

## Using Molecule

The following is a list of the most common commands used with Molecule.  For a complete list of scenarios and test functionality please review [MOLECULE_SCENARIOS.md](MOLECULE_SCENARIOS.md).

```
ls molecule
```


### Running a Scenario

To run the provisioning phase of a scenario:

```
molecule converge -s <scenario name>
```

This will leave the containers around for investigation. It is also useful because you can rerun converge multiple times as you develop code.

### SSHing into a container

Each docker container is named inside the molecule.yml file, copy the name and run:

```
molecule login -s <scenario name> -h <container-name>
```

### Running Scenario Validations Tests

Post provisioning validation tasks are defined in the verify.yml playbooks within each scenario. These can be run with:

```
molecule verify -s <scenario name>
```

### Destroying the Containers

Simply run:

```
molecule destroy -s <scenario name>
```

## Creating and Modifying Scenarios

When developing new features you can create a new scenario simply by duplicating the default one and customizing. Edit the verify.yml to have test assertions for your scenario.

Be sure to update the scenario documentation section and run the molecule_doc.py script before submitting your PR.  This will update the relevant documentation.

More details on building scenarios can be found [here](https://molecule.readthedocs.io/en/latest/getting-started.html?highlight=scenarios#molecule-scenarios).

## Running a full test suite

To run a molecule scenario completely, run:
```
molecule test -s <scenario name>
```
Beware, this will destroy the containers upon success or failure, making it challenging to investigate issues.

### Running Molecule in a Container

At times, pip installation of molecule can lead to errors:
```
ImportError: No module named docker.common
```

As a workaround you can use molecule in a container.  
In your current shell create an alias to start molecule in a container:

```
cd ansible_collections/confluent/platform
export CP_ANSIBLE_PATH=$PWD
alias molecule="docker run -it --rm --dns="8.8.8.8" -v "/var/run/docker.sock:/var/run/docker.sock" -v ~/.cache:/root/.cache -v "$CP_ANSIBLE_PATH:$CP_ANSIBLE_PATH" -w "$CP_ANSIBLE_PATH" quay.io/ansible/molecule:3.1.5 molecule"
```

To make the alias permanent, add the following to your .bashrc file:

```
export CP_ANSIBLE_PATH=<Replace this with the path>
alias molecule="docker run -it --rm --dns="8.8.8.8" -v "/var/run/docker.sock:/var/run/docker.sock" -v ~/.cache:/root/.cache -v "$CP_ANSIBLE_PATH:$CP_ANSIBLE_PATH" -w "$CP_ANSIBLE_PATH" quay.io/ansible/molecule:3.1.5 molecule"
```

Now the molecule command will run a container, but function as it should.
