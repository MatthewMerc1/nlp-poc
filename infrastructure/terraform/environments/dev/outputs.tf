# Development Environment Outputs

output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.data_bucket.bucket_id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.data_bucket.bucket_arn
}

output "opensearch_domain_name" {
  description = "Name of the OpenSearch domain"
  value       = module.opensearch.domain_name
}

output "opensearch_endpoint" {
  description = "Endpoint of the OpenSearch domain"
  value       = module.opensearch.domain_endpoint
}

output "opensearch_dashboard_url" {
  description = "URL for the OpenSearch dashboard"
  value       = "https://${module.opensearch.domain_endpoint}/_dashboards/"
}

output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = module.api_gateway.invoke_url
}

output "api_key" {
  description = "API key for authentication"
  value       = module.api_gateway.api_key
  sensitive   = true
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.lambda.function_name
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.opensearch.vpc_id
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = module.monitoring.sns_topic_arn
}

output "bedrock_policy_arn" {
  description = "ARN of the Bedrock embedding policy"
  value       = module.lambda.bedrock_policy_arn
} 