### What
Discovery is set of scripts that searches the Confluent Platform services and their properties on given set of nodes. This is a tool to help users to use cp-ansible plays to manage their cluster which was orgininally not installed by cp-ansible.  
Though this script tries to come up with inventory which is the closed representation of the given cluster, yet its advisable to run in lower environment and validate it manually.

### Prerequisites
#### Software
- Python 3.8+  
- Ansible 2.11  
- PyYaml 6.0  
- ansible_runner (pip)
- jproperties (pip)

These are dependencies for this script and should be installed on the machine where we are executing it from. This is not a requirement for managed nodes of the cluster.
#### Hosts
The discovery script needs list of hosts which is part of the existing cluster on which services has to be discovered. Apart from the list of hosts, the script also need the Confluent Service names. If these service names has been updated, the same should be provided under `service_override` section.

```yaml
all:
  vars:
    ansible_connection: docker
    ansible_user: null
    service_override:
      zookeeper_service_name: myservice.zookeeper
```

### How
Discovery uses set of Python and Ansible scripts to build a cp-ansible compatible inventory file. Once we have the inventory file, we can use it for any cluster operation normally using cp-ansible.

```shell
cd <some_path>/ansible_collections/confluent/platform
PYTHONPATH=. python discovery/main.py --input discovery/hosts.yml [optional arguments] 
```
#### Sample input file (hosts.yml)
A Cluster with un-known host group mappings. In this case, the script will try to map the service and corresponding hosts.
```yaml
vars:
  ansible_connection: ssh
  ansible_user: centos
  ansible_become: true
  ansible_ssh_extra_args: -o StrictHostKeyChecking=no
  ansible_ssh_private_key_file: ~/Work/keys/muckrake.pem

hosts:
  all:
    - ec2-35-85-206-158.us-west-2.compute.amazonaws.com
    - ec2-44-236-74-105.us-west-2.compute.amazonaws.com
    - ec2-35-85-206-158.us-west-2.compute.amazonaws.com
    - ec2-44-236-74-105.us-west-2.compute.amazonaws.com
    - ec2-54-212-15-112.us-west-2.compute.amazonaws.com
    - ec2-34-219-160-51.us-west-2.compute.amazonaws.com
    - ec2-18-237-83-100.us-west-2.compute.amazonaws.com
    - ec2-34-209-150-254.us-west-2.compute.amazonaws.com
    - ec2-54-245-5-52.us-west-2.compute.amazonaws.com

```
A Cluster with known host group mappings. Script will look for the configured services on the given hosts. Please update the service name if service names are non default, using service overrides values. 
```yaml
vars:
  ansible_connection: ssh
  ansible_user: centos
  ansible_become: true
  ansible_ssh_extra_args: -o StrictHostKeyChecking=no
  ansible_ssh_private_key_file: ~/Work/keys/muckrake.pem

hosts:
  zookeeper:
    - ec2-35-85-206-158.us-west-2.compute.amazonaws.com
    - ec2-44-236-74-105.us-west-2.compute.amazonaws.com

  kafka_broker:
    - ec2-35-85-206-158.us-west-2.compute.amazonaws.com
    - ec2-44-236-74-105.us-west-2.compute.amazonaws.com

  schema_registry:
    - ec2-54-212-15-112.us-west-2.compute.amazonaws.com
    - ec2-34-219-160-51.us-west-2.compute.amazonaws.com

  kafka_connect:
    - ec2-18-237-83-100.us-west-2.compute.amazonaws.com
    - ec2-34-209-150-254.us-west-2.compute.amazonaws.com

  kafka_rest:
    - ec2-54-245-5-52.us-west-2.compute.amazonaws.com

  ksql:
    - ec2-18-237-83-100.us-west-2.compute.amazonaws.com
    - ec2-34-209-150-254.us-west-2.compute.amazonaws.com

  control_center:
    - ec2-54-245-5-52.us-west-2.compute.amazonaws.com

```
For a cluster running on local docker environment 
```yaml

vars:
  ansible_connection: docker
  service_override:
    zookeeper_service_name: 'custom-service-name'
hosts:
  all:
    - zookeeper1
    - kafka-broker1
    - kafka-broker2
    - kafka-broker3
    - schema-registry1
    - kafka-rest1
    - kafka-connect1
    - ksql1
    - control-center1

```

#### Command Line options
##### verbose
To get the verbose output from script and Ansible you can set the verbosity level between 0 to 4. Where 4 means more verbose.
##### limit
Use limit flag to limit the discovery for specified list of hosts
##### output_file
Use this flag to specify output inventory file name. Default value is inventory.yml

```shell
python discovery/main.py --input discovery/hosts.yml --verbose 4 --limit host1,host2
```
### FQA
* **Can I use it for older CP versions**  
Ideally we should be using the discovery from the branch which maps to the CP cluster. However, to onboard existing cluster, one can use the latest disvoery code and use **--from_version** parameter to specify the CP cluster version


* **Getting Permission issue while executing the script**  
Ensure that the VM/Host exists and the user has access to /tmp directory. Sometimes deleting ~/.ansible and ~/.cache directories turns out to be a quick solution.

### Known Issues and limitations
* If passwords are encrypted using secret encryption or any other encryption algorithm, this script would not be able to decrypt it. User has to explicitly add the passwords in the generated inventory file in order to continue using the cp-ansible.
* The input hosts file doesn't support regex for hosts pattern
* Discovery doesn't support CP community edition.
* At the time of running this script, the CP services should be up and running. Otherwise, the script will ignore those nodes/services
* If secrets protection is enabled on cluster, Discovery scripts can populate the master key. However, all passwords should be filled by the user before using the play
