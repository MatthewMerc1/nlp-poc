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
  default     = "nlp-poc-bucket-test"
}

variable "bucket_force_destroy" {
  description = "Whether to force destroy the bucket even if it contains objects"
  type        = bool
  default     = true
}

variable "bucket_tags" {
  description = "Tags to apply to the S3 bucket"
  type        = map(string)
  default = {
    Name        = "AudiobookDataBucket"
    Environment = "dev"
    "caylent:owner" = "matthew.mercado@caylent.com"
  }
}

variable "enable_versioning" {
  description = "Whether to enable versioning on the S3 bucket"
  type        = bool
  default     = true
} 