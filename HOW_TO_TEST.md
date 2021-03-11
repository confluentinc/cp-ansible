# How to test

Starting with CP-Ansible 5.5.0, we have included testing via the [Molecule](https://molecule.readthedocs.io/en/latest/) framework, and strongly advise its usage before submitting a Pull Request.

## Prerequisites

1. Python3 installed with PIP
2. Docker installed
3. Install the Molecule and Docker libraries  
```pip install molecule docker```

Note: If using Molecule version 3.1.0 or later use the following command to install:

```pip3 install molecule molecule-docker```



Note: We recommend increasing your docker memory to at least 20GB of RAM and your CPU count to 10.  

### A note about Molecule

You might find Molecule failing with an error like: 
```
ImportError: No module named docker.common
```
You can spend some time troubleshooting this issue with the prerequisites.  
As a workaround you can use molecule in a container.  

In your current shell create an alias to start molecule in a container: 

```
git clone https://github.com/confluentinc/cp-ansible
cd cp-ansible
export CP_ANISBLE_PATH=$PWD
alias molecule="docker run -it --rm --dns="8.8.8.8" -v "/var/run/docker.sock:/var/run/docker.sock" -v ~/.cache:/root/.cache -v "$CP_ANISBLE_PATH:$CP_ANISBLE_PATH" -w "$CP_ANISBLE_PATH/roles/confluent.test" quay.io/ansible/molecule:3.1.5 molecule"
```

Now you can run the molecule command as suggested later on.  
You can also consider integrating the alias in your bashrc file. In your bashrc file add the following:

alias molecule="docker run -it --rm --dns="8.8.8.8" -v "/var/run/docker.sock:/var/run/docker.sock" -v ~/.cache:/root/.cache -v "$CP_ANISBLE_PATH:$CP_ANISBLE_PATH" -w "$CP_ANISBLE_PATH/roles/confluent.test" quay.io/ansible/molecule:3.1.5 molecule"
```

Now you can run the molecule command as suggested later on.  
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
