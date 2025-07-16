output "collection_endpoint" {
  description = "Endpoint for the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.this.collection_endpoint
}

output "collection_id" {
  description = "ID of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.this.id
}

output "collection_name" {
  description = "Name of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.this.name
} 