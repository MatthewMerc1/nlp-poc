#!/bin/bash

# Book recommendation pipeline orchestration script
set -e

echo "🔄 Starting Book Recommendation Pipeline..."

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

# Step 1: Generate book embeddings
echo ""
echo "📚 Step 1: Generating book embeddings for recommendations..."
./src/scripts/generate_book_embeddings.sh

# Step 2: Load book embeddings to OpenSearch
echo ""
echo "🔍 Step 2: Loading book embeddings to OpenSearch..."
./src/scripts/load_book_embeddings.sh

echo ""
echo "✅ Book recommendation pipeline completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run 'make test' to test the book recommendation API"
echo "2. Try: python tests/api/test_book_recommendations.py 'gothic horror with female protagonist'"
echo "3. Access OpenSearch Dashboard: $(cd infrastructure/terraform/environments/dev && terraform output -raw opensearch_dashboard_url 2>/dev/null || echo 'Run terraform output opensearch_dashboard_url')" 