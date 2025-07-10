# Monitoring Module - CloudWatch alarms, SNS topics, and alerting
# This module creates comprehensive monitoring for the NLP POC infrastructure

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"

  tags = var.tags
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

# Lambda Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count = var.enable_lambda_monitoring ? 1 : 0
  alarm_name          = "${var.project_name}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.alarm_evaluation_periods
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = var.alarm_period
  statistic           = "Sum"
  threshold           = var.lambda_error_threshold
  alarm_description   = "Lambda function error rate is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  dimensions = {
    FunctionName = var.lambda_function_name
  }
  tags = var.tags
}

# Lambda Duration Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  count = var.enable_lambda_monitoring ? 1 : 0
  alarm_name          = "${var.project_name}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.alarm_evaluation_periods
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = var.alarm_period
  statistic           = "Average"
  threshold           = var.lambda_duration_threshold
  alarm_description   = "Lambda function is taking too long to execute"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  dimensions = {
    FunctionName = var.lambda_function_name
  }
  tags = var.tags
}

# API Gateway 4XX Errors Alarm
resource "aws_cloudwatch_metric_alarm" "api_4xx_errors" {
  count = var.enable_api_monitoring ? 1 : 0

  alarm_name          = "${var.project_name}-api-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.alarm_evaluation_periods
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = var.alarm_period
  statistic           = "Sum"
  threshold           = var.api_4xx_error_threshold
  alarm_description   = "API Gateway 4XX error rate is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiName = var.api_gateway_name
    Stage   = var.api_gateway_stage
  }

  tags = var.tags
}

# API Gateway 5XX Errors Alarm
resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  count = var.enable_api_monitoring ? 1 : 0

  alarm_name          = "${var.project_name}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.alarm_evaluation_periods
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = var.alarm_period
  statistic           = "Sum"
  threshold           = var.api_5xx_error_threshold
  alarm_description   = "API Gateway 5XX error rate is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiName = var.api_gateway_name
    Stage   = var.api_gateway_stage
  }

  tags = var.tags
}

# OpenSearch Cluster Health Alarm
resource "aws_cloudwatch_metric_alarm" "opensearch_health" {
  count = var.enable_opensearch_monitoring ? 1 : 0

  alarm_name          = "${var.project_name}-opensearch-health"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = var.alarm_evaluation_periods
  metric_name         = "ClusterStatus.green"
  namespace           = "AWS/ES"
  period              = var.alarm_period
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "OpenSearch cluster is not healthy"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DomainName = var.opensearch_domain_name
    ClientId   = data.aws_caller_identity.current.account_id
  }

  tags = var.tags
} 