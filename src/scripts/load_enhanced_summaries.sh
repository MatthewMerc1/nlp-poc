#!/bin/bash

# Script to load enhanced book summaries into OpenSearch via Lambda

set -e

# Configuration
BUCKET_NAME="nlp-poc-s3-data-2025"
AWS_PROFILE="caylent-dev-test"
AWS_REGION="us-east-1"

echo "Loading enhanced book summaries into OpenSearch..."
echo "Bucket: $BUCKET_NAME"
echo "Profile: $AWS_PROFILE"
echo "Region: $AWS_REGION"
echo "=================================="

# Get Lambda function name from Terraform
LAMBDA_FUNCTION_NAME=$(cd infrastructure/terraform/environments/dev && terraform output -raw lambda_function_name 2>/dev/null || echo "nlp-poc-lambda")

echo "Using Lambda function: $LAMBDA_FUNCTION_NAME"

# List enhanced book summaries in S3
echo "Listing enhanced book summaries in S3..."
ENHANCED_SUMMARIES=$(aws s3 ls s3://$BUCKET_NAME/enhanced-book-summaries/ --profile $AWS_PROFILE | grep "enhanced-summary.json" | awk '{print $4}')

if [ -z "$ENHANCED_SUMMARIES" ]; then
    echo "No enhanced book summaries found in S3!"
    echo "Please run the enhanced summary generation first:"
    echo "python src/scripts/generate_enhanced_summaries.py --bucket $BUCKET_NAME --profile $AWS_PROFILE"
    exit 1
fi

echo "Found enhanced summaries:"
echo "$ENHANCED_SUMMARIES"
echo ""

# Load each enhanced summary
SUCCESS_COUNT=0
TOTAL_COUNT=0

for summary_file in $ENHANCED_SUMMARIES; do
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    echo "Processing enhanced summary: $summary_file"
    
    # Download the enhanced summary from S3
    echo "Downloading enhanced summary from S3..."
    aws s3 cp s3://$BUCKET_NAME/enhanced-book-summaries/$summary_file /tmp/enhanced_summary.json --profile $AWS_PROFILE
    
    # Load the enhanced summary into OpenSearch via Lambda
    echo "Loading enhanced summary into OpenSearch via Lambda..."
    
    # Create the Lambda payload
    LAMBDA_PAYLOAD=$(cat <<EOF
{
    "action": "load_enhanced_book_summary",
    "book_summary_data": $(cat /tmp/enhanced_summary.json)
}
EOF
)
    
    # Invoke Lambda function
    LAMBDA_RESPONSE=$(aws lambda invoke \
        --function-name $LAMBDA_FUNCTION_NAME \
        --payload "$LAMBDA_PAYLOAD" \
        --profile $AWS_PROFILE \
        --region $AWS_REGION \
        /tmp/lambda_response.json)
    
    # Check if Lambda invocation was successful
    if [ $? -eq 0 ]; then
        # Parse Lambda response
        LAMBDA_STATUS=$(echo $LAMBDA_RESPONSE | jq -r '.StatusCode')
        LAMBDA_BODY=$(cat /tmp/lambda_response.json | jq -r '.body')
        
        if [ "$LAMBDA_STATUS" = "200" ]; then
            SUCCESS=$(echo $LAMBDA_BODY | jq -r '.success')
            if [ "$SUCCESS" = "true" ]; then
                echo "✅ Successfully loaded enhanced summary: $summary_file"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                echo "❌ Failed to load enhanced summary: $summary_file"
                echo "Lambda response: $LAMBDA_BODY"
            fi
        else
            echo "❌ Lambda invocation failed with status: $LAMBDA_STATUS"
            echo "Lambda response: $LAMBDA_BODY"
        fi
    else
        echo "❌ Failed to invoke Lambda function"
    fi
    
    echo ""
    
    # Clean up temporary files
    rm -f /tmp/enhanced_summary.json /tmp/lambda_response.json
    
    # Rate limiting - be respectful to AWS services
    sleep 1
done

echo "=================================="
echo "Enhanced summary loading complete!"
echo "Successfully loaded: $SUCCESS_COUNT/$TOTAL_COUNT enhanced summaries"
echo ""

# Check the enhanced index status
echo "Checking enhanced index status..."
LAMBDA_PAYLOAD='{"action": "check_enhanced_index"}'

LAMBDA_RESPONSE=$(aws lambda invoke \
    --function-name $LAMBDA_FUNCTION_NAME \
    --payload "$LAMBDA_PAYLOAD" \
    --profile $AWS_PROFILE \
    --region $AWS_REGION \
    /tmp/lambda_response.json)

if [ $? -eq 0 ]; then
    LAMBDA_BODY=$(cat /tmp/lambda_response.json | jq -r '.body')
    echo "Enhanced index status:"
    echo "$LAMBDA_BODY" | jq '.'
else
    echo "Failed to check enhanced index status"
fi

rm -f /tmp/lambda_response.json

echo ""
echo "Enhanced book summaries loaded successfully!"
echo "You can now use the enhanced search API with multiple strategies." 