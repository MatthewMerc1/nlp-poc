# IAM Policy for Bedrock and S3 access
resource "aws_iam_policy" "bedrock_embedding_policy" {
  name        = "bedrock-embedding-policy"
  description = "Policy for Bedrock embedding generation and S3 access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:ListFoundationModels"
        ]
        Resource = [
          "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.audiobook_data.arn,
          "${aws_s3_bucket.audiobook_data.arn}/*"
        ]
      }
    ]
  })

  tags = merge(var.shared_tags, var.iam_policy_tags)
}

# Output the policy ARN for reference
output "bedrock_policy_arn" {
  description = "ARN of the Bedrock embedding policy"
  value       = aws_iam_policy.bedrock_embedding_policy.arn
} 
