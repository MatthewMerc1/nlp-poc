#!/bin/bash

# Script to load book summaries into OpenSearch

set -e

# Get configuration from environment or set defaults
BUCKET_NAME=${BUCKET_NAME:-""}
OPENSEARCH_ENDPOINT=${OPENSEARCH_ENDPOINT:-""}
AWS_PROFILE=${AWS_PROFILE:-"caylent-dev-test"}

# Check if required variables are provided
if [ -z "$BUCKET_NAME" ]; then
    echo "Error: BUCKET_NAME environment variable is required"
    echo "Usage: BUCKET_NAME=your-bucket-name OPENSEARCH_ENDPOINT=your-endpoint ./load_book_summaries.sh"
    exit 1
fi

if [ -z "$OPENSEARCH_ENDPOINT" ]; then
    echo "Error: OPENSEARCH_ENDPOINT environment variable is required"
    echo "Usage: BUCKET_NAME=your-bucket-name OPENSEARCH_ENDPOINT=your-endpoint ./load_book_summaries.sh"
    exit 1
fi

echo "Starting book summary loading..."
echo "Bucket: $BUCKET_NAME"
echo "OpenSearch Endpoint: $OPENSEARCH_ENDPOINT"
echo "AWS Profile: $AWS_PROFILE"
echo "=================================="

# Run the book summary loading script
python src/scripts/load_book_summaries_to_opensearch.py \
    --bucket "$BUCKET_NAME" \
    --opensearch-endpoint "$OPENSEARCH_ENDPOINT" \
    --profile "$AWS_PROFILE"

echo "Book summary loading complete!" 