# OpenSearch Module Variables

variable "domain_name" {
  description = "Name of the OpenSearch domain"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "t3.small.search"
}

variable "instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 1
}

variable "volume_size" {
  description = "EBS volume size in GB"
  type        = number
  default     = 10
}

variable "volume_type" {
  description = "EBS volume type"
  type        = string
  default     = "gp3"
}

variable "engine_version" {
  description = "OpenSearch engine version"
  type        = string
  default     = "OpenSearch_2.11"
}

variable "zone_awareness_enabled" {
  description = "Enable zone awareness"
  type        = bool
  default     = false
}

variable "enable_advanced_security" {
  description = "Enable advanced security options"
  type        = bool
  default     = false
}

variable "master_user_name" {
  description = "Master user name for advanced security"
  type        = string
  default     = "admin"
}

variable "master_user_password" {
  description = "Master user password for advanced security"
  type        = string
  default     = ""
  sensitive   = true
}

variable "vpc_cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "allowed_ipv4_addresses" {
  description = "List of allowed IPv4 addresses for OpenSearch access"
  type        = list(string)
  default     = []
}

variable "allowed_ipv6_addresses" {
  description = "List of allowed IPv6 addresses for OpenSearch access"
  type        = list(string)
  default     = []
}

variable "bastion_public_key" {
  description = "Public SSH key for bastion host access"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
} 