variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS profile to use for authentication"
  type        = string
  default     = "caylent-dev-test"
}

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
  default     = "nlp-poc-bucket-dev"
}

variable "bucket_force_destroy" {
  description = "Whether to force destroy the bucket even if it contains objects"
  type        = bool
  default     = true
}



variable "enable_versioning" {
  description = "Whether to enable versioning on the S3 bucket"
  type        = bool
  default     = true
}

# OpenSearch variables
variable "opensearch_domain_name" {
  description = "Name of the OpenSearch domain"
  type        = string
  default     = "nlp-poc-embeddings-dev"
}

variable "opensearch_instance_type" {
  description = "Instance type for OpenSearch nodes"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 1
}

variable "opensearch_volume_size" {
  description = "EBS volume size for OpenSearch nodes (GB)"
  type        = number
  default     = 10
}

# Shared tags for all resources
variable "shared_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "dev"
    "caylent:owner" = "matthew.mercado@caylent.com"
    Project     = "nlp-poc"
  }
}

# Resource-specific tag variables
variable "s3_bucket_tags" {
  description = "Additional tags for S3 bucket"
  type        = map(string)
  default = {
    Name = "NLP-POC-S3-Bucket"
    Purpose = "book-storage"
    ResourceType = "s3-bucket"
  }
}

variable "opensearch_domain_tags" {
  description = "Additional tags for OpenSearch domain"
  type        = map(string)
  default = {
    Name = "NLP-POC-OpenSearch-Domain"
    Purpose = "vector-search"
    ResourceType = "opensearch-domain"
  }
}

variable "vpc_tags" {
  description = "Additional tags for VPC"
  type        = map(string)
  default = {
    Name = "nlp-poc-vpc"
    Purpose = "opensearch-networking"
    ResourceType = "vpc"
  }
}

variable "subnet_tags" {
  description = "Additional tags for subnet"
  type        = map(string)
  default = {
    Name = "nlp-poc-subnet"
    Purpose = "opensearch-networking"
    ResourceType = "subnet"
  }
}

variable "security_group_tags" {
  description = "Additional tags for security group"
  type        = map(string)
  default = {
    Name = "nlp-poc-security-group"
    Purpose = "opensearch-security"
    ResourceType = "security-group"
  }
}

variable "route_table_tags" {
  description = "Additional tags for route table"
  type        = map(string)
  default = {
    Name = "nlp-poc-route-table"
    Purpose = "opensearch-networking"
    ResourceType = "route-table"
  }
}

variable "internet_gateway_tags" {
  description = "Additional tags for internet gateway"
  type        = map(string)
  default = {
    Name = "nlp-poc-internet-gateway"
    Purpose = "opensearch-networking"
    ResourceType = "internet-gateway"
  }
}

variable "iam_policy_tags" {
  description = "Additional tags for IAM policy"
  type        = map(string)
  default = {
    Name = "nlp-poc-bedrock-policy"
    Purpose = "ai-permissions"
    ResourceType = "iam-policy"
  }
} 
