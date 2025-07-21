# NLP POC - Vector Search with Project Gutenberg Books

This project demonstrates a complete NLP pipeline for vector search using Project Gutenberg books, Amazon Bedrock embeddings, and OpenSearch.

## 📁 Project Structure

```
nlp-poc/
├── src/                    # Source code
│   ├── lambda/            # Lambda function
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── scripts/           # Core Python and shell scripts
│   │   ├── upload_gutenberg.py      # Download books from Project Gutenberg
│   │   ├── generate_book_summaries.py   # Generate book-level summaries (scalable, parallel)
│   │   ├── bulk_index_to_opensearch.py  # Bulk index summaries to OpenSearch
│   │   ├── load_book_summaries_to_opensearch.py # Load summaries to OpenSearch (direct)
│   │   ├── generate_book_summaries.sh   # Shell wrapper for summary generation
│   │   └── upload_books.sh              # Shell wrapper for uploading books
│   └── api/               # API-related code (future)
├── infrastructure/        # Infrastructure as Code
│   ├── terraform/         # Terraform configurations
│   │   ├── environments/dev/   # Dev environment configs
│   │   └── modules/           # Terraform modules
│   └── scripts/           # Infrastructure scripts
│       ├── package_lambda.sh # Package Lambda function
│       └── teardown.sh       # Cleanup infrastructure
├── scripts/               # Orchestration scripts
│   ├── setup.sh           # Initial project setup
│   └── pipeline.sh        # Complete data pipeline (Makefile: pipeline)
├── tests/                 # Test files
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── api/               # API tests
│       └── test_api.py    # Enhanced API test script
├── docs/                  # Documentation
├── config/                # Configuration files
│   └── terraform.tfvars.example # Example Terraform variables
├── requirements.txt       # Python dependencies
├── Makefile              # Build and deployment commands
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🚀 Quick Start

### Using Makefile (Recommended)

```bash
# Set up development environment
make setup

# Deploy infrastructure (without Lambda)
make deploy

# Deploy Lambda function (package and upload)
make deploy-lambda

# Run complete data pipeline (deploy Lambda, upload books, generate summaries, load to OpenSearch, test)
make pipeline

# Test the API
make test

