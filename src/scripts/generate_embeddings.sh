#!/bin/bash

# Script to generate embeddings for books using Amazon Bedrock

# Get the bucket name from Terraform output
BUCKET_NAME=$(cd infrastructure/terraform/environments/dev && terraform output -raw bucket_name 2>/dev/null)

if [ -z "$BUCKET_NAME" ]; then
    echo "Error: Could not get bucket name from Terraform output."
    echo "Please run 'make deploy' first to create the bucket."
    exit 1
fi

echo "Found S3 bucket: $BUCKET_NAME"

# Check if Python script exists
if [ ! -f "src/scripts/generate_embeddings.py" ]; then
    echo "Error: src/scripts/generate_embeddings.py not found"
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

# Check if Bedrock is available in the region
echo "Checking Bedrock availability..."
aws bedrock list-foundation-models --profile caylent-dev-test --region us-east-1 > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "Warning: Bedrock might not be available in us-east-1 region."
    echo "You may need to use a different region where Bedrock is available."
    echo "Common regions: us-west-2, eu-west-1, ap-southeast-1"
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run the embedding generation script
echo "Starting embedding generation..."
python src/scripts/generate_embeddings.py \
    --bucket "$BUCKET_NAME" \
    --profile "caylent-dev-test" \
    --model "amazon.titan-embed-text-v1" \
    --chunk-size 1000 \
    --overlap 100

echo "Embedding generation complete!" 