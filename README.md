# NLP POC - Vector Search with Project Gutenberg Books

This project demonstrates a complete NLP pipeline for vector search using Project Gutenberg books, Amazon Bedrock embeddings, and OpenSearch.

## 📁 Project Structure

```
nlp-poc/
├── terraform/           # Infrastructure as Code
│   ├── main.tf         # Main Terraform configuration
│   ├── variables.tf    # Variable definitions
│   ├── outputs.tf      # Output values
│   ├── iam.tf          # IAM policies
│   ├── opensearch.tf   # OpenSearch domain
│   ├── terraform.tfvars # Variable values
│   └── terraform.tfvars.example # Example variables
├── scripts/            # Python scripts and shell scripts
│   ├── upload_gutenberg.py      # Download books from Project Gutenberg
│   ├── generate_embeddings.py   # Generate embeddings using Bedrock
│   ├── check_embeddings.py      # Check generated embeddings
│   ├── load_embeddings_to_opensearch.py # Load embeddings to OpenSearch
│   ├── upload_books.sh          # Shell script to upload books
│   ├── generate_embeddings.sh   # Shell script to generate embeddings
│   └── load_to_opensearch.sh    # Shell script to load to OpenSearch
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## 🚀 Quick Start

### 1. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

**Note:** OpenSearch domain creation takes 10-15 minutes.

### 2. Upload Books from Project Gutenberg

```bash
cd scripts
./upload_books.sh
```

### 3. Generate Embeddings

```bash
cd scripts
./generate_embeddings.sh
```

### 4. Load Embeddings into OpenSearch

```bash
cd scripts
./load_to_opensearch.sh
```

### 5. Access OpenSearch Dashboard

```bash
cd terraform
terraform output opensearch_dashboard_url
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

Key variables in `terraform/terraform.tfvars`:

- `bucket_name`: S3 bucket name
- `opensearch_domain_name`: OpenSearch domain name
- `opensearch_instance_type`: OpenSearch instance type (default: `t3.small.search`)

## 🏗️ Infrastructure Components

### AWS Resources Created

1. **S3 Bucket** - Stores books and embeddings
2. **OpenSearch Domain** - Vector search database
3. **VPC & Networking** - Isolated network for OpenSearch
4. **IAM Policies** - Permissions for Bedrock and S3

### OpenSearch Index Structure

- `book_title`: Text field for filtering
- `author`: Text field for filtering
- `chunk_index`: Integer for ordering
- `text`: Original text content
- `text_vector`: 1536-dimensional embedding vector
- `model_id`: Embedding model used
- `uploaded_at`: Timestamp

## 🔍 Vector Search Features

- **Semantic Search**: Find similar text using vector similarity
- **HNSW Algorithm**: Fast approximate nearest neighbor search
- **Cosine Similarity**: Semantic matching metric
- **Hybrid Search**: Combine vector and text search

## 💰 Cost Estimation

- **OpenSearch**: ~$30/month (t3.small.search)
- **S3 Storage**: ~$0.023/GB/month
- **Bedrock Embeddings**: ~$0.0001 per 1K tokens
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
- Use IAM roles instead of profiles in production
- Enable VPC endpoints for better security

## 📝 License

This project is for educational and development purposes. 