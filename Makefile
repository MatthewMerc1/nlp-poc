.PHONY: help setup deploy deploy-full package deploy-lambda pipeline test teardown clean

# Default target
help:
	@echo "Available commands:"
	@echo "  setup      - Set up the development environment"
	@echo "  deploy     - Deploy infrastructure (without Lambda)"
	@echo "  deploy-full- Deploy complete infrastructure with Lambda"
	@echo "  package    - Package Lambda function"
	@echo "  deploy-lambda - Package and deploy Lambda function to AWS"
	@echo "  pipeline   - Run the complete data pipeline"
	@echo "  generate-book-embeddings - Generate book embeddings for recommendations"
	@echo "  load-book-embeddings - Load book embeddings to OpenSearch"

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

# Generate book embeddings for recommendations
generate-book-embeddings:
	@echo "Generating book embeddings for recommendations..."
	@cd src/scripts && ./generate_book_embeddings.sh

# Load book embeddings to OpenSearch
load-book-embeddings:
	@echo "Loading book embeddings to OpenSearch..."
	@cd src/scripts && ./load_book_embeddings.sh



# Run tests
test:
	@echo "Running API tests..."
	@python tests/api/test_book_recommendations.py "gothic horror with female protagonist"

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

# Package and deploy Lambda function to AWS
deploy-lambda:
	@echo "Packaging and deploying Lambda function to AWS..."
	@make package
	@echo "Deploying to AWS Lambda..."
	@aws lambda update-function-code \
		--function-name nlp-poc-semantic-search \
		--zip-file fileb://infrastructure/terraform/environments/dev/lambda_function.zip \
		--profile caylent-dev-test
	@echo "Lambda function deployed successfully!"

# Show project status
status:
	@echo "Project Status:"
	@echo "  Virtual environment: $(shell [ -d "venv" ] && echo "✓ Created" || echo "✗ Not created")"
	@echo "  Terraform state: $(shell [ -f "infrastructure/terraform/environments/dev/terraform.tfstate" ] && echo "✓ Deployed" || echo "✗ Not deployed")"
	@echo "  Lambda package: $(shell [ -f "infrastructure/terraform/environments/dev/lambda_function.zip" ] && echo "✓ Packaged" || echo "✗ Not packaged")" 