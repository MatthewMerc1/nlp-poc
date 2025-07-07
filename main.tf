terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

resource "aws_s3_bucket" "audiobook_data" {
  bucket = var.bucket_name

  force_destroy = var.bucket_force_destroy

  tags = var.bucket_tags
}

resource "aws_s3_bucket_versioning" "versioning" {
  count  = var.enable_versioning ? 1 : 0
  bucket = aws_s3_bucket.audiobook_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket organization - create folders for books and embeddings
resource "aws_s3_object" "books_folder" {
  bucket = aws_s3_bucket.audiobook_data.id
  key    = "books/"
  source = "/dev/null"
}

resource "aws_s3_object" "embeddings_folder" {
  bucket = aws_s3_bucket.audiobook_data.id
  key    = "embeddings/"
  source = "/dev/null"
}