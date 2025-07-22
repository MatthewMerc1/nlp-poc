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

module "vpc" {
  source  = "../../modules/vpc"
  vpc_cidr = "10.0.0.0/16"
  vpc_name = "nlp-poc-vpc"
  azs      = ["us-east-1a", "us-east-1b"]
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

# Add OpenSearch Serverless module
module "opensearch_serverless" {
  source                  = "../../modules/opensearch_serverless"
  collection_name         = var.opensearch_serverless_collection_name
  description             = var.opensearch_serverless_description
  data_access_policy_json = var.opensearch_serverless_data_access_policy_json
}

# Update Lambda module to use OpenSearch Serverless endpoint
module "lambda" {
  source = "../../modules/lambda"
  function_name = "nlp-poc-semantic-search"
  lambda_zip_path = "lambda_function.zip"
  aws_region = var.aws_region
  create_lambda_function = true
  timeout = 60
  memory_size = 512
  s3_bucket_arn = module.data_bucket.bucket_arn
  opensearch_serverless_collection_endpoint = module.opensearch_serverless.collection_endpoint
  opensearch_collection_name = var.opensearch_serverless_collection_name
  collection_id = module.opensearch_serverless.collection_id
  api_gateway_execution_arn = module.api_gateway.execution_arn
  environment_variables = {
    OPENSEARCH_ENDPOINT = module.opensearch_serverless.collection_endpoint
    OPENSEARCH_INDEX    = "book-summaries"
    BEDROCK_MODEL_ID    = "amazon.titan-embed-text-v1"
    LOG_LEVEL           = "INFO"
  }
  tags = {
    Environment = "dev"
    Project     = "nlp-poc"
  }
  # Enable Lambda to run in the VPC
  vpc_config = {
    subnet_ids         = module.vpc.private_subnet_ids
    security_group_ids = [module.vpc.batch_security_group_id]
  }
}

# Use API Gateway module
module "api_gateway" {
  source = "../../modules/api_gateway"

  api_name = "nlp-poc-semantic-api"
  lambda_invoke_arn = module.lambda.function_invoke_arn
  
  # Set to false since log group already exists
  create_log_group = true
  
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
  
  # Alert configuration
  alert_email_addresses = var.alert_email_addresses
  
  # Enable monitoring (OpenSearch Serverless doesn't need traditional monitoring)
  enable_lambda_monitoring = true
  enable_api_monitoring    = true
  enable_opensearch_monitoring = false
  
  tags = {
    Environment = "dev"
    Project     = "nlp-poc"
  }
} 

module "batch" {
  source = "../../modules/batch"

  compute_environment_name = "nlp-poc-batch-ce"
  job_queue_name           = "nlp-poc-batch-queue"
  job_definition_name      = "nlp-poc-batch-job"
  job_image                = "123456789012.dkr.ecr.us-east-1.amazonaws.com/your-batch-image:latest" # TODO: Update with your ECR image URI
  job_vcpus                = 2
  job_memory               = 4096
  job_command              = ["python", "your_script.py"] # TODO: Update as needed
  job_environment          = []
  aws_region               = var.aws_region

  max_vcpus                = 32
  min_vcpus                = 0
  desired_vcpus            = 0
  instance_types           = ["m5.large"]

  subnet_ids               = module.vpc.private_subnet_ids
  security_group_ids       = [module.vpc.batch_security_group_id]
} 