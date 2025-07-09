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

  # Access policy - allow all access when using VPC endpoint
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

  # Fine-grained access control
  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = true
    
    master_user_options {
      master_user_name = var.opensearch_master_user
      master_user_password = var.opensearch_master_password
    }
  }

  tags = merge(var.shared_tags, var.opensearch_domain_tags)
}

# VPC for OpenSearch
resource "aws_vpc" "opensearch_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.shared_tags, var.vpc_tags)
}

# Public Subnet for NAT Gateway
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.opensearch_vpc.id
  cidr_block              = "10.0.0.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-public-subnet"
    Purpose      = "nat-gateway"
    ResourceType = "subnet"
  })
}

# Private Subnet for OpenSearch and Lambda
resource "aws_subnet" "opensearch_subnet" {
  vpc_id            = aws_vpc.opensearch_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = merge(var.shared_tags, var.subnet_tags)
}

# Internet Gateway
resource "aws_internet_gateway" "opensearch_igw" {
  vpc_id = aws_vpc.opensearch_vpc.id

  tags = merge(var.shared_tags, var.internet_gateway_tags)
}

# Public Route Table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.opensearch_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.opensearch_igw.id
  }

  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-public-rt"
    Purpose      = "nat-gateway"
    ResourceType = "route-table"
  })
}

# Associate Public Subnet with Public Route Table
resource "aws_route_table_association" "public_rta" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# Private Route Table
resource "aws_route_table" "opensearch_rt" {
  vpc_id = aws_vpc.opensearch_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gw.id
  }

  tags = merge(var.shared_tags, var.route_table_tags)
}

# Associate Private Subnet with Private Route Table
resource "aws_route_table_association" "opensearch_rta" {
  subnet_id      = aws_subnet.opensearch_subnet.id
  route_table_id = aws_route_table.opensearch_rt.id
}

# Security Group for OpenSearch
resource "aws_security_group" "opensearch_sg" {
  name        = "opensearch-sg"
  description = "Security group for OpenSearch domain"
  vpc_id      = aws_vpc.opensearch_vpc.id

  # HTTPS access - restrict to VPC and allowed IPs
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = concat(
      [aws_subnet.opensearch_subnet.cidr_block],
      var.allowed_ipv4_addresses
    )
    ipv6_cidr_blocks = var.allowed_ipv6_addresses
  }

  # HTTP access (for development) - restrict to VPC and allowed IPs
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = concat(
      [aws_subnet.opensearch_subnet.cidr_block],
      var.allowed_ipv4_addresses
    )
    ipv6_cidr_blocks = var.allowed_ipv6_addresses
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.shared_tags, var.security_group_tags)
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat_eip" {
  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-nat-eip"
    Purpose      = "nat-gateway"
    ResourceType = "eip"
  })
}

# NAT Gateway in Public Subnet
resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public_subnet.id
  tags = merge(var.shared_tags, {
    Name         = "nlp-poc-nat-gateway"
    Purpose      = "nat-gateway"
    ResourceType = "nat-gateway"
  })
}
