# S3 Module Variables
# Comprehensive variable definitions for S3 bucket configuration

# Basic Configuration
variable "bucket_name" {
  description = "Base name for the S3 bucket"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]{3,63}$", var.bucket_name))
    error_message = "Bucket name must be 3-63 characters long and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "bucket_name_override" {
  description = "Override the bucket name completely (ignores bucket_name and random suffix)"
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod", "test"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod, test."
  }
}

variable "enable_random_suffix" {
  description = "Whether to add a random suffix to ensure bucket name uniqueness"
  type        = bool
  default     = true
}

variable "force_destroy" {
  description = "Allow bucket to be destroyed even if it contains objects"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Security Configuration
variable "versioning_enabled" {
  description = "Enable S3 bucket versioning"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "KMS key ID for server-side encryption (leave empty for S3 managed encryption)"
  type        = string
  default     = ""
}

variable "block_public_access" {
  description = "Enable S3 bucket public access block"
  type        = bool
  default     = true
}

variable "bucket_policy" {
  description = "JSON policy document for the S3 bucket"
  type        = string
  default     = ""
}

# Logging Configuration
variable "logging_bucket" {
  description = "S3 bucket name for access logging (leave empty to disable)"
  type        = string
  default     = ""
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
  default = []
}

# Event Notifications
variable "notifications" {
  description = "S3 bucket event notifications configuration"
  type = map(object({
    type            = string # "lambda", "sqs", or "sns"
    destination_arn = string
    events          = list(string)
    filter_prefix   = optional(string)
    filter_suffix   = optional(string)
  }))
  default = {}
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

# Website Configuration
variable "website_configuration" {
  description = "S3 bucket website configuration"
  type = object({
    index_document = string
    error_document = optional(string)
    routing_rules = optional(list(object({
      condition = object({
        key_prefix_equals               = optional(string)
        http_error_code_returned_equals = optional(string)
      })
      redirect = object({
        hostname                = optional(string)
        http_redirect_code      = optional(string)
        protocol                = optional(string)
        replace_key_prefix_with = optional(string)
        replace_key_with        = optional(string)
      })
    })))
  })
  default = null
}

# Replication Configuration
variable "replication_configuration" {
  description = "S3 bucket replication configuration"
  type = object({
    role_arn = string
    rules = list(object({
      id     = string
      status = string
      filter = optional(object({
        prefix = optional(string)
        tags   = optional(map(string))
      }))
      destination = object({
        bucket        = string
        storage_class = optional(string)
        kms_key_id    = optional(string)
      })
      delete_marker_replication_status = optional(string)
    }))
  })
  default = null
}

# Data Lake Configuration
variable "create_data_lake_structure" {
  description = "Create standard data lake folder structure"
  type        = bool
  default     = false
}

variable "data_lake_folders" {
  description = "List of folder names to create for data lake structure"
  type        = list(string)
  default = [
    "bronze/raw-data",
    "bronze/staging",
    "silver/cleaned-data",
    "silver/validated-data", 
    "gold/analytics",
    "gold/aggregated",
    "archive/backup",
    "logs/application",
    "logs/audit",
    "temp/processing"
  ]
}

# Performance and Cost Optimization
variable "intelligent_tiering_configuration" {
  description = "S3 Intelligent Tiering configuration"
  type = object({
    name   = string
    status = string
    filter = optional(object({
      prefix = optional(string)
      tags   = optional(map(string))
    }))
    tiering = object({
      access_tier = string
      days        = number
    })
  })
  default = null
}

variable "inventory_configuration" {
  description = "S3 inventory configuration"
  type = object({
    name                     = string
    included_object_versions = string
    schedule_frequency       = string
    destination_bucket       = string
    destination_prefix       = optional(string)
    destination_format       = optional(string)
    fields                   = optional(list(string))
  })
  default = null
}

# Multi-part Upload Configuration
variable "multipart_upload_retention_days" {
  description = "Number of days to retain incomplete multipart uploads"
  type        = number
  default     = 7
  validation {
    condition     = var.multipart_upload_retention_days >= 1 && var.multipart_upload_retention_days <= 365
    error_message = "Multipart upload retention days must be between 1 and 365."
  }
}

# Access Point Configuration
variable "access_points" {
  description = "S3 access points configuration"
  type = map(object({
    name   = string
    policy = optional(string)
    vpc_configuration = optional(object({
      vpc_id = string
    }))
  }))
  default = {}
}

# Object Lock Configuration
variable "object_lock_configuration" {
  description = "S3 object lock configuration"
  type = object({
    object_lock_enabled = string
    rule = optional(object({
      default_retention = object({
        mode  = string
        days  = optional(number)
        years = optional(number)
      })
    }))
  })
  default = null
}

# Metrics Configuration
variable "metrics_configurations" {
  description = "S3 bucket metrics configurations"
  type = map(object({
    name   = string
    filter = optional(object({
      prefix = optional(string)
      tags   = optional(map(string))
    }))
  }))
  default = {}
}

# Request Payment Configuration
variable "request_payer" {
  description = "Who pays for S3 requests (BucketOwner or Requester)"
  type        = string
  default     = "BucketOwner"
  validation {
    condition     = contains(["BucketOwner", "Requester"], var.request_payer)
    error_message = "Request payer must be either 'BucketOwner' or 'Requester'."
  }
}