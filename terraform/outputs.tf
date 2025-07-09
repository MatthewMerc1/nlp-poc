output "bucket_name" {
  description = "Name of the created S3 bucket"
  value       = aws_s3_bucket.audiobook_data.bucket
}

output "bucket_arn" {
  description = "ARN of the created S3 bucket"
  value       = aws_s3_bucket.audiobook_data.arn
}

output "bucket_region" {
  description = "AWS region where the bucket was created"
  value       = aws_s3_bucket.audiobook_data.region
}

output "bucket_tags" {
  description = "Tags applied to the S3 bucket"
  value       = aws_s3_bucket.audiobook_data.tags
}

# OpenSearch outputs
output "opensearch_domain_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = aws_opensearch_domain.embeddings_domain.endpoint
}

output "opensearch_domain_arn" {
  description = "OpenSearch domain ARN"
  value       = aws_opensearch_domain.embeddings_domain.arn
}

output "opensearch_dashboard_url" {
  description = "OpenSearch Dashboard URL"
  value       = "https://${aws_opensearch_domain.embeddings_domain.endpoint}/_dashboards/"
}

# API Gateway outputs
output "api_key" {
  description = "API key for accessing the semantic search API"
  value       = aws_api_gateway_api_key.semantic_api_key.value
  sensitive   = true
}

# Monitoring outputs
output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "cloudwatch_log_groups" {
  description = "CloudWatch log groups created"
  value = {
    api_gateway = aws_cloudwatch_log_group.api_gateway_logs.name
    lambda      = aws_cloudwatch_log_group.lambda_logs.name
  }
} 
