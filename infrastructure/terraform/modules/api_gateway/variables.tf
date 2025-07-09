# API Gateway Module Variables

variable "api_name" {
  description = "Name of the API Gateway"
  type        = string
}

variable "api_description" {
  description = "Description of the API Gateway"
  type        = string
  default     = "REST API for semantic search"
}

variable "stage_name" {
  description = "Name of the API Gateway stage"
  type        = string
  default     = "dev"
}

variable "lambda_invoke_arn" {
  description = "Invocation ARN of the Lambda function"
  type        = string
}

variable "require_api_key" {
  description = "Whether to require API key for access"
  type        = bool
  default     = true
}

variable "daily_quota" {
  description = "Daily request quota"
  type        = number
  default     = 1000
}

variable "rate_limit" {
  description = "Rate limit per second"
  type        = number
  default     = 10
}

variable "burst_limit" {
  description = "Burst limit"
  type        = number
  default     = 20
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "enable_xray" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
} 