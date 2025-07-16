.PHONY: help setup deploy deploy-full package deploy-lambda pipeline test teardown clean purge-index local-setup local-pipeline local-load-summaries local-generate-summaries local-check-index local-stop local-purge-index

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
	@echo "  load-summaries - Load book summaries to OpenSearch (via Lambda)"
	@echo "  load-summaries-direct - Load summaries directly (bypasses Lambda)"
	@echo "  bulk-index-summaries - Bulk index summaries to OpenSearch (direct)"
	@echo "  purge-index - Purge current OpenSearch index"
	@echo "  check-index - Check index status"
	@echo "  test       - Run API tests"
	@echo "  test-processing - Test book processing"
	@echo "  teardown   - Tear down infrastructure"
	@echo "  clean      - Clean up generated files"
	@echo ""
	@echo "Local Development Commands:"
	@echo "  local-setup - Set up local OpenSearch access"
	@echo "  local-pipeline - Run pipeline with local OpenSearch access"
	@echo "  local-generate-summaries - Generate summaries with local access"
	@echo "  local-load-summaries - Load summaries with local OpenSearch access"
	@echo "  local-check-index - Check index status with local access"
	@echo "  local-purge-index - Purge index with local OpenSearch access"
	@echo "  local-stop - Stop local OpenSearch access (kill SSH tunnel)"
	@echo "  upload-books - Upload 100 books from Project Gutenberg to S3 (scalable)"

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



# Generate book summaries
generate-summaries:
	@echo "Generating book summaries..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	python ../../../../src/scripts/generate_book_summaries.py --bucket "$$BUCKET_NAME" --profile caylent-dev-test --max-workers 4 --batch-size 50

# Load book summaries to OpenSearch
load-summaries:
	@echo "Loading book summaries to OpenSearch..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	OPENSEARCH_ENDPOINT=$$(terraform output -raw opensearch_serverless_collection_endpoint 2>/dev/null) && \
	cd ../../.. && \
	python src/scripts/load_book_summaries_to_opensearch.py --bucket "$$BUCKET_NAME" --opensearch-endpoint "$$OPENSEARCH_ENDPOINT" --profile caylent-dev-test

# Load summaries directly to OpenSearch (bypasses Lambda)
load-summaries-direct:
	@echo "Loading summaries directly to OpenSearch..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	OPENSEARCH_ENDPOINT=$$(terraform output -raw opensearch_serverless_collection_endpoint 2>/dev/null) && \
	python ../../../../src/scripts/bulk_index_to_opensearch.py --bucket "$$BUCKET_NAME" --opensearch-endpoint "$$OPENSEARCH_ENDPOINT" --profile caylent-dev-test --batch-size 100

# Bulk index summaries to OpenSearch
bulk-index-summaries:
	@echo "Bulk indexing summaries to OpenSearch..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	OPENSEARCH_ENDPOINT=$$(terraform output -raw opensearch_serverless_collection_endpoint 2>/dev/null) && \
	python ../../../../src/scripts/bulk_index_to_opensearch.py --bucket "$$BUCKET_NAME" --opensearch-endpoint "$$OPENSEARCH_ENDPOINT" --profile caylent-dev-test --batch-size 100

# Purge current OpenSearch index
purge-index:
	@echo "Purging current OpenSearch index..."
	@cd infrastructure/terraform/environments/dev && \
	OPENSEARCH_ENDPOINT=$$(terraform output -raw opensearch_serverless_collection_endpoint 2>/dev/null) && \
	cd ../../.. && \
	python src/scripts/purge_opensearch_direct.py --opensearch-endpoint "$$OPENSEARCH_ENDPOINT" --profile caylent-dev-test

# Check index status
check-index:
	@echo "Checking index status..."
	@cd infrastructure/terraform/environments/dev && \
	OPENSEARCH_ENDPOINT=$$(terraform output -raw opensearch_serverless_collection_endpoint 2>/dev/null) && \
	python ../../../../src/scripts/load_book_summaries_to_opensearch.py --opensearch-endpoint "$$OPENSEARCH_ENDPOINT" --profile caylent-dev-test --check-only

# Run tests
test:
	@echo "Running API tests..."
	@python tests/api/test_api.py "wonderland" multi 3

# Test processing
test-processing:
	@echo "Testing book processing..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	python ../../../../src/scripts/test_processing.py --bucket "$$BUCKET_NAME" --profile caylent-dev-test --max-books 3 --max-workers 2

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

# Upload books from Project Gutenberg
upload-books:
	@echo "Uploading books from Project Gutenberg to S3..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	python ../../../../src/scripts/upload_gutenberg.py --bucket "$$BUCKET_NAME" --profile caylent-dev-test --limit 100

# Show project status
status:
	@echo "Project Status:"
	@echo "  Virtual environment: $(shell [ -d "venv" ] && echo "✓ Created" || echo "✗ Not created")"
	@echo "  Terraform state: $(shell [ -f "infrastructure/terraform/environments/dev/terraform.tfstate" ] && echo "✓ Deployed" || echo "✗ Not deployed")"
	@echo "  Lambda package: $(shell [ -f "infrastructure/terraform/environments/dev/lambda_function.zip" ] && echo "✓ Packaged" || echo "✗ Not packaged")"

# Local Development Commands
local-setup:
	@echo "Setting up local OpenSearch access..."
	@./scripts/opensearch_local_access.sh

local-pipeline:
	@echo "Running pipeline with local OpenSearch access..."
	@./scripts/run_with_local_opensearch.sh "./scripts/pipeline.sh"

local-load-summaries:
	@echo "Loading summaries with local OpenSearch access..."
	@./scripts/opensearch_local_access.sh && \
	cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	python ../../../../src/scripts/bulk_index_to_opensearch.py --bucket "$$BUCKET_NAME" --opensearch-endpoint "localhost:8443" --profile caylent-dev-test --batch-size 100

local-generate-summaries:
	@echo "Generating summaries with local access..."
	@cd infrastructure/terraform/environments/dev && \
	BUCKET_NAME=$$(terraform output -raw bucket_name 2>/dev/null) && \
	cd ../../../.. && \
	python src/scripts/generate_book_summaries.py --bucket "$$BUCKET_NAME" --profile caylent-dev-test

local-check-index:
	@echo "Checking index status with local OpenSearch access..."
	@./scripts/opensearch_local_access.sh && \
	cd infrastructure/terraform/environments/dev && \
	python ../../../../src/scripts/load_book_summaries_to_opensearch.py --opensearch-endpoint "localhost:8443" --profile caylent-dev-test --check-only

local-purge-index:
	@echo "Purging index with local OpenSearch access..."
	@./scripts/opensearch_local_access.sh && \
	cd infrastructure/terraform/environments/dev && \
	python ../../../../src/scripts/purge_opensearch_direct.py --opensearch-endpoint "localhost:8443" --profile caylent-dev-test

local-stop:
	@echo "Stopping local OpenSearch access..."
	@./scripts/stop_opensearch_local_access.sh

 