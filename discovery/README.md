### What
Discovery is set of scripts that searches the Confluent Platform services and their properties on given set of nodes. This is a tool to help users to use cp-ansible plays to manage their cluster which was orgininally not installed by cp-ansible.  
Though this script tries to come up with inventory which is the closed representation of the given cluster, yet its advisable to run in lower environment and validate it manually.

### Prerequisites
#### Software
> Python 3.9+  
> Ansible 2.11  
> PyYaml 6.0  

These are dependencies for this script and should be installed on the machine where we are executing it from. This is not a requirement for managed nodes of the cluster.
#### Hosts
The discovery script needs list of hosts which is part of the existing cluster and services has to be discovered

### How
Discovery uses set of Python and Ansible scripts to build a cp-ansible compatible inventory file. Once we have the inventory file, we can use it for any cluster operation normally using cp-ansible.

```shell
cd <some_path>/ansible_collections/confluent/platform
PYTHONPATH=. python discovery/main.py --input discovery/hosts.yml [optional arguments] 
```
#### Sample input file (hosts.yml)
```yaml
all:
  vars:
    ansible_connection: ssh
    ansible_become: true
    ansible_python_interpreter: auto
    ansible_user: centos
    ansible_become_user: root
    ansible_become_method: sudo
    ansible_ssh_extra_args: -o StrictHostKeyChecking=no
    ansible_ssh_private_key_file: <path_to_private_key_to_login_to_vms>
  hosts:
    - ec2-35-164-166-99.us-west-2.compute.amazonaws.com
    - ec2-35-164-166-99.us-west-2.compute.amazonaws.com
    - ec2-35-86-106-150.us-west-2.compute.amazonaws.com
    - ec2-54-191-208-245.us-west-2.compute.amazonaws.com
    - ec2-35-164-166-99.us-west-2.compute.amazonaws.com
```
#### Sample output file (inventory.yml)

#### Command Line options
We can override all input parameters from command line as well.
```shell
python discovery/main.py --input discovery/hosts.yml --ansible_user some_user --ansible_connection docker 
```
### FQA
* **Can I use it for older CP versions**  
Ideally we should be using the discovery from the branch which maps to the CP cluster. However, to onboard existing cluster, one can use the latest disvoery code and use **--from_version** parameter to specify the CP cluster version

### Known Issues and limitations
* If passwords are encrypted using secret encryption or any other encryption algorithm, this script would not be able to decrypt it. User has to explicitly add the passwords in the generated inventory file in order to continue using the cp-ansible.
* The input hosts file doesn't support regex for hosts parttern
* Discovery doesn't support CP community edition.
* At the time of running this script, the CP services should be up and running. Otherwise, the script will ignore those nodes/services
* If secrets protection is enabled on cluster, Discovery scripts can populate the master key. However, all passwords should be filled by the user before using the play
