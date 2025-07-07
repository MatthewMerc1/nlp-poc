# Main Terraform configuration for NLP POC
# This file contains the core Terraform configuration and provider setup

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS Provider configuration
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

# Note: Individual resources are defined in separate files:
# - s3.tf: S3 bucket and folder structure
# - opensearch.tf: OpenSearch domain and networking
# - iam.tf: IAM policies and permissions