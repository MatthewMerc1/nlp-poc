# Architecture Overview

## System Components

### 1. Data Pipeline
- **Project Gutenberg Integration**: Downloads classic literature books
- **Text Processing**: Chunks text into manageable segments
- **Embedding Generation**: Uses Amazon Bedrock to create vector embeddings
- **Storage**: S3 bucket for books and embeddings

### 2. Search Infrastructure
- **OpenSearch Domain**: Vector search database with HNSW algorithm
- **Index Structure**: Optimized for semantic search
- **VPC**: Isolated network for security

### 3. API Layer
- **API Gateway**: REST API endpoint
- **Lambda Function**: Serverless semantic search handler
- **Authentication**: API key-based access control

## Data Flow

```
Project Gutenberg → S3 (Books) → Bedrock (Embeddings) → S3 (Embeddings) → OpenSearch → API Gateway → Lambda
```

## Security

- VPC isolation for OpenSearch
- IAM roles with least privilege
- API key authentication
- S3 bucket encryption

## Scalability

- Serverless Lambda functions
- Auto-scaling OpenSearch domain
- S3 for unlimited storage
- API Gateway for request management 