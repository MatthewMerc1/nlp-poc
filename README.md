# NLP POC - Vector Search with Project Gutenberg Books

This project demonstrates a complete NLP pipeline for vector search using Project Gutenberg books, Amazon Bedrock embeddings, and OpenSearch.

## 📁 Project Structure

```
nlp-poc/
├── src/                    # Source code
│   ├── lambda/            # Lambda function
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── scripts/           # Core Python scripts
│   │   ├── upload_gutenberg.py      # Download books from Project Gutenberg
│   │   ├── generate_embeddings.py   # Generate embeddings using Bedrock
│   │   ├── check_embeddings.py      # Check generated embeddings
│   │   ├── load_embeddings_to_opensearch.py # Load embeddings to OpenSearch (legacy)
│   │   ├── load_embeddings_via_lambda.py    # Load embeddings via Lambda (recommended)
│   │   ├── upload_books.sh          # Shell script to upload books
│   │   ├── generate_embeddings.sh   # Shell script to generate embeddings
│   │   └── load_to_opensearch.sh    # Shell script to load to OpenSearch (updated)
│   └── api/               # API-related code (future)
├── infrastructure/        # Infrastructure as Code
│   ├── terraform/         # Terraform configurations
│   │   ├── main.tf        # Main Terraform configuration
│   │   ├── variables.tf   # Variable definitions
│   │   ├── outputs.tf     # Output values
│   │   ├── iam.tf         # IAM policies
│   │   ├── opensearch.tf  # OpenSearch domain
│   │   ├── s3.tf          # S3 bucket configuration
│   │   ├── monitoring.tf  # CloudWatch monitoring
│   │   ├── api_gateway.tf # API Gateway configuration
│   │   ├── terraform.tfvars # Variable values
│   │   └── .terraform/    # Generated files (gitignored)
│   └── scripts/           # Infrastructure scripts
│       ├── package_lambda.sh # Package Lambda function
│       └── teardown.sh       # Cleanup infrastructure
├── scripts/               # Orchestration scripts
│   ├── setup.sh           # Initial project setup
│   └── pipeline.sh        # Complete data pipeline
├── tests/                 # Test files
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── api/               # API tests
│       └── test_semantic_api.py
├── docs/                  # Documentation
│   ├── api/               # API documentation
│   ├── deployment/        # Deployment guides
│   └── architecture/      # Architecture diagrams
├── config/                # Configuration files
│   └── terraform.tfvars.example # Example Terraform variables
├── requirements.txt       # Python dependencies
├── Makefile              # Build and deployment commands
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🚀 Quick Start

### Option 1: Using Makefile (Recommended)

```bash
# Set up development environment
make setup

# Deploy infrastructure
make deploy

# Run complete data pipeline
make pipeline

# Test the API
make test

# Check project status
make status
```

### Option 2: Manual Steps

#### 1. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

**Note:** OpenSearch domain creation takes 10-15 minutes.

#### 2. Upload Books from Project Gutenberg

```bash
./src/scripts/upload_books.sh
```

#### 3. Generate Embeddings

```bash
./src/scripts/generate_embeddings.sh
```

#### 4. Load Embeddings into OpenSearch

**Option A: Lambda-based approach (Recommended)**
```bash
# Uses Lambda function to load embeddings (avoids connectivity issues)
./src/scripts/load_to_opensearch.sh

# Or use the Makefile command
make load-embeddings
```

**Option B: Direct approach (Legacy)**
```bash
# Direct OpenSearch connection (may have connectivity issues)
python src/scripts/load_embeddings_to_opensearch.py \
    --bucket "$BUCKET_NAME" \
    --opensearch-endpoint "https://$OPENSEARCH_ENDPOINT" \
    --profile "caylent-dev-test" \
    --index "book-embeddings"
```

#### 5. Package and Deploy Lambda

```bash
# Package Lambda function
./infrastructure/scripts/package_lambda.sh

# Deploy infrastructure
cd infrastructure/terraform
terraform apply
```

#### 6. Test Semantic Search API

```bash
# Test the API (automatically gets URL and API key from Terraform)
python tests/api/test_semantic_api.py "What is the meaning of life?"

