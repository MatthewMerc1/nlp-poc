#!/bin/bash

# Script to load embeddings into OpenSearch

# Get the bucket name from Terraform output
BUCKET_NAME=$(cd terraform && terraform output -raw bucket_name 2>/dev/null)

if [ -z "$BUCKET_NAME" ]; then
    echo "Error: Could not get bucket name from Terraform output."
    echo "Please run 'terraform apply' first to create the bucket."
    exit 1
fi

# Get the OpenSearch endpoint from Terraform output
OPENSEARCH_ENDPOINT=$(cd terraform && terraform output -raw opensearch_domain_endpoint 2>/dev/null)

if [ -z "$OPENSEARCH_ENDPOINT" ]; then
    echo "Error: Could not get OpenSearch endpoint from Terraform output."
    echo "Please run 'terraform apply' first to create the OpenSearch domain."
    exit 1
fi

echo "Found S3 bucket: $BUCKET_NAME"
echo "Found OpenSearch endpoint: $OPENSEARCH_ENDPOINT"

# Check if Python script exists
if [ ! -f "scripts/load_embeddings_to_opensearch.py" ]; then
    echo "Error: scripts/load_embeddings_to_opensearch.py not found"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

# Wait for OpenSearch to be ready
echo "Waiting for OpenSearch domain to be ready..."
echo "This may take 10-15 minutes for the domain to be fully operational."
echo "You can check the status in the AWS console."

# Run the loading script
echo "Starting embedding load to OpenSearch..."
python scripts/load_embeddings_to_opensearch.py \
    --bucket "$BUCKET_NAME" \
    --opensearch-endpoint "https://$OPENSEARCH_ENDPOINT" \
    --profile "caylent-dev-test" \
    --index "book-embeddings"

echo "Load complete!"
echo ""
echo "You can now access OpenSearch Dashboard at:"
echo "https://$OPENSEARCH_ENDPOINT/_dashboards/"
echo ""
echo "Or use the URL from Terraform output:"
cd terraform && terraform output opensearch_dashboard_url 