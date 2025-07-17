#!/bin/bash

# Enhanced Pipeline Script
# This script runs the complete enhanced pipeline for better search accuracy

set -e

echo "🚀 Enhanced NLP Pipeline - Better Search Accuracy"
echo "=================================================="
echo ""

# Check if AWS credentials are available
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity --profile caylent-test >/dev/null 2>&1; then
    echo "❌ AWS credentials not available or expired"
    echo "Please run: aws sso login --profile caylent-test"
    exit 1
fi
echo "✅ AWS credentials available"
echo ""

# Step 1: Deploy Lambda function
echo "Step 1: Deploying Lambda function..."
echo "This will package and deploy the Lambda function"
echo "Press Enter to continue or Ctrl+C to cancel..."
read -r

make deploy-lambda
echo "✅ Lambda function deployed"
echo ""

# Step 2: Run the data pipeline
echo "Step 2: Running data pipeline..."
echo "This will:"
echo "  - Upload books from Project Gutenberg to S3"
echo "  - Generate book summaries (takes 10-15 minutes)"
echo "  - Load summaries to OpenSearch"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read -r

make upload-books
make generate-summaries
make load-summaries
echo "✅ Data pipeline complete!"
echo ""

# Step 3: Test the system
echo "Step 3: Testing search..."
echo "Running API tests..."
make test
echo "✅ Tests complete!"
echo ""

echo "🎉 Pipeline successfully completed!"
echo ""
echo "You can now test the semantic search:"
echo ""
echo "  # Test basic search"
echo "  python tests/api/test_api.py 'wonderland' multi 3"
echo "  python tests/api/test_api.py 'detective mystery' multi 3"
echo "  python tests/api/test_api.py 'love story' multi 3"
echo ""
echo "  # Test with different result counts"
echo "  python tests/api/test_api.py 'monster creation' multi 5"
echo ""
echo "Expected features:"
echo "  - Semantic search across book summaries"
echo "  - Relevant book recommendations"
echo "  - Clean, direct summaries without boilerplate" 