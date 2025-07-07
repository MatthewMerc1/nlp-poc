# S3 Bucket for storing books and embeddings
resource "aws_s3_bucket" "audiobook_data" {
  bucket = var.bucket_name

  force_destroy = var.bucket_force_destroy

  tags = merge(var.shared_tags, var.s3_bucket_tags)
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