# Check project status
make status
```

## 🛠️ Available Makefile Commands

```bash
make help                # Show all available commands
make setup               # Set up development environment
make deploy              # Deploy infrastructure (without Lambda)
make deploy-full         # Deploy complete infrastructure with Lambda
make package             # Package Lambda function
make deploy-lambda       # Package and deploy Lambda function to AWS
make pipeline            # Run the complete data pipeline (recommended)
make generate-summaries  # Generate book summaries (parallel, scalable)
make bulk-index-summaries# Bulk index summaries to OpenSearch (direct)
make load-summaries      # Load summaries to OpenSearch (direct, not via Lambda)
make test                # Run API tests
make teardown            # Tear down infrastructure
make clean               # Clean up generated files
make upload-books        # Upload 100 books from Project Gutenberg to S3
make status              # Show project status (virtualenv, Terraform, Lambda package)
```

## 🧩 Manual Steps (Advanced)

### 1. Upload Books from Project Gutenberg
```bash
make upload-books
# or manually:
BUCKET_NAME=your-bucket-name AWS_PROFILE=your-profile ./src/scripts/upload_books.sh
```

### 2. Generate Book-Level Summaries (Parallel, Scalable)
```bash
make generate-summaries
# or manually:
BUCKET_NAME=your-bucket-name AWS_PROFILE=your-profile ./src/scripts/generate_book_summaries.sh
# or directly:
python src/scripts/generate_book_summaries.py --bucket your-bucket-name --profile your-profile --max-workers 8 --batch-size 50
```

### 3. Load Book Summaries into OpenSearch
```bash
make load-summaries
# or manually:
python src/scripts/load_book_summaries_to_opensearch.py --bucket your-bucket-name --profile your-profile --opensearch-endpoint your-opensearch-endpoint
```

### 4. Bulk Index Summaries to OpenSearch (for large-scale loads)
```bash
make bulk-index-summaries
# or manually:
python src/scripts/bulk_index_to_opensearch.py --bucket your-bucket-name --profile your-profile --opensearch-endpoint your-opensearch-endpoint
```

### 5. Package and Deploy Lambda
```bash
make deploy-lambda
# or manually:
./infrastructure/scripts/package_lambda.sh
# then deploy with Terraform or AWS CLI
```

### 6. Test the API
```bash
make test
# or manually:
python tests/api/test_api.py 'your query' [strategy] [size]
python tests/api/test_api.py --compare 'your query'
python tests/api/test_api.py --accuracy
```

## 🧪 API Test Script Usage

The main API test script is `tests/api/test_api.py`. It supports multiple search strategies and enhanced output.

**Usage:**
```bash
python tests/api/test_api.py "your query" [strategy] [size]
python tests/api/test_api.py --compare "your query"
python tests/api/test_api.py --accuracy
```
- **Strategies:** multi, plot, thematic, character, combined
- **Examples:**
  - `python tests/api/test_api.py 'wonderland'`
  - `python tests/api/test_api.py 'detective mystery' plot 3`
  - `python tests/api/test_api.py --compare 'love story'`
  - `python tests/api/test_api.py --accuracy`

## 📚 Books Included

The following books from Project Gutenberg are processed (default set, can be expanded):

1. **Pride and Prejudice** - Jane Austen
2. **The Great Gatsby** - F. Scott Fitzgerald
3. **Alice's Adventures in Wonderland** - Lewis Carroll
4. **Frankenstein** - Mary Shelley
5. **The Adventures of Sherlock Holmes** - Arthur Conan Doyle
6. **Dracula** - Bram Stoker
7. **The Picture of Dorian Gray** - Oscar Wilde
8. **The Time Machine** - H.G. Wells
9. **A Christmas Carol** - Charles Dickens
10. **The War of the Worlds** - H.G. Wells

## 🔧 Configuration

### Environment Variables
- `AWS_PROFILE`: Set to your AWS profile (default: `caylent-test`)
- `AWS_REGION`: AWS region (default: `us-east-1`)

### Terraform Variables
Key variables in `infrastructure/terraform/environments/dev/terraform.tfvars`:
- `bucket_name`: S3 bucket name
- `opensearch_domain_name`: OpenSearch domain name

## 🏗️ Infrastructure Components

- **S3 Bucket**: Stores books and embeddings
- **OpenSearch Serverless**: Vector search database
- **API Gateway**: REST API for semantic search
- **Lambda Function**: Serverless semantic search handler
- **IAM Policies**: Permissions for Bedrock and S3
- **Monitoring**: CloudWatch alarms and logging

## 🔄 Book-Level Semantic Search Pipeline

- **Upload books** from Project Gutenberg to S3
- **Generate hierarchical summaries** for each book (parallel, scalable)
- **Generate embeddings** for summaries
- **Bulk index/load summaries** to OpenSearch
- **Query via API Gateway + Lambda**

## 📝 Script Reference

### Python Scripts (src/scripts/)
- `upload_gutenberg.py`: Download books from Project Gutenberg and upload to S3
- `generate_book_summaries.py`: Generate book-level summaries and embeddings (parallel, scalable)
- `bulk_index_to_opensearch.py`: Bulk index book summaries to OpenSearch (efficient for large datasets)
- `load_book_summaries_to_opensearch.py`: Load book summaries to OpenSearch (direct, not via Lambda)

### Shell Scripts (src/scripts/)
- `upload_books.sh`: Wrapper for uploading books
- `generate_book_summaries.sh`: Wrapper for summary generation

### Orchestration Scripts (scripts/)
- `pipeline.sh`: Runs the full pipeline (deploy Lambda, upload books, generate summaries, load to OpenSearch, test)
- `setup.sh`: Initial project setup

### Infrastructure Scripts (infrastructure/scripts/)
- `package_lambda.sh`: Package Lambda function for deployment
- `teardown.sh`: Tear down infrastructure

## 🔍 Vector Search Features

- **Semantic Search**: Find similar text using vector similarity
- **HNSW Algorithm**: Fast approximate nearest neighbor search
- **Cosine Similarity**: Semantic matching metric
- **Hybrid Search**: Combine vector and text search

## 🌐 API Usage

### Semantic Search Endpoint

**URL**: `POST /search`

**Request Body**:
```json
{
  "query": "What is the meaning of life?",
  "search_strategy": "multi",
  "size": 5
}
```

**Response**:
```json
{
  "query": "What is the meaning of life?",
  "search_strategy": "multi",
  "results": [
    {
      "score": 0.9234,
      "book_title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "summary": "..."
    }
  ],
  "total_results": 5
}
```

### Example Usage

```bash
# Using curl (replace YOUR_API_KEY with actual key from terraform output api_key)
curl -X POST "https://your-api-gateway-url/prod/search" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"query": "What is the meaning of life?", "search_strategy": "multi", "size": 5}'

# Using Python
env API_KEY=your-key API_URL=your-url python tests/api/test_api.py 'What is the meaning of life?'
```

## 🔒 Security & Monitoring

- **S3**: Server-side encryption, public access blocked, versioning enabled
- **OpenSearch**: Fine-grained access control, IP restrictions, encryption at rest/in transit
- **API Gateway**: API key authentication, usage plans, logging
- **Lambda**: VPC isolation, IAM least privilege
- **CloudWatch**: Alarms for errors, duration, and API metrics

## 📋 Deployment Checklist

- [ ] Update `allowed_ip_addresses` with production IP ranges
- [ ] Change default passwords in `terraform.tfvars`
- [ ] Configure alert email addresses
- [ ] Review and adjust rate limits
- [ ] Set up cross-region replication for S3
- [ ] Configure backup retention policies
- [ ] Test disaster recovery procedures
- [ ] Review IAM permissions for least privilege
- [ ] Set up monitoring dashboards
- [ ] Document runbooks for common issues 