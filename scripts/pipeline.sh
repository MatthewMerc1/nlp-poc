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

# Step 1: Upload books
echo ""
echo "📚 Step 1: Uploading books from Project Gutenberg..."
./src/scripts/upload_books.sh

# Step 2: Generate book summaries
echo ""
echo "📖 Step 2: Generating book-level summaries..."
BUCKET_NAME="$BUCKET_NAME" ./src/scripts/generate_book_summaries.sh

# Step 3: Load book summaries to OpenSearch
echo ""
echo "🔍 Step 3: Loading book summaries to OpenSearch..."
OPENSEARCH_ENDPOINT=$(cd infrastructure/terraform/environments/dev && terraform output -raw opensearch_endpoint 2>/dev/null)
BUCKET_NAME="$BUCKET_NAME" OPENSEARCH_ENDPOINT="$OPENSEARCH_ENDPOINT" ./src/scripts/load_book_summaries.sh

echo ""
echo "✅ Data pipeline completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run 'make test' to test the semantic search API"
echo "2. Access OpenSearch Dashboard: $(cd infrastructure/terraform/environments/dev && terraform output -raw opensearch_dashboard_url 2>/dev/null || echo 'Run terraform output opensearch_dashboard_url')" 