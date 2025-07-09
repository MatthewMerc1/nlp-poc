#!/bin/bash

# Data pipeline orchestration script
set -e

echo "🔄 Starting NLP POC data pipeline..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Run './scripts/setup.sh' first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if infrastructure is deployed
echo "🔍 Checking infrastructure status..."
if [ ! -f "infrastructure/terraform/.terraform/terraform.tfstate" ]; then
    echo "❌ Error: Infrastructure not deployed. Run 'make deploy' first."
    exit 1
fi

# Get bucket name from Terraform output
BUCKET_NAME=$(cd infrastructure/terraform && terraform output -raw bucket_name 2>/dev/null)
if [ -z "$BUCKET_NAME" ]; then
    echo "❌ Error: Could not get bucket name from Terraform output."
    echo "Please run 'make deploy' first to create the infrastructure."
    exit 1
fi

echo "✅ Found S3 bucket: $BUCKET_NAME"

# Step 1: Upload books
echo ""
echo "📚 Step 1: Uploading books from Project Gutenberg..."
./src/scripts/upload_books.sh

# Step 2: Generate embeddings
echo ""
echo "🧠 Step 2: Generating embeddings..."
./src/scripts/generate_embeddings.sh

# Step 3: Load to OpenSearch
echo ""
echo "🔍 Step 3: Loading embeddings to OpenSearch..."
./src/scripts/load_to_opensearch.sh

echo ""
echo "✅ Data pipeline completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run 'make package' to package the Lambda function"
echo "2. Run 'make deploy' to deploy the API"
echo "3. Run 'make test' to test the semantic search API" 