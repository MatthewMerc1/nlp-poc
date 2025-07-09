#!/bin/bash

# NLP POC Infrastructure Teardown Script
# This script will completely remove all infrastructure to stop billing

set -e

echo "🗑️  Starting NLP POC Infrastructure Teardown..."
echo "⚠️  WARNING: This will permanently delete all data!"
echo ""

# Confirm before proceeding
read -p "Are you sure you want to destroy all infrastructure? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Teardown cancelled."
    exit 0
fi

echo ""
echo "📋 Step 1: Destroying Terraform infrastructure..."

cd terraform

# Check if terraform is initialized
if [ ! -d ".terraform" ]; then
    echo "Initializing Terraform..."
    terraform init
fi

# Destroy infrastructure
echo "Running terraform destroy..."
terraform destroy -auto-approve

echo ""
echo "📋 Step 2: Cleaning up local files..."

# Remove Terraform files
rm -rf .terraform/
rm -f terraform.tfstate*
rm -f .terraform.lock.hcl
rm -f lambda_function.zip

echo ""
echo "📋 Step 3: Verifying cleanup..."

# Check for remaining resources
echo "Checking for remaining S3 buckets..."
aws s3 ls | grep nlp-poc || echo "No nlp-poc S3 buckets found"

echo "Checking for remaining OpenSearch domains..."
aws es list-domain-names | grep nlp-poc || echo "No nlp-poc OpenSearch domains found"

echo "Checking for remaining Lambda functions..."
aws lambda list-functions | grep nlp-poc || echo "No nlp-poc Lambda functions found"

echo "Checking for remaining API Gateways..."
aws apigateway get-rest-apis | grep nlp-poc || echo "No nlp-poc API Gateways found"

echo ""
echo "✅ Teardown complete!"
echo "💰 All billing should now be stopped."
echo ""
echo "📊 Estimated monthly costs that were saved:"
echo "   - OpenSearch: ~$30/month"
echo "   - S3 Storage: ~$0.023/GB/month"
echo "   - API Gateway: ~$3.50/million requests"
echo "   - Lambda: ~$0.20 per million requests"
echo ""
echo "🔄 To redeploy in the future, run:"
echo "   cd terraform && terraform init && terraform apply" 