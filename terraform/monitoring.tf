# CloudWatch Alarms for monitoring

# Lambda Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "nlp-poc-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Lambda function error rate is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.semantic_lambda.function_name
  }

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-lambda-errors-alarm"
    Purpose      = "lambda-monitoring"
    ResourceType = "cloudwatch-alarm"
  })
}

# Lambda Duration Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "nlp-poc-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "25000" # 25 seconds
  alarm_description   = "Lambda function is taking too long to execute"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.semantic_lambda.function_name
  }

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-lambda-duration-alarm"
    Purpose      = "lambda-monitoring"
    ResourceType = "cloudwatch-alarm"
  })
}

# API Gateway 4XX Errors Alarm
resource "aws_cloudwatch_metric_alarm" "api_4xx_errors" {
  alarm_name          = "nlp-poc-api-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "API Gateway 4XX error rate is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiName = aws_api_gateway_rest_api.semantic_api.name
    Stage   = aws_api_gateway_stage.semantic_stage.stage_name
  }

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-api-4xx-errors-alarm"
    Purpose      = "api-monitoring"
    ResourceType = "cloudwatch-alarm"
  })
}

# API Gateway 5XX Errors Alarm
resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "nlp-poc-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "API Gateway 5XX error rate is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiName = aws_api_gateway_rest_api.semantic_api.name
    Stage   = aws_api_gateway_stage.semantic_stage.stage_name
  }

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-api-5xx-errors-alarm"
    Purpose      = "api-monitoring"
    ResourceType = "cloudwatch-alarm"
  })
}

# OpenSearch Cluster Health Alarm
resource "aws_cloudwatch_metric_alarm" "opensearch_health" {
  alarm_name          = "nlp-poc-opensearch-health"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ClusterStatus.green"
  namespace           = "AWS/ES"
  period              = "300"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "OpenSearch cluster is not healthy"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DomainName = aws_opensearch_domain.embeddings_domain.domain_name
    ClientId   = data.aws_caller_identity.current.account_id
  }

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-opensearch-health-alarm"
    Purpose      = "opensearch-monitoring"
    ResourceType = "cloudwatch-alarm"
  })
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "nlp-poc-alerts"

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-alerts-topic"
    Purpose      = "alerting"
    ResourceType = "sns-topic"
  })
}

# SNS Topic Subscription (email)
resource "aws_sns_topic_subscription" "alerts_email" {
  count     = length(var.alert_email_addresses)
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email_addresses[count.index]
}

# Data source for current AWS account
data "aws_caller_identity" "current" {} 