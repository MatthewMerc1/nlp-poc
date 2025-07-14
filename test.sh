#!/bin/bash

# Usage: ./move_enhanced_to_book_summaries.sh <bucket-name> [--profile <aws-profile>]

BUCKET="$1"
PROFILE_ARG=""
if [[ "$2" == "--profile" && -n "$3" ]]; then
  PROFILE_ARG="--profile $3"
fi

if [[ -z "$BUCKET" ]]; then
  echo "Usage: $0 <bucket-name> [--profile <aws-profile>]"
  exit 1
fi

echo "Copying all objects from enhanced-book-summaries/ to book-summaries/ in bucket: $BUCKET"

# Copy all objects to new prefix
aws s3 cp s3://$BUCKET/enhanced-book-summaries/ s3://$BUCKET/book-summaries/ --recursive $PROFILE_ARG

if [[ $? -ne 0 ]]; then
  echo "Copy failed. Aborting delete step."
  exit 1
fi

echo "Copy complete. Deleting old objects from enhanced-book-summaries/ ..."

# Delete all objects from old prefix
aws s3 rm s3://$BUCKET/enhanced-book-summaries/ --recursive $PROFILE_ARG

echo "Move complete."