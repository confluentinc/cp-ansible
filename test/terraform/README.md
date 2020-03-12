# Terraform to support cp-ansible

This repo is meant to help provision infrastructure that can be used to facilitate the testing of cp-ansible. The terraform code is opinionated and far from perfect and only runs smoothly in us-west-2 in a preprovisioned subnet. It is *not* intended to be your production Confluent Platform deployment.

**Dependencies:**

 - Latest version of terraform (0.12+)
 - Ansible version 2.7 or greater

## Instructions

### 1. Set AWS Credential Environment Variables

```
export AWS_ACCESS_KEY_ID="key"
export AWS_SECRET_ACCESS_KEY="secret"
```

### 2. Customize installation by setting variables in variables.tf

This terraform code currently deploys centos 7 VMs with AMIs tied to us-west-2. If you desire a deployment in another region, then you will need to set these variables:

 - vpc_id
 - subnet_id
 - ami
 - kerberos_ami

Terraform will also create an ssh key in AWS and give it to your hosts out of your public key found at ~/.ssh/id_rsa.pub If you would like to use a different local key, change this variable: *ssh_key_public_path*. If you would like to use a pre existing key in AWS follow the commented instructions in variables.tf

### 3. Provision Infrastructure

Creating instances takes two commands! Be sure to put your own unique identifier and key pair name to avoid naming collisions.

```
cd /path/to/cp-ansible-tools/terraform
terraform init
terraform apply -var 'vpc_id=vpc-1234' \
  -var 'subnet=subnet-1234' \
  -var 'unique_identifier=user1' \
  -var 'ssh_key_pair=user1-key'
```

### 4. Examine your inventory file (Can be skipped)

Terraform will create you ansible inventory file for you in the file *hosts.yml*. This is the file where you set installation variables. Examine it with:

```
cat hosts.yml
```

### 5. SSH to a host (Can be skipped)

Provided a local ssh key was used in the provisioning, it is very easy to ssh to your hosts. Copy a public hostname from the hosts.yml and run:

```
ssh centos@<public hostname>
```

### 6. Install Confluent Platform

Using the generated *hosts.yml* file, you can very easily install all the components by running:

```
cd ../..
ansible-playbook -i test/terraform/hosts.yml all.yml
```

### 7. View your deployment in the browser!

Copy c3's public hostname from *hosts.yml* and to *https://<public_hostname_of_c3>:9021* in your browser

### 8. Destroy Infrastructure

Don't be ~~wasty~~ and destroy everything that you have deployed, so you do not get billed. To destroy run:

```
cd test/terraform
terraform destroy --auto-approve
```
