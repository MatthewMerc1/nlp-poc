#!/bin/bash

# Script to package Lambda function with dependencies

set -e

echo "Packaging Lambda function..."

# Create a temporary directory for packaging
PACKAGE_DIR="lambda_package"
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR

# Copy Lambda function code
cp src/lambda/lambda_function.py $PACKAGE_DIR/

# Install dependencies
pip install -r src/lambda/requirements.txt -t $PACKAGE_DIR/

# Create ZIP file in terraform directory
cd $PACKAGE_DIR
zip -r ../infrastructure/terraform/environments/dev/lambda_function.zip .
cd ..

# Clean up
rm -rf $PACKAGE_DIR

echo "Lambda function packaged as infrastructure/terraform/environments/dev/lambda_function.zip"
echo "You can now run: cd infrastructure/terraform/environments/dev && terraform apply" 