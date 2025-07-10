#!/bin/bash

# Script to load book embeddings into OpenSearch for recommendations

# Get the bucket name and OpenSearch endpoint from Terraform output
cd ../../infrastructure/terraform/environments/dev

BUCKET_NAME=$(terraform output -raw bucket_name 2>/dev/null)
OPENSEARCH_ENDPOINT=$(terraform output -raw opensearch_endpoint 2>/dev/null)

if [ -z "$BUCKET_NAME" ]; then
    echo "Error: Could not get bucket name from Terraform output."
    echo "Please run 'terraform apply' first to create the bucket."
    exit 1
fi

if [ -z "$OPENSEARCH_ENDPOINT" ]; then
    echo "Error: Could not get OpenSearch endpoint from Terraform output."
    echo "Please run 'terraform apply' first to create the OpenSearch domain."
    exit 1
fi

echo "Found S3 bucket: $BUCKET_NAME"
echo "Found OpenSearch endpoint: $OPENSEARCH_ENDPOINT"

cd ../../../src/scripts

# Check if Python script exists
if [ ! -f "load_book_embeddings_to_opensearch.py" ]; then
    echo "Error: load_book_embeddings_to_opensearch.py not found"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "../../venv" ]; then
    echo "Creating virtual environment..."
    cd ../..
    python3 -m venv venv
    cd src/scripts
fi

echo "Activating virtual environment..."
source ../../venv/bin/activate

echo "Installing dependencies..."
pip install -r ../../requirements.txt

# Run the book embedding loading script
echo "Starting to load book embeddings into OpenSearch..."
python load_book_embeddings_to_opensearch.py \
    --bucket "$BUCKET_NAME" \
    --opensearch-endpoint "https://$OPENSEARCH_ENDPOINT" \
    --profile "caylent-dev-test" \
    --index "book-recommendations"

echo "Book embedding loading complete!" 