resource "aws_opensearchserverless_collection" "this" {
  name        = var.collection_name
  description = var.description
  type        = "SEARCH"
  
  depends_on = [
    aws_opensearchserverless_security_policy.encryption
  ]
}

resource "aws_opensearchserverless_security_policy" "encryption" {
  name        = "enc-${var.collection_name}"
  type        = "encryption"
  description = "Encryption policy for ${var.collection_name} collection"
  policy      = jsonencode({
    Rules = [
      {
        Resource = [
          "collection/${var.collection_name}"
        ]
        ResourceType = "collection"
      }
    ]
    AWSOwnedKey = true
  })
}

resource "aws_opensearchserverless_access_policy" "data_access" {
  name   = "data-${var.collection_name}"
  type   = "data"
  policy = jsonencode(var.data_access_policy_json)
  
  depends_on = [
    aws_opensearchserverless_collection.this
  ]
} 