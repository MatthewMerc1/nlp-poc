# Development Environment Variables

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS profile to use"
  type        = string
  default     = "caylent-dev-test"
}

variable "bucket_name" {
  description = "Name of the S3 bucket for data storage"
  type        = string
}

variable "opensearch_serverless_collection_name" {
  description = "Name of the OpenSearch Serverless collection."
  type        = string
  default     = "nlp-poc-serverless"
}

variable "opensearch_serverless_description" {
  description = "Description for the OpenSearch Serverless collection."
  type        = string
  default     = "OpenSearch Serverless collection for NLP POC."
}

variable "opensearch_serverless_data_access_policy_json" {
  description = "OpenSearch Serverless data access policy configuration."
  type = list(object({
    Principal = list(string)
    Rules = list(object({
      Resource     = list(string)
      Permission   = list(string)
      ResourceType = string
    }))
  }))
}

variable "force_destroy" {
  description = "Whether to force destroy the S3 bucket"
  type        = bool
  default     = false
}

variable "folders" {
  description = "List of folders to create in the S3 bucket"
  type        = list(string)
  default     = []
}

variable "lifecycle_rules" {
  description = "List of lifecycle rules for the S3 bucket"
  type = list(object({
    id              = string
    status          = string
    prefix          = string
    transitions     = list(object({
      days          = number
      storage_class = string
    }))
    expiration_days = optional(number)
  }))
  default = []
}

variable "alert_email_addresses" {
  description = "List of email addresses to receive monitoring alerts"
  type        = list(string)
  default     = []
} 