# Or with custom size
python tests/api/test_semantic_api.py "What is the meaning of life?" 10
```

### 7. Access OpenSearch Dashboard

```bash
cd infrastructure/terraform
terraform output opensearch_dashboard_url
```

## 🛠️ Available Commands

The project includes a Makefile with convenient commands:

```bash
make help      # Show all available commands
make setup     # Set up development environment
make deploy    # Deploy infrastructure
make pipeline  # Run complete data pipeline
make load-embeddings # Load embeddings to OpenSearch via Lambda
make test      # Run API tests
make teardown  # Tear down infrastructure
make clean     # Clean up generated files
make package   # Package Lambda function
make status    # Show project status
```

## 📚 Books Included

The following books from Project Gutenberg are processed:

1. **Pride and Prejudice** - Jane Austen (899 chunks)
2. **The Great Gatsby** - F. Scott Fitzgerald (319 chunks)
3. **Alice's Adventures in Wonderland** - Lewis Carroll (178 chunks)
4. **Frankenstein** - Mary Shelley (518 chunks)
5. **The Adventures of Sherlock Holmes** - Arthur Conan Doyle (669 chunks)
6. **Dracula** - Bram Stoker
7. **The Picture of Dorian Gray** - Oscar Wilde
8. **The Time Machine** - H.G. Wells
9. **A Christmas Carol** - Charles Dickens
10. **The War of the Worlds** - H.G. Wells

## 🔧 Configuration

### Environment Variables

- `AWS_PROFILE`: Set to your AWS profile (default: `caylent-dev-test`)
- `AWS_REGION`: AWS region (default: `us-east-1`)

### Terraform Variables

Key variables in `infrastructure/terraform/terraform.tfvars`:

- `bucket_name`: S3 bucket name
- `opensearch_domain_name`: OpenSearch domain name
- `opensearch_instance_type`: OpenSearch instance type (default: `t3.small.search`)

## 🏗️ Infrastructure Components

### AWS Resources Created

1. **S3 Bucket** - Stores books and embeddings
2. **OpenSearch Domain** - Vector search database
3. **VPC & Networking** - Isolated network for OpenSearch
4. **IAM Policies** - Permissions for Bedrock and S3
5. **API Gateway** - REST API for semantic search
6. **Lambda Function** - Serverless semantic search handler

### OpenSearch Index Structure

- `book_title`: Text field for filtering
- `author`: Text field for filtering
- `chunk_index`: Integer for ordering
- `text`: Original text content
- `text_vector`: 1536-dimensional embedding vector

## 🔄 Lambda-Based Embedding Loading

The project now uses a **Lambda-based approach** for loading embeddings into OpenSearch, which provides several advantages:

### Why Lambda-Based Loading?

1. **No Connectivity Issues**: Lambda function is already in the VPC and can access OpenSearch
2. **More Secure**: No need to expose OpenSearch to the internet
3. **Reliable**: Avoids network timeouts and connection issues
4. **Scalable**: Can handle large datasets efficiently

### How It Works

1. **Lambda Function Enhancement**: The Lambda function now includes a `load_embeddings` action
2. **S3 Integration**: Reads embedding files from S3 bucket
3. **Bulk Indexing**: Uses OpenSearch bulk API for efficient loading
4. **Error Handling**: Comprehensive error handling and logging

### Usage

```bash
# Load all embeddings using the updated script
./src/scripts/load_to_opensearch.sh

# Or use the dedicated Makefile command
make load-embeddings

# Or run the Python script directly
python src/scripts/load_embeddings_via_lambda.py \
    --bucket "your-bucket-name" \
    --profile "your-aws-profile"
```
- `model_id`: Embedding model used
- `uploaded_at`: Timestamp

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
  "size": 5
}
```

**Response**:
```json
{
  "query": "What is the meaning of life?",
  "results": [
    {
      "score": 0.9234,
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "book_id": "gatsby",
      "chapter": "Chapter 1",
      "content": "In my younger and more vulnerable years my father gave me some advice..."
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
  -d '{"query": "What is the meaning of life?", "size": 5}'

# Using Python (automatically gets API key)
python scripts/test_semantic_api.py "What is the meaning of life?"
```

