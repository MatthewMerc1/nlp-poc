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
