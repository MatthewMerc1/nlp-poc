# Development Environment - Using Modules
# This file shows how simple it becomes when using modules

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

# Use the S3 module - much simpler than 161 lines of S3 configuration!
module "data_bucket" {
  source = "../../modules/s3"

  bucket_name = var.bucket_name
  force_destroy = var.force_destroy
  
  folders = var.folders
  
  lifecycle_rules = var.lifecycle_rules

  tags = {
    Environment = "dev"
    Project     = "nlp-poc"
    Owner       = "data-team"
  }
}

# Use OpenSearch module
module "opensearch" {
  source = "../../modules/opensearch"

  domain_name     = var.opensearch_domain_name
  aws_region      = var.aws_region
  instance_type   = "t3.small.search"
  instance_count  = 1
  
  # VPC configuration
  vpc_cidr_block       = "10.0.0.0/16"
  public_subnet_cidr   = "10.0.0.0/24"
  private_subnet_cidr  = "10.0.1.0/24"
  
  # Security
  allowed_ipv4_addresses = var.allowed_ipv4_addresses
  allowed_ipv6_addresses = var.allowed_ipv6_addresses
  
  # Bastion configuration
  bastion_public_key = var.bastion_public_key
  
  tags = {
    Environment = "dev"
    Project     = "nlp-poc"
  }
}

# Use Lambda module
module "lambda" {
  source = "../../modules/lambda"

  function_name = "nlp-poc-semantic-search"
  lambda_zip_path = "lambda_function.zip"
  aws_region = var.aws_region
  
  # Set to true to manage Lambda function with Terraform
  create_lambda_function = true 
  
  # Increase timeout and memory for better performance
  timeout = 60
  memory_size = 512
  
  # Resource ARNs
  s3_bucket_arn = module.data_bucket.bucket_arn
  opensearch_domain_arn = module.opensearch.domain_arn
  api_gateway_execution_arn = module.api_gateway.execution_arn
  
  # Environment variables
  environment_variables = {
    OPENSEARCH_ENDPOINT = module.opensearch.domain_endpoint
    OPENSEARCH_INDEX    = "book-summaries"
    BEDROCK_MODEL_ID    = "amazon.titan-embed-text-v1"
    LOG_LEVEL           = "INFO"
  }
  
  # VPC configuration
  vpc_config = {
    subnet_ids         = [module.opensearch.private_subnet_id]
    security_group_ids = [module.opensearch.security_group_id]
  }
  
  tags = {
    Environment = "dev"
    Project     = "nlp-poc"
  }
}

# Use API Gateway module
module "api_gateway" {
  source = "../../modules/api_gateway"

  api_name = "nlp-poc-semantic-api"
  lambda_invoke_arn = module.lambda.function_invoke_arn
  
  # Set to false since log group already exists
  create_log_group = false
  
  tags = {
    Environment = "dev"
    Project     = "dev"
  }
}

# Use Monitoring module
module "monitoring" {
  source = "../../modules/monitoring"

  project_name = "nlp-poc"
  
  # Monitoring targets
  lambda_function_name = module.lambda.function_name
  api_gateway_name     = module.api_gateway.api_id
  api_gateway_stage    = "dev"
  opensearch_domain_name = module.opensearch.domain_name
  
  # Alert configuration
  alert_email_addresses = var.alert_email_addresses
  
  # Enable all monitoring
  enable_lambda_monitoring = true
  enable_api_monitoring    = true
  enable_opensearch_monitoring = true
  
  tags = {
    Environment = "dev"
    Project     = "nlp-poc"
  }
} 