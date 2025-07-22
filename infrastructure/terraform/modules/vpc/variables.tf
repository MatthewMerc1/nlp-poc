variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "vpc_name" {
  description = "Name for the VPC and related resources."
  type        = string
  default     = "nlp-poc-vpc"
}

variable "azs" {
  description = "List of availability zones to use for subnets. Should be at least two."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
} 