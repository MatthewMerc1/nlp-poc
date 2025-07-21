#!/bin/bash

# Script to upload Project Gutenberg books to S3 bucket

# Get the bucket name from Terraform output
BUCKET_NAME=$(cd infrastructure/terraform/environments/dev && terraform output -raw bucket_name 2>/dev/null)

if [ -z "$BUCKET_NAME" ]; then
    echo "Error: Could not get bucket name from Terraform output."
    echo "Please run 'make deploy' first to create the bucket."
    exit 1
fi

echo "Found S3 bucket: $BUCKET_NAME"

# Check if Python script exists
if [ ! -f "src/scripts/upload_gutenberg.py" ]; then
    echo "Error: src/scripts/upload_gutenberg.py not found"
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

# Run the upload script
echo "Starting book upload..."
python src/scripts/upload_gutenberg.py --bucket "$BUCKET_NAME" --profile "caylent-test" --limit 5

echo "Upload complete!" 