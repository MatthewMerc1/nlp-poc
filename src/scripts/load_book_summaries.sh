#!/bin/bash

# Script to load book summaries into OpenSearch via Lambda function
# This avoids VPC connection issues by using the Lambda function that's already in the VPC

# Get the bucket name from environment or Terraform output
BUCKET_NAME=${BUCKET_NAME:-$(cd infrastructure/terraform/environments/dev && terraform output -raw bucket_name 2>/dev/null)}

if [ -z "$BUCKET_NAME" ]; then
    echo "Error: Could not get bucket name. Please set BUCKET_NAME environment variable or run 'make deploy' first."
    exit 1
fi

# Set AWS profile (can be overridden by environment variable)
AWS_PROFILE=${AWS_PROFILE:-"caylent-dev-test"}

echo "Starting book summary loading..."
echo "Bucket: $BUCKET_NAME"
echo "AWS Profile: $AWS_PROFILE"
echo "=================================="

# Check if Python script exists
if [ ! -f "src/scripts/load_book_summaries_via_lambda.py" ]; then
    echo "Error: src/scripts/load_book_summaries_via_lambda.py not found"
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

# Run the Lambda-based loading script
echo "Starting book summary loading via Lambda..."
python src/scripts/load_book_summaries_via_lambda.py --bucket "$BUCKET_NAME" --profile "$AWS_PROFILE"

echo "Book summary loading complete!" 