## 💰 Cost Estimation

- **OpenSearch**: ~$30/month (t3.small.search)
- **S3 Storage**: ~$0.023/GB/month
- **Bedrock Embeddings**: ~$0.0001 per 1K tokens
- **API Gateway**: ~$3.50/million requests
- **Lambda**: ~$0.20 per million requests + compute time
- **Data Transfer**: Minimal for this use case

## 🛠️ Development

### Running Scripts Manually

```bash
# Activate virtual environment
source venv/bin/activate

# Upload books
python scripts/upload_gutenberg.py --bucket "your-bucket" --profile "your-profile"

# Generate embeddings
python scripts/generate_embeddings.py --bucket "your-bucket" --profile "your-profile"

# Check embeddings
python scripts/check_embeddings.py --bucket "your-bucket" --profile "your-profile"

# Load to OpenSearch
python scripts/load_embeddings_to_opensearch.py \
  --bucket "your-bucket" \
  --opensearch-endpoint "your-opensearch-endpoint" \
  --profile "your-profile"
```

### Adding New Books

1. Update the book list in `scripts/upload_gutenberg.py`
2. Run `./upload_books.sh`
3. Run `./generate_embeddings.sh`
4. Run `./load_to_opensearch.sh`

## 🔒 Security Notes

- OpenSearch access is currently open for development
- Restrict IP access in production

## 🔒 Security Best Practices

This project implements several security best practices:

### S3 Security
- **Server-side encryption** enabled with AES256
- **Public access blocked** completely
- **Bucket policy** enforces encryption for uploads
- **Versioning enabled** for data protection
- **Lifecycle policies** for cost optimization

### OpenSearch Security
- **Fine-grained access control** enabled
- **IP restrictions** via security groups and access policies
- **Encryption at rest** and in transit
- **VPC isolation** for network security

### API Gateway Security
- **API key authentication** required
- **Usage plans** with rate limiting (10 req/sec, 1000/day)
- **CloudWatch logging** for audit trails
- **CORS configuration** for web access

### Lambda Security
- **VPC isolation** for network security
- **IAM least privilege** principles
- **Environment variable encryption** (consider using AWS Secrets Manager for production)
- **Reserved concurrency** to prevent resource exhaustion

## 📊 Monitoring & Observability

### CloudWatch Alarms
The following alarms are configured:
- **Lambda Errors**: Alerts when error rate exceeds 5 errors per 5 minutes
- **Lambda Duration**: Alerts when execution time exceeds 25 seconds
- **API Gateway 4XX Errors**: Alerts when client errors exceed 10 per 5 minutes
- **API Gateway 5XX Errors**: Alerts when server errors exceed 5 per 5 minutes
- **OpenSearch Health**: Alerts when cluster status is not green

### Logging
- **API Gateway logs** with detailed request/response information
- **Lambda logs** with structured logging
- **OpenSearch logs** for cluster monitoring

### Alerting
- **SNS topic** for centralized alerting
- **Email subscriptions** for immediate notification
- **Configurable thresholds** for different environments

## 🚀 Performance Optimizations

### Lambda Performance
- **Increased memory** to 1024MB for better CPU allocation
- **Reserved concurrency** to prevent throttling
- **VPC configuration** for low-latency OpenSearch access

### S3 Lifecycle Management
- **Automatic transitions** to cost-effective storage classes
- **Data retention policies** to manage storage costs
- **Incomplete multipart cleanup** to prevent orphaned uploads

## 🔄 Backup & Disaster Recovery

### Data Protection
- **S3 versioning** for point-in-time recovery
- **Cross-region replication** (consider for production)
- **Automated backups** via lifecycle policies

### Recovery Procedures
1. **Infrastructure recovery**: Use Terraform to recreate resources
2. **Data recovery**: Restore from S3 versions or cross-region copies
3. **Application recovery**: Redeploy Lambda functions and API Gateway

## 📋 Deployment Checklist

Before deploying to production:

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