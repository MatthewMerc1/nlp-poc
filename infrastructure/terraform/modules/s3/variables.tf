# S3 Module Variables

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "force_destroy" {
  description = "Whether to force destroy the bucket even if it contains objects"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to the S3 bucket"
  type        = map(string)
  default     = {}
}

variable "encryption_algorithm" {
  description = "Server-side encryption algorithm"
  type        = string
  default     = "AES256"
}

variable "enable_bucket_policy" {
  description = "Whether to enable bucket policy"
  type        = bool
  default     = true
}

variable "enable_versioning" {
  description = "Whether to enable versioning"
  type        = bool
  default     = false
}

variable "folders" {
  description = "List of folders to create in the bucket"
  type        = list(string)
  default     = []
}

variable "lifecycle_rules" {
  description = "List of lifecycle rules for the bucket"
  type = list(object({
    id              = string
    status          = string
    prefix          = string
    transitions     = list(object({
      days          = number
      storage_class = string
    }))
    expiration_days = optional(number)
  }))
  default = []
} 