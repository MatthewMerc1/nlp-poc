.PHONY: help setup deploy deploy-full package deploy-lambda pipeline test teardown clean upload-books

# Default target
help:
	@echo "Available commands:"
	@echo "  setup      - Set up the development environment"
	@echo "  deploy     - Deploy infrastructure (without Lambda)"
	@echo "  deploy-full- Deploy complete infrastructure with Lambda"
	@echo "  package    - Package Lambda function"
	@echo "  deploy-lambda - Package and deploy Lambda function to AWS"
	@echo "  pipeline   - Run the complete data pipeline"
	@echo "  generate-summaries - Generate book summaries"
	@echo "  bulk-index-summaries - Bulk index summaries to OpenSearch (direct)"
	@echo "  test       - Run API tests"
	@echo "  teardown   - Tear down infrastructure"
	@echo "  clean      - Clean up generated files"
	@echo "  upload-books - Upload 100 books from Project Gutenberg to S3 (scalable)"

# Set up development environment
setup:
	@echo "Setting up development environment..."
	@./scripts/setup.sh

# Deploy infrastructure
deploy:
	@echo "Deploying infrastructure..."
	@echo "Note: Run 'make package' first to create the Lambda ZIP file."
	@
	

# Deploy with Lambda (packages and deploys everything)
deploy-full:
	@echo "Packaging and deploying complete infrastructure..."
	@make package
	@cd infrastructure/terraform/environments/dev && terraform init && terraform plan && terraform apply

# Run the complete data pipeline
pipeline:
	@echo "Running data pipeline..."
	@./scripts/pipeline.sh



# Generate book summaries
generate-summaries:
	@echo "Generating book summaries..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	python ../../../../src/scripts/generate_book_summaries.py --bucket "$$BUCKET_NAME" --profile caylent-test --max-workers 4 --batch-size 50 $(ARGS)

# Load summaries to OpenSearch (bypasses Lambda)
load-summaries:
	@echo "Loading summaries  to OpenSearch..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	OPENSEARCH_ENDPOINT=$$(terraform output -raw opensearch_serverless_collection_endpoint 2>/dev/null) && \
	python ../../../../src/scripts/load_book_summaries_to_opensearch.py --bucket "$$BUCKET_NAME" --opensearch-endpoint "$$OPENSEARCH_ENDPOINT" --profile caylent-test

# Bulk index summaries to OpenSearch
bulk-index-summaries:
	@echo "Bulk indexing summaries to OpenSearch..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	OPENSEARCH_ENDPOINT=$$(terraform output -raw opensearch_serverless_collection_endpoint 2>/dev/null) && \
	python ../../../../src/scripts/load_book_summaries_to_opensearch.py --bucket "$$BUCKET_NAME" --opensearch-endpoint "$$OPENSEARCH_ENDPOINT" --profile caylent-test --batch-size 100

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
		--profile caylent-test \
		--region us-east-1
	@echo "Lambda function deployed successfully!"

# Upload books from Project Gutenberg
upload-books:
	@echo "Uploading books from Project Gutenberg to S3..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	python ../../../../src/scripts/upload_gutenberg.py --bucket "$$BUCKET_NAME" --profile caylent-test --limit 100

# Show project status
status:
	@echo "Project Status:"
	@echo "  Virtual environment: $(shell [ -d "venv" ] && echo "✓ Created" || echo "✗ Not created")"
	@echo "  Terraform state: $(shell [ -f "infrastructure/terraform/environments/dev/terraform.tfstate" ] && echo "✓ Deployed" || echo "✗ Not deployed")"
	@echo "  Lambda package: $(shell [ -f "infrastructure/terraform/environments/dev/lambda_function.zip" ] && echo "✓ Packaged" || echo "✗ Not packaged")"



 