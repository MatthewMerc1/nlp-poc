#!/bin/bash

# Load embeddings to OpenSearch via Lambda
# This script uses the Lambda function to load embeddings, avoiding direct OpenSearch connectivity issues

set -e

echo "🔍 Loading embeddings to OpenSearch via Lambda..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Run './scripts/setup.sh' first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if infrastructure is deployed
if [ ! -f "infrastructure/terraform/environments/dev/terraform.tfstate" ]; then
    echo "❌ Error: Infrastructure not deployed. Run 'make deploy' first."
    exit 1
fi

# Get bucket name from Terraform output
BUCKET_NAME=$(cd infrastructure/terraform/environments/dev && terraform output -raw bucket_name 2>/dev/null)
if [ -z "$BUCKET_NAME" ]; then
    echo "❌ Error: Could not get bucket name from Terraform output."
    echo "Please run 'make deploy' first to create the infrastructure."
    exit 1
fi

echo "✅ Found S3 bucket: $BUCKET_NAME"

# Get OpenSearch endpoint for reference
OPENSEARCH_ENDPOINT=$(cd infrastructure/terraform/environments/dev && terraform output -raw opensearch_endpoint 2>/dev/null)
if [ -n "$OPENSEARCH_ENDPOINT" ]; then
    echo "✅ Found OpenSearch endpoint: $OPENSEARCH_ENDPOINT"
fi

echo "============================================================"
echo "Loading embeddings into OpenSearch via Lambda function..."
echo "This approach avoids direct connectivity issues by using the Lambda function"
echo "which is already in the VPC and has access to OpenSearch."
echo "============================================================"

# Load embeddings using the Lambda-based script
python src/scripts/load_embeddings_via_lambda.py --bucket "$BUCKET_NAME" --profile caylent-dev-test

echo ""
echo "✅ Load complete!"

# Get OpenSearch dashboard URL
DASHBOARD_URL=$(cd infrastructure/terraform/environments/dev && terraform output -raw opensearch_dashboard_url 2>/dev/null)
if [ -n "$DASHBOARD_URL" ]; then
    echo ""
    echo "You can now access OpenSearch Dashboard at:"
    echo "$DASHBOARD_URL"
    echo ""
    echo "Or use the URL from Terraform output:"
    echo "\"$DASHBOARD_URL\""
else
    echo ""
    echo "You can access OpenSearch Dashboard using:"
    echo "cd infrastructure/terraform/environments/dev && terraform output opensearch_dashboard_url"
fi 