# Monitoring Module Variables

variable "project_name" {
  description = "Name of the project for resource naming"
  type        = string
}

variable "alert_email_addresses" {
  description = "List of email addresses to receive alerts"
  type        = list(string)
  default     = []
}

variable "enable_lambda_monitoring" {
  description = "Enable Lambda monitoring alarms"
  type        = bool
  default     = true
}

variable "enable_api_monitoring" {
  description = "Enable API Gateway monitoring alarms"
  type        = bool
  default     = true
}

variable "enable_opensearch_monitoring" {
  description = "Enable OpenSearch monitoring alarms"
  type        = bool
  default     = true
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to monitor"
  type        = string
  default     = ""
}

variable "api_gateway_name" {
  description = "Name of the API Gateway to monitor"
  type        = string
  default     = ""
}

variable "api_gateway_stage" {
  description = "Stage name of the API Gateway to monitor"
  type        = string
  default     = "dev"
}

variable "opensearch_domain_name" {
  description = "Name of the OpenSearch domain to monitor"
  type        = string
  default     = ""
}

variable "alarm_evaluation_periods" {
  description = "Number of evaluation periods for alarms"
  type        = string
  default     = "2"
}

variable "alarm_period" {
  description = "Period in seconds for alarm evaluation"
  type        = string
  default     = "300"
}

variable "lambda_error_threshold" {
  description = "Threshold for Lambda error alarm"
  type        = string
  default     = "5"
}

variable "lambda_duration_threshold" {
  description = "Threshold for Lambda duration alarm (milliseconds)"
  type        = string
  default     = "25000"
}

variable "api_4xx_error_threshold" {
  description = "Threshold for API Gateway 4XX error alarm"
  type        = string
  default     = "10"
}

variable "api_5xx_error_threshold" {
  description = "Threshold for API Gateway 5XX error alarm"
  type        = string
  default     = "5"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
} 