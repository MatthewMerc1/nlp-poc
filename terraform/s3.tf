# S3 Bucket for storing books and embeddings
resource "aws_s3_bucket" "audiobook_data" {
  bucket = var.bucket_name

  force_destroy = var.bucket_force_destroy

  tags = merge(var.shared_tags, var.s3_bucket_tags)
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "audiobook_data" {
  bucket = aws_s3_bucket.audiobook_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "audiobook_data" {
  bucket = aws_s3_bucket.audiobook_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 bucket policy to restrict access
resource "aws_s3_bucket_policy" "audiobook_data" {
  bucket = aws_s3_bucket.audiobook_data.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyUnencryptedObjectUploads"
        Effect = "Deny"
        Principal = {
          AWS = "*"
        }
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.audiobook_data.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      },
      {
        Sid    = "DenyIncorrectEncryptionHeader"
        Effect = "Deny"
        Principal = {
          AWS = "*"
        }
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.audiobook_data.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.audiobook_data]
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

# S3 Lifecycle Policy
resource "aws_s3_bucket_lifecycle_configuration" "audiobook_data" {
  bucket = aws_s3_bucket.audiobook_data.id

  rule {
    id     = "embeddings_lifecycle"
    status = "Enabled"

    filter {
      prefix = "embeddings/"
    }

    # Transition to IA after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Transition to Glacier after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Delete after 1 year
    expiration {
      days = 365
    }
  }

  rule {
    id     = "books_lifecycle"
    status = "Enabled"

    filter {
      prefix = "books/"
    }

    # Transition to IA after 30 days (minimum required)
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Delete after 6 months
    expiration {
      days = 180
    }
  }

  rule {
    id     = "incomplete_multipart"
    status = "Enabled"

    filter {
      prefix = ""
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
} 
