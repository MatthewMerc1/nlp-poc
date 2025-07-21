# Development Environment Outputs

output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.data_bucket.bucket_id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.data_bucket.bucket_arn
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

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = module.lambda.role_arn
}

output "lambda_role_name" {
  description = "Name of the Lambda execution role"
  value       = module.lambda.role_name
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = module.monitoring.sns_topic_arn
}

output "bedrock_policy_arn" {
  description = "ARN of the Bedrock embedding policy"
  value       = module.lambda.bedrock_policy_arn
}

output "opensearch_serverless_collection_endpoint" {
  description = "Endpoint for the OpenSearch Serverless collection."
  value       = module.opensearch_serverless.collection_endpoint
}

output "opensearch_serverless_collection_name" {
  description = "Name of the OpenSearch Serverless collection."
  value       = module.opensearch_serverless.collection_name
} 