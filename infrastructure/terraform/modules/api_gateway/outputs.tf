# API Gateway Module Outputs

output "api_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_arn" {
  description = "ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.main.arn
}

output "execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.main.execution_arn
}

output "invoke_url" {
  description = "Invoke URL for the API Gateway"
  value       = "${aws_api_gateway_stage.main.invoke_url}/search"
}

output "api_key" {
  description = "API key for authentication"
  value       = var.require_api_key ? aws_api_gateway_api_key.main[0].value : null
  sensitive   = true
}

output "api_key_id" {
  description = "ID of the API key"
  value       = var.require_api_key ? aws_api_gateway_api_key.main[0].id : null
} 