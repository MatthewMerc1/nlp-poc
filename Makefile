.PHONY: help setup deploy pipeline test teardown clean

# Default target
help:
	@echo "Available commands:"
	@echo "  setup      - Set up the development environment"
	@echo "  deploy     - Deploy infrastructure (without Lambda)"
	@echo "  deploy-full- Deploy complete infrastructure with Lambda"
	@echo "  package    - Package Lambda function"
	@echo "  pipeline   - Run the complete data pipeline"
	@echo "  load-embeddings - Load embeddings to OpenSearch via Lambda"
	@echo "  test       - Run API tests"
	@echo "  teardown   - Tear down infrastructure"
	@echo "  clean      - Clean up generated files"

# Set up development environment
setup:
	@echo "Setting up development environment..."
	@./scripts/setup.sh

# Deploy infrastructure
deploy:
	@echo "Deploying infrastructure..."
	@echo "Note: Run 'make package' first to create the Lambda ZIP file."
	@cd infrastructure/terraform/environments/dev && terraform init && terraform plan && terraform apply

# Deploy with Lambda (packages and deploys everything)
deploy-full:
	@echo "Packaging and deploying complete infrastructure..."
	@make package
	@cd infrastructure/terraform/environments/dev && terraform init && terraform plan && terraform apply

# Run the complete data pipeline
pipeline:
	@echo "Running data pipeline..."
	@./scripts/pipeline.sh

# Load embeddings to OpenSearch via Lambda
load-embeddings:
	@echo "Loading embeddings to OpenSearch via Lambda..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	python ../../src/scripts/load_embeddings_via_lambda.py --bucket "$$BUCKET_NAME" --profile caylent-dev-test

# Run tests
test:
	@echo "Running API tests..."
	@python tests/api/test_semantic_api.py "test query"

# Tear down infrastructure
teardown:
	@echo "Tearing down infrastructure..."
	@./infrastructure/scripts/teardown.sh

# Clean up generated files
clean:
	@echo "Cleaning up generated files..."
	@rm -rf infrastructure/terraform/environments/dev/.terraform/terraform.tfstate*
	@rm -rf infrastructure/terraform/environments/dev/.terraform/lambda_function.zip
	@echo "Cleanup complete!"

# Package Lambda function
package:
	@echo "Packaging Lambda function..."
	@./infrastructure/scripts/package_lambda.sh

# Show project status
status:
	@echo "Project Status:"
	@echo "  Virtual environment: $(shell [ -d "venv" ] && echo "✓ Created" || echo "✗ Not created")"
	@echo "  Terraform state: $(shell [ -f "infrastructure/terraform/environments/dev/terraform.tfstate" ] && echo "✓ Deployed" || echo "✗ Not deployed")"
	@echo "  Lambda package: $(shell [ -f "infrastructure/terraform/environments/dev/lambda_function.zip" ] && echo "✓ Packaged" || echo "✗ Not packaged")" 