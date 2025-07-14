#!/bin/bash

# Enhanced Pipeline Script
# This script runs the complete enhanced pipeline for better search accuracy

set -e

echo "🚀 Enhanced NLP Pipeline - Better Search Accuracy"
echo "=================================================="
echo ""

# Check if AWS credentials are available
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity --profile caylent-dev-test >/dev/null 2>&1; then
    echo "❌ AWS credentials not available or expired"
    echo "Please run: aws sso login --profile caylent-dev-test"
    exit 1
fi
echo "✅ AWS credentials available"
echo ""

# Step 1: Deploy enhanced Lambda function
echo "Step 1: Deploying enhanced Lambda function..."
echo "This will replace the current Lambda with the enhanced version"
echo "Press Enter to continue or Ctrl+C to cancel..."
read -r

make deploy-enhanced-lambda
echo "✅ Enhanced Lambda function deployed"
echo ""

# Step 2: Run the enhanced pipeline
echo "Step 2: Running enhanced pipeline..."
echo "This will:"
echo "  - Purge the current OpenSearch index"
echo "  - Generate enhanced book summaries (takes 10-15 minutes)"
echo "  - Load enhanced summaries to OpenSearch"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read -r

make pipeline-enhanced
echo "✅ Enhanced pipeline complete!"
echo ""

# Step 3: Test the enhanced system
echo "Step 3: Testing enhanced search..."
echo "Running enhanced API tests..."
make test-enhanced
echo "✅ Enhanced tests complete!"
echo ""

echo "🎉 Enhanced pipeline successfully completed!"
echo ""
echo "You can now test the improved search accuracy:"
echo ""
echo "  # Test with different strategies"
echo "  python tests/api/test_enhanced_api.py 'wonderland' multi 3"
echo "  python tests/api/test_enhanced_api.py 'detective mystery' plot 3"
echo "  python tests/api/test_enhanced_api.py 'love story' thematic 3"
echo ""
echo "  # Compare strategies"
echo "  python tests/api/test_enhanced_api.py --compare 'monster creation'"
echo ""
echo "  # Test accuracy improvements"
echo "  python tests/api/test_enhanced_api.py --accuracy"
echo ""
echo "Expected improvements:"
echo "  - Better score differentiation"
echo "  - More relevant results"
echo "  - Strategy-specific matching"
echo "  - No more boilerplate text in summaries" 