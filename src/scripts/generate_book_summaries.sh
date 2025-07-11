#!/bin/bash

# Script to generate book-level summaries using hierarchical summarization

set -e

# Get configuration from environment or set defaults
BUCKET_NAME=${BUCKET_NAME:-""}
AWS_PROFILE=${AWS_PROFILE:-"caylent-dev-test"}
CHUNK_SIZE=${CHUNK_SIZE:-8000}
OVERLAP=${OVERLAP:-500}

# Check if bucket name is provided
if [ -z "$BUCKET_NAME" ]; then
    echo "Error: BUCKET_NAME environment variable is required"
    echo "Usage: BUCKET_NAME=your-bucket-name ./generate_book_summaries.sh"
    exit 1
fi

echo "Starting book summary generation..."
echo "Bucket: $BUCKET_NAME"
echo "AWS Profile: $AWS_PROFILE"
echo "Chunk Size: $CHUNK_SIZE"
echo "Overlap: $OVERLAP"
echo "=================================="

# Run the book summary generation script
python src/scripts/generate_book_summaries.py \
    --bucket "$BUCKET_NAME" \
    --profile "$AWS_PROFILE" \
    --chunk-size "$CHUNK_SIZE" \
    --overlap "$OVERLAP"

echo "Book summary generation complete!" 