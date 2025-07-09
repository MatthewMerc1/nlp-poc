# API Gateway Module - REST API with Lambda integration
# This module creates a complete API Gateway setup with monitoring

# API Gateway REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = var.api_name
  description = var.api_description

  tags = var.tags
}

# API Gateway Resource
resource "aws_api_gateway_resource" "search" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "search"
}

# API Gateway Method
resource "aws_api_gateway_method" "search" {
  rest_api_id      = aws_api_gateway_rest_api.main.id
  resource_id      = aws_api_gateway_resource.search.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = var.require_api_key
}

# API Gateway Integration
resource "aws_api_gateway_integration" "search" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.search.id
  http_method             = aws_api_gateway_method.search.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arn
}

# API Key (if required)
resource "aws_api_gateway_api_key" "main" {
  count = var.require_api_key ? 1 : 0
  
  name        = "${var.api_name}-key"
  description = "API key for ${var.api_name}"
  
  tags = var.tags
}

# Usage Plan (if API key is required)
resource "aws_api_gateway_usage_plan" "main" {
  count = var.require_api_key ? 1 : 0
  
  name        = "${var.api_name}-usage-plan"
  description = "Usage plan for ${var.api_name}"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.main.stage_name
  }

  quota_settings {
    limit  = var.daily_quota
    period = "DAY"
  }

  throttle_settings {
    rate_limit  = var.rate_limit
    burst_limit = var.burst_limit
  }

  tags = var.tags
}

# Associate API Key with Usage Plan
resource "aws_api_gateway_usage_plan_key" "main" {
  count = var.require_api_key ? 1 : 0
  
  key_id        = aws_api_gateway_api_key.main[0].id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.main[0].id
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.api_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "main" {
  depends_on = [
    aws_api_gateway_integration.search,
  ]

  rest_api_id = aws_api_gateway_rest_api.main.id

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "main" {
  stage_name    = var.stage_name
  rest_api_id   = aws_api_gateway_rest_api.main.id
  deployment_id = aws_api_gateway_deployment.main.id

  # Enable CloudWatch logging
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId           = "$context.requestId"
      ip                  = "$context.identity.sourceIp"
      caller              = "$context.identity.userAgent"
      user                = "$context.identity.user"
      requestTime         = "$context.requestTime"
      httpMethod          = "$context.httpMethod"
      resourcePath        = "$context.resourcePath"
      status              = "$context.status"
      protocol            = "$context.protocol"
      responseLength      = "$context.responseLength"
      integrationLatency  = "$context.integrationLatency"
      responseLatency     = "$context.responseLatency"
    })
  }

  # Enable detailed CloudWatch metrics
  xray_tracing_enabled = var.enable_xray

  tags = var.tags
} 