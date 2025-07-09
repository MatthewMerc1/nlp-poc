# API Gateway and Lambda for semantic queries
resource "aws_api_gateway_rest_api" "semantic_api" {
  name        = "nlp-poc-semantic-api"
  description = "API Gateway for semantic queries against OpenSearch"

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-semantic-api"
    Purpose      = "semantic-search-api"
    ResourceType = "api-gateway"
  })
}

# API Gateway Resource
resource "aws_api_gateway_resource" "semantic_resource" {
  rest_api_id = aws_api_gateway_rest_api.semantic_api.id
  parent_id   = aws_api_gateway_rest_api.semantic_api.root_resource_id
  path_part   = "search"
}

# API Gateway Method
resource "aws_api_gateway_method" "semantic_method" {
  rest_api_id   = aws_api_gateway_rest_api.semantic_api.id
  resource_id   = aws_api_gateway_resource.semantic_resource.id
  http_method   = "POST"
  authorization = "NONE"
  api_key_required = true
}

# API Gateway Integration
resource "aws_api_gateway_integration" "semantic_integration" {
  rest_api_id             = aws_api_gateway_rest_api.semantic_api.id
  resource_id             = aws_api_gateway_resource.semantic_resource.id
  http_method             = aws_api_gateway_method.semantic_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.semantic_lambda.invoke_arn
}

# API Key
resource "aws_api_gateway_api_key" "semantic_api_key" {
  name = "nlp-poc-semantic-api-key"
  description = "API key for semantic search API"
  
  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-semantic-api-key"
    Purpose      = "api-authentication"
    ResourceType = "api-key"
  })
}

# Usage Plan
resource "aws_api_gateway_usage_plan" "semantic_usage_plan" {
  name         = "nlp-poc-semantic-usage-plan"
  description  = "Usage plan for semantic search API"

  api_stages {
    api_id = aws_api_gateway_rest_api.semantic_api.id
    stage  = aws_api_gateway_stage.semantic_stage.stage_name
  }

  quota_settings {
    limit  = 1000
    period = "DAY"
  }

  throttle_settings {
    rate_limit  = 10
    burst_limit = 20
  }

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-semantic-usage-plan"
    Purpose      = "api-rate-limiting"
    ResourceType = "usage-plan"
  })
}

# Associate API Key with Usage Plan
resource "aws_api_gateway_usage_plan_key" "semantic_usage_plan_key" {
  key_id        = aws_api_gateway_api_key.semantic_api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.semantic_usage_plan.id
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.semantic_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.semantic_api.execution_arn}/*/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "semantic_deployment" {
  depends_on = [
    aws_api_gateway_integration.semantic_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.semantic_api.id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "semantic_stage" {
  stage_name    = "dev"
  rest_api_id   = aws_api_gateway_rest_api.semantic_api.id
  deployment_id = aws_api_gateway_deployment.semantic_deployment.id

  # Enable CloudWatch logging
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.userAgent"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      integrationLatency = "$context.integrationLatency"
      responseLatency    = "$context.responseLatency"
    })
  }

  # Enable detailed CloudWatch metrics
  xray_tracing_enabled = true
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/nlp-poc-semantic-api"
  retention_in_days = 7

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-api-gateway-logs"
    Purpose      = "api-monitoring"
    ResourceType = "log-group"
  })
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.semantic_lambda.function_name}"
  retention_in_days = 7

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-lambda-logs"
    Purpose      = "lambda-monitoring"
    ResourceType = "log-group"
  })

  # Import existing log group if it exists
  lifecycle {
    create_before_destroy = true
  }
}

# Lambda Function
resource "aws_lambda_function" "semantic_lambda" {
  filename      = "lambda_function.zip"
  function_name = "nlp-poc-semantic-search"
  role          = aws_iam_role.semantic_lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 1024

  vpc_config {
    subnet_ids         = [aws_subnet.opensearch_subnet.id]
    security_group_ids = [aws_security_group.opensearch_sg.id]
  }

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = aws_opensearch_domain.embeddings_domain.endpoint
      OPENSEARCH_INDEX    = "book-embeddings"
      BEDROCK_MODEL_ID    = "amazon.titan-embed-text-v1"
      LOG_LEVEL           = "INFO"
    }
  }

  # Reserved concurrency to prevent throttling
  reserved_concurrent_executions = 10

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-semantic-lambda"
    Purpose      = "semantic-search"
    ResourceType = "lambda-function"
  })
}

# IAM Role for Lambda
resource "aws_iam_role" "semantic_lambda_role" {
  name = "nlp-poc-semantic-lambda-role"

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

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-semantic-lambda-role"
    Purpose      = "lambda-execution"
    ResourceType = "iam-role"
  })
}

# IAM Policy for Lambda
resource "aws_iam_policy" "semantic_lambda_policy" {
  name        = "nlp-poc-semantic-lambda-policy"
  description = "Policy for semantic search Lambda function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "es:ESHttp*"
        ]
        Resource = "${aws_opensearch_domain.embeddings_domain.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v1"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-semantic-lambda-policy"
    Purpose      = "lambda-permissions"
    ResourceType = "iam-policy"
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "semantic_lambda_policy_attachment" {
  role       = aws_iam_role.semantic_lambda_role.name
  policy_arn = aws_iam_policy.semantic_lambda_policy.arn
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "semantic_lambda_basic_policy_attachment" {
  role       = aws_iam_role.semantic_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Outputs
output "api_gateway_url" {
  description = "URL of the API Gateway endpoint"
  value       = "${aws_api_gateway_stage.semantic_stage.invoke_url}/search"
}

output "lambda_function_name" {
  description = "Name of the semantic search Lambda function"
  value       = aws_lambda_function.semantic_lambda.function_name
}

output "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = aws_opensearch_domain.embeddings_domain.endpoint
}

