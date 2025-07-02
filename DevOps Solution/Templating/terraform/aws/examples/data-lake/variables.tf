# Variables for Data Lake Example
# This file defines all the input variables for the data lake implementation

# Provider Configuration
variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "us-west-2"
  validation {
    condition = contains([
      "us-east-1", "us-east-2", "us-west-1", "us-west-2",
      "eu-west-1", "eu-west-2", "eu-central-1",
      "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
    ], var.aws_region)
    error_message = "AWS region must be a valid region."
  }
}

# Basic S3 Configuration
variable "bucket_name" {
  description = "Base name for the S3 bucket"
  type        = string
  default     = "bigdata-demo-lake"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod", "test"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod, test."
  }
}

variable "enable_random_suffix" {
  description = "Whether to add a random suffix to bucket names"
  type        = bool
  default     = true
}

variable "force_destroy" {
  description = "Allow bucket to be destroyed even if it contains objects (use with caution)"
  type        = bool
  default     = false
}

# Security Configuration
variable "versioning_enabled" {
  description = "Enable S3 bucket versioning"
  type        = bool
  default     = true
}

variable "enable_kms_encryption" {
  description = "Enable KMS encryption for S3 bucket"
  type        = bool
  default     = false
}

variable "block_public_access" {
  description = "Enable S3 bucket public access block"
  type        = bool
  default     = true
}

variable "logging_bucket" {
  description = "S3 bucket name for access logging (leave empty to use local logging bucket)"
  type        = string
  default     = ""
}

variable "create_logging_bucket" {
  description = "Create a separate bucket for access logs"
  type        = bool
  default     = true
}

# Data Lake Configuration
variable "create_data_lake_structure" {
  description = "Create standard data lake folder structure"
  type        = bool
  default     = true
}

variable "data_lake_folders" {
  description = "List of folder names to create for data lake structure"
  type        = list(string)
  default = [
    "bronze/raw-data/orders",
    "bronze/raw-data/customers", 
    "bronze/raw-data/products",
    "bronze/staging/incremental",
    "silver/cleaned-data/orders",
    "silver/cleaned-data/customers",
    "silver/validated-data/customer-360",
    "gold/analytics/sales-reports",
    "gold/analytics/customer-segments",
    "gold/aggregated/monthly-kpis",
    "gold/aggregated/product-performance",
    "archive/backup/daily",
    "archive/backup/monthly",
    "logs/application/spark",
    "logs/application/glue",
    "logs/audit/access",
    "temp/processing/etl",
    "temp/processing/ml-training"
  ]
}

# Lifecycle Management
variable "lifecycle_rules" {
  description = "List of lifecycle rules for the S3 bucket"
  type = list(object({
    id      = string
    enabled = bool
    filter = optional(object({
      prefix = optional(string)
      tags   = optional(map(string))
    }))
    expiration = optional(object({
      days                         = optional(number)
      expired_object_delete_marker = optional(bool)
    }))
    noncurrent_version_expiration = optional(object({
      days = number
    }))
    transitions = optional(list(object({
      days          = number
      storage_class = string
    })))
    noncurrent_version_transitions = optional(list(object({
      days          = number
      storage_class = string
    })))
  }))
  default = [
    {
      id      = "data_lake_lifecycle"
      enabled = true
      filter = {
        prefix = ""
      }
      transitions = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        },
        {
          days          = 90
          storage_class = "GLACIER"
        },
        {
          days          = 365
          storage_class = "DEEP_ARCHIVE"
        }
      ]
      noncurrent_version_transitions = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        },
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]
      noncurrent_version_expiration = {
        days = 365
      }
    },
    {
      id      = "temp_cleanup"
      enabled = true
      filter = {
        prefix = "temp/"
      }
      expiration = {
        days = 7
      }
    }
  ]
}

# Event Notifications
variable "notifications" {
  description = "S3 bucket event notifications configuration"
  type = map(object({
    type            = string
    destination_arn = string
    events          = list(string)
    filter_prefix   = optional(string)
    filter_suffix   = optional(string)
  }))
  default = {}
}

variable "create_lambda_processor" {
  description = "Create a sample Lambda function for data processing"
  type        = bool
  default     = false
}

# CORS Configuration
variable "cors_rules" {
  description = "CORS rules for the S3 bucket"
  type = list(object({
    allowed_headers = optional(list(string))
    allowed_methods = list(string)
    allowed_origins = list(string)
    expose_headers  = optional(list(string))
    max_age_seconds = optional(number)
  }))
  default = []
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and alarms"
  type        = bool
  default     = true
}

variable "bucket_size_alarm_threshold" {
  description = "Threshold in bytes for bucket size alarm"
  type        = number
  default     = 107374182400  # 100 GB
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications"
  type        = string
  default     = ""
}

# Tagging
variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "BigData-Demo"
    Owner       = "DataEngineering"
    CostCenter  = "Analytics"
    Compliance  = "None"
    Backup      = "Required"
    Purpose     = "DataLake"
  }
}