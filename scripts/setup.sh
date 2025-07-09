#!/bin/bash

# Setup script for NLP POC project
set -e

echo "🚀 Setting up NLP POC development environment..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed"
    exit 1
fi

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is required but not installed"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if Terraform is available
if ! command -v terraform &> /dev/null; then
    echo "❌ Error: Terraform is required but not installed"
    echo "Install from: https://www.terraform.io/downloads"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "⚠️  Warning: AWS credentials not configured or invalid"
    echo "Please run: aws configure"
    echo "Or set AWS_PROFILE environment variable"
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure AWS credentials if needed"
echo "2. Copy config/terraform.tfvars.example to infrastructure/terraform/terraform.tfvars"
echo "3. Run 'make deploy' to deploy infrastructure"
echo "4. Run 'make pipeline' to process data" 