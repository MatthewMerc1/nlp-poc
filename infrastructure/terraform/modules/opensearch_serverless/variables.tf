variable "collection_name" {
  description = "Name of the OpenSearch Serverless collection."
  type        = string
}

variable "description" {
  description = "Description for the collection."
  type        = string
  default     = "OpenSearch Serverless collection for NLP POC."
}

variable "data_access_policy_json" {
  description = "Data access policy configuration."
  type = list(object({
    Principal = list(string)
    Rules = list(object({
      Resource     = list(string)
      Permission   = list(string)
      ResourceType = string
    }))
  }))
} 