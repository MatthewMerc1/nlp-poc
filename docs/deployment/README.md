# Deployment Guide

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Terraform** installed (v1.0+)
4. **Python 3.8+** installed
5. **Make** utility (optional, for convenience)

## Quick Deployment

### 1. Initial Setup
```bash
# Clone the repository
git clone <repository-url>
cd nlp-poc

# Set up development environment
make setup
```

### 2. Configure Variables
```bash
# Copy example configuration
cp config/terraform.tfvars.example infrastructure/terraform/terraform.tfvars

# Edit the configuration file
nano infrastructure/terraform/terraform.tfvars
```

### 3. Deploy Infrastructure
```bash
# Deploy all AWS resources
make deploy
```

**Note**: OpenSearch domain creation takes 10-15 minutes.

### 4. Process Data
```bash
# Run the complete data pipeline
make pipeline
```

### 5. Deploy API
```bash
# Package and deploy Lambda function
make package
make deploy
```

### 6. Test the API
```bash
# Test book recommendations
make test
```

## Manual Deployment Steps

### Infrastructure Deployment
```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### Data Processing
```bash
# Generate book embeddings
./src/scripts/generate_book_embeddings.sh

# Load book embeddings to OpenSearch
./src/scripts/load_book_embeddings.sh
```

### API Deployment
```bash
# Package Lambda
./infrastructure/scripts/package_lambda.sh

# Deploy
cd infrastructure/terraform
terraform apply
```

## Troubleshooting

### Common Issues

1. **Terraform State Lock**: If deployment fails, check for state locks
2. **OpenSearch Not Ready**: Wait 10-15 minutes after domain creation
3. **AWS Credentials**: Ensure proper AWS profile is configured
4. **Bedrock Access**: Verify Bedrock is available in your region

### Useful Commands

```bash
# Check project status
make status

# View Terraform outputs
cd infrastructure/terraform && terraform output

# Clean up resources
make teardown

# Clean generated files
make clean
```

## Cost Optimization

- Use `t3.small.search` for development
- Consider auto-scaling for production
- Monitor CloudWatch metrics
- Use S3 lifecycle policies for old data 