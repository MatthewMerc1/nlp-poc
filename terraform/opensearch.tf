# OpenSearch Domain for vector embeddings
resource "aws_opensearch_domain" "embeddings_domain" {
  domain_name    = var.opensearch_domain_name
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type          = var.opensearch_instance_type
    instance_count         = var.opensearch_instance_count
    zone_awareness_enabled = false
  }

  ebs_options {
    ebs_enabled = true
    volume_size = var.opensearch_volume_size
    volume_type = "gp3"
  }

  # Network configuration
  vpc_options {
    subnet_ids         = [aws_subnet.opensearch_subnet.id]
    security_group_ids = [aws_security_group.opensearch_sg.id]
  }

  # Access policy - no IP restrictions when using VPC endpoint
  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "*"
        }
        Action = [
          "es:*"
        ]
        Resource = "arn:aws:es:${var.aws_region}:*:domain/${var.opensearch_domain_name}/*"
      }
    ]
  })

  # Encryption at rest
  encrypt_at_rest {
    enabled = true
  }

  # Node-to-node encryption
  node_to_node_encryption {
    enabled = true
  }

  # Domain endpoint options
  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  tags = var.bucket_tags
}

# VPC for OpenSearch
resource "aws_vpc" "opensearch_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.bucket_tags, {
    Name = "opensearch-vpc"
  })
}

# Subnet for OpenSearch
resource "aws_subnet" "opensearch_subnet" {
  vpc_id            = aws_vpc.opensearch_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = merge(var.bucket_tags, {
    Name = "opensearch-subnet"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "opensearch_igw" {
  vpc_id = aws_vpc.opensearch_vpc.id

  tags = merge(var.bucket_tags, {
    Name = "opensearch-igw"
  })
}

# Route Table
resource "aws_route_table" "opensearch_rt" {
  vpc_id = aws_vpc.opensearch_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.opensearch_igw.id
  }

  tags = merge(var.bucket_tags, {
    Name = "opensearch-rt"
  })
}

# Route Table Association
resource "aws_route_table_association" "opensearch_rta" {
  subnet_id      = aws_subnet.opensearch_subnet.id
  route_table_id = aws_route_table.opensearch_rt.id
}

# Security Group for OpenSearch
resource "aws_security_group" "opensearch_sg" {
  name        = "opensearch-sg"
  description = "Security group for OpenSearch domain"
  vpc_id      = aws_vpc.opensearch_vpc.id

  # HTTPS access
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP access (for development)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.bucket_tags, {
    Name = "opensearch-sg"
  })
} 
