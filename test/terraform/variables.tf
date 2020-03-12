variable "vpc_id" {
  description = "VPC ID"
  default     = "vpc-1234"
}

variable "subnet" {
  description = "VPC Subnet ID the instance is launched in"
  default     = "subnet-1234"
}

variable "region" {
  description = "AWS Region the instance is launched in"
  default     = "us-west-2"
}

variable "unique_identifier" {
  description = "Unique ID for AWS objects to avoid naming collisions"
  default = "cp1"
}

## Use the below code to create a new aws key from a local file
## NOTE: Change this variable to something unique to avoid naming collision
variable "ssh_key_pair" {
  description = "SSH key pair to be provisioned on the instance"
  default = "cp1-key"
}
variable "ssh_key_public_path" {
  description = "Path to local public ssh key"
  default = "~/.ssh/id_rsa.pub"
}
resource "aws_key_pair" "default" {
  key_name   = var.ssh_key_pair
  public_key = file(var.ssh_key_public_path)
}

## Alternatively comment out the above key variables and use an aws key that already exists in aws
# variable "ssh_key_pair" {
#   description = "SSH key pair to be provisioned on the instance"
#   default     = "muckrake-2017-06-01"
# }

variable "instance_type" {
  description = "The type of the instance"
  default     = "t2.medium"
}

variable "ami" {
  description = "The AMI to use for the instance."
  # Below amis only work in us-west-2, if you select another region, this MUST be changed with it
  default = "ami-01ed306a12b7d1c96" # centos
  # default = "ami-0b37e9efc396e4c38" #Ubuntu 16
  # default = "ami-0b86e06624ac20c42" # Debian stretch
}

variable "kerberos_ami" {
  description = "Kerberos AMI, should be centos/rhel"
  default = "ami-01ed306a12b7d1c96" # centos
}

variable "zookeeper_instance_count" {
  description = "EC2 instance count of Zookeeper Nodes"
  default     = "3"
}

variable "kafka_instance_count" {
  description = "EC2 instance count of Kafka Brokers"
  default     = "3"
}

variable "schema_registry_instance_count" {
  description = "EC2 instance count of Schema Registry instances"
  default     = "1"
}

variable "connect_instance_count" {
  description = "EC2 instance count of Connect Nodes"
  default     = "1"
}

variable "rest_proxy_instance_count" {
  description = "EC2 instance count of Rest Proxy Nodes"
  default     = "1"
}

variable "ksql_instance_count" {
  description = "EC2 instance count of KSQL Nodes"
  default     = "1"
}

variable "control_center_instance_count" {
  description = "EC2 instance count of Control Center Nodes"
  default     = "1"
}
