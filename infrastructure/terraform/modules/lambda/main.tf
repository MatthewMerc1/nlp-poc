# Lambda Module - Lambda function with IAM roles and policies
# This module creates a Lambda function with necessary permissions

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# IAM Role for Lambda
resource "aws_iam_role" "lambda" {
  name = "${var.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM Policy for Lambda execution
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for Bedrock access
resource "aws_iam_policy" "bedrock_policy" {
  name        = "${var.function_name}-bedrock-policy"
  description = "Policy for Bedrock embedding generation"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:ListFoundationModels"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v1"
        ]
      }
    ]
  })

  tags = var.tags
}

# Attach Bedrock policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_bedrock" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.bedrock_policy.arn
}

# IAM Policy for S3 access
resource "aws_iam_policy" "s3_policy" {
  name        = "${var.function_name}-s3-policy"
  description = "Policy for S3 access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      }
    ]
  })

  tags = var.tags
}

# Attach S3 policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.s3_policy.arn
}

# IAM Policy for OpenSearch access
resource "aws_iam_policy" "opensearch_policy" {
  name        = "${var.function_name}-opensearch-policy"
  description = "Policy for OpenSearch access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:CreateCollectionItems",
          "aoss:DescribeCollectionItems",
          "aoss:UpdateCollectionItems", 
          "aoss:DeleteCollectionItems",
          "aoss:ReadDocument",
          "aoss:WriteDocument",
          "aoss:APIAccessAll"
        ]
        Resource = [
          "arn:aws:aoss:${var.aws_region}:${data.aws_caller_identity.current.account_id}:collection/${var.collection_id}",
          "arn:aws:aoss:${var.aws_region}:${data.aws_caller_identity.current.account_id}:index/${var.collection_id}/*"
        ]
      }
    ]
  })

  tags = var.tags
}

# Attach OpenSearch policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_opensearch" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.opensearch_policy.arn
}

# IAM Policy for VPC access (if VPC config is provided)
resource "aws_iam_policy" "vpc_policy" {
  count = var.vpc_config != null ? 1 : 0
  
  name        = "${var.function_name}-vpc-policy"
  description = "Policy for VPC access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ]
        Resource = "*"
      }
    ]
  })

  tags = var.tags
}

# Attach VPC policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  count = var.vpc_config != null ? 1 : 0
  
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.vpc_policy[0].arn
}

# Lambda Function
resource "aws_lambda_function" "main" {
  filename         = var.lambda_zip_path
  function_name    = var.function_name
  role            = aws_iam_role.lambda.arn
  handler         = var.handler
  runtime         = var.runtime
  timeout         = var.timeout
  memory_size     = var.memory_size

  # Only create if ZIP file exists and function doesn't already exist
  count = fileexists(var.lambda_zip_path) && var.create_lambda_function ? 1 : 0

  dynamic "vpc_config" {
    for_each = var.vpc_config != null ? [var.vpc_config] : []
    content {
      subnet_ids         = vpc_config.value.subnet_ids
      security_group_ids = vpc_config.value.security_group_ids
    }
  }

  environment {
    variables = merge(
      var.environment_variables,
      {
        OPENSEARCH_ENDPOINT = var.opensearch_serverless_collection_endpoint
      }
    )
  }

  tags = var.tags
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  count = fileexists(var.lambda_zip_path) && var.create_lambda_function ? 1 : 0
  
  name              = "/aws/lambda/${aws_lambda_function.main[0].function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  count = fileexists(var.lambda_zip_path) && var.create_lambda_function ? 1 : 0
  
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
} 