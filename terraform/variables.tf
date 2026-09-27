variable "region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type (must have an attached NVIDIA GPU)"
  type        = string
  default     = "g4dn.xlarge"
}

variable "key_name" {
  description = "Name of an existing EC2 key pair to SSH in with"
  type        = string
}

variable "ssh_cidr" {
  description = "CIDR allowed to SSH in, e.g. \"1.2.3.4/32\" (your public IP)"
  type        = string
}

variable "root_volume_gb" {
  description = "Root EBS volume size in GB"
  type        = number
  default     = 100
}

variable "instance_name" {
  description = "Name tag for the instance"
  type        = string
  default     = "vllm-nexus"
}
