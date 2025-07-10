# NLP POC - Book Recommendation System

This project demonstrates a complete book recommendation system using Project Gutenberg books, Amazon Bedrock embeddings, and OpenSearch. The system provides semantic book recommendations based on user queries like "gothic horror with female protagonist".

## 📁 Project Structure

```
nlp-poc/
├── src/                    # Source code
│   ├── lambda/            # Lambda function
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── scripts/           # Core Python scripts
│   │   ├── generate_book_embeddings.py      # Generate book embeddings for recommendations
│   │   ├── load_book_embeddings_to_opensearch.py # Load book embeddings to OpenSearch
│   │   ├── generate_book_embeddings.sh      # Shell script to generate book embeddings
│   │   └── load_book_embeddings.sh          # Shell script to load book embeddings
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
│       └── test_book_recommendations.py
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

#### 2. Generate Book Embeddings for Recommendations

```bash
# Generate embeddings for entire books (not content chunks)
./src/scripts/generate_book_embeddings.sh

# Or use the Makefile command
make generate-book-embeddings
```

#### 3. Load Book Embeddings into OpenSearch

```bash
# Load book embeddings for recommendations
./src/scripts/load_book_embeddings.sh

# Or use the Makefile command
make load-book-embeddings
```

#### 5. Package and Deploy Lambda

```bash
# Package Lambda function
./infrastructure/scripts/package_lambda.sh

# Deploy infrastructure
cd infrastructure/terraform
terraform apply
```

#### 4. Test Book Recommendation API

```bash
# Test the API (automatically gets URL and API key from Terraform)
python tests/api/test_book_recommendations.py "gothic horror with female protagonist"

# Or with custom size
python tests/api/test_book_recommendations.py "mystery detective fiction" 10
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
make generate-book-embeddings # Generate book embeddings for recommendations
make load-book-embeddings # Load book embeddings to OpenSearch
make test      # Run API tests
make teardown  # Tear down infrastructure
make clean     # Clean up generated files
make package   # Package Lambda function
make status    # Show project status
```

## 📚 Books Included

The following books from Project Gutenberg are included with metadata and embeddings:

1. **Pride and Prejudice** - Jane Austen (Romance, Classic Literature)
2. **The Great Gatsby** - F. Scott Fitzgerald (Literary Fiction, Classic Literature)
3. **Alice's Adventures in Wonderland** - Lewis Carroll (Fantasy, Children's Literature)
4. **Frankenstein** - Mary Shelley (Gothic Fiction, Science Fiction, Horror)
5. **The Adventures of Sherlock Holmes** - Arthur Conan Doyle (Mystery, Detective Fiction)
6. **Dracula** - Bram Stoker (Gothic Fiction, Horror, Vampire Fiction)
7. **The Picture of Dorian Gray** - Oscar Wilde (Gothic Fiction, Philosophical Fiction)
8. **The Time Machine** - H.G. Wells (Science Fiction, Time Travel)
9. **A Christmas Carol** - Charles Dickens (Classic Literature, Christmas Fiction)
10. **The War of the Worlds** - H.G. Wells (Science Fiction, Alien Invasion)

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
- `genre`: Text field for filtering
- `description`: Text field for filtering
- `gutenberg_id`: Keyword field for exact matching
- `book_vector`: 1536-dimensional embedding vector for recommendations

## 🔄 Book Recommendation System

The project now provides **semantic book recommendations** instead of content search. Key features:

### Key Features

- **Semantic Understanding**: Uses embeddings to understand book themes and content
- **Rich Metadata**: Includes genre, author, and descriptions for better recommendations
- **Scalable**: Can handle hundreds of thousands of books
- **Fast**: Vector similarity search provides instant recommendations

### How It Works

1. **Book Processing**: Books are downloaded and metadata is extracted
2. **Embedding Generation**: Entire books are embedded (not just chunks)
3. **Vector Storage**: Book embeddings are stored in OpenSearch
4. **Semantic Search**: User queries are embedded and matched to similar books

### Example Queries

- "gothic horror with female protagonist"
- "mystery detective fiction"
- "science fiction time travel"
- "romance classic literature"
- "fantasy children's books"

## 🔍 Book Recommendation Features

- **Semantic Search**: Find similar books using vector similarity
- **HNSW Algorithm**: Fast approximate nearest neighbor search
- **Cosine Similarity**: Semantic matching metric
- **Rich Metadata**: Genre, author, and description filtering

## 🌐 API Usage

### Book Recommendation Endpoint

**URL**: `POST /search`

**Request Body**:
```json
{
  "query": "gothic horror with female protagonist",
  "size": 5
}
```

**Response**:
```json
{
  "query": "gothic horror with female protagonist",
  "recommendations": [
    {
      "score": 0.9234,
      "title": "Frankenstein",
      "author": "Mary Shelley",
      "genre": "Gothic Fiction, Science Fiction, Horror",
      "description": "A Gothic horror novel about a scientist who creates a monster and the consequences of playing God, exploring themes of creation and responsibility.",
      "gutenberg_id": "84"
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
  -d '{"query": "gothic horror with female protagonist", "size": 5}'

# Using Python (automatically gets API key)
python tests/api/test_book_recommendations.py "gothic horror with female protagonist"
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

# Generate book embeddings
python src/scripts/generate_book_embeddings.py --bucket "your-bucket" --profile "your-profile"

# Load book embeddings to OpenSearch
python src/scripts/load_book_embeddings_to_opensearch.py \
  --bucket "your-bucket" \
  --opensearch-endpoint "your-opensearch-endpoint" \
  --profile "your-profile"
```

### Adding New Books

1. Update the book list in `src/scripts/generate_book_embeddings.py`
2. Run `./src/scripts/generate_book_embeddings.sh`
3. Run `./src/scripts/load_book_embeddings.sh`

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