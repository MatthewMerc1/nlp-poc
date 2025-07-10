# Lambda Module Outputs

output "function_name" {
  description = "Name of the Lambda function"
  value       = length(aws_lambda_function.main) > 0 ? aws_lambda_function.main[0].function_name : ""
}

output "function_arn" {
  description = "ARN of the Lambda function"
  value       = length(aws_lambda_function.main) > 0 ? aws_lambda_function.main[0].arn : ""
}

output "function_invoke_arn" {
  description = "Invocation ARN of the Lambda function"
  value       = length(aws_lambda_function.main) > 0 ? aws_lambda_function.main[0].invoke_arn : ""
}

output "role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda.arn
}

output "role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda.name
}

output "bedrock_policy_arn" {
  description = "ARN of the Bedrock embedding policy"
  value       = aws_iam_policy.bedrock_policy.arn
} 