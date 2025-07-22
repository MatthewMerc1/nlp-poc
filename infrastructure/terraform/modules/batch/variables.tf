variable "compute_environment_name" {
  description = "Name for the AWS Batch compute environment."
  type        = string
}

variable "max_vcpus" {
  description = "Maximum number of vCPUs for the compute environment."
  type        = number
  default     = 32
}

variable "min_vcpus" {
  description = "Minimum number of vCPUs for the compute environment."
  type        = number
  default     = 0
}

variable "desired_vcpus" {
  description = "Desired number of vCPUs for the compute environment."
  type        = number
  default     = 0
}

variable "instance_types" {
  description = "List of EC2 instance types for the compute environment."
  type        = list(string)
  default     = ["m5.large"]
}

variable "subnet_ids" {
  description = "List of subnet IDs for the compute environment."
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs for the compute environment."
  type        = list(string)
}

variable "job_queue_name" {
  description = "Name for the AWS Batch job queue."
  type        = string
}

variable "job_definition_name" {
  description = "Name for the AWS Batch job definition."
  type        = string
}

variable "job_image" {
  description = "Docker image for the AWS Batch job."
  type        = string
}

variable "job_vcpus" {
  description = "Number of vCPUs for the job."
  type        = number
  default     = 2
}

variable "job_memory" {
  description = "Memory (in MiB) for the job."
  type        = number
  default     = 4096
}

variable "job_command" {
  description = "Command to run in the job container."
  type        = list(string)
  default     = []
}

variable "job_environment" {
  description = "Environment variables for the job container."
  type        = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "aws_region" {
  description = "AWS region for log configuration."
  type        = string
} 