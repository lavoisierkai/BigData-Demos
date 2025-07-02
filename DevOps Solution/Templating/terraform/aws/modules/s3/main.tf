# S3 Bucket Module for Data Lake Implementation
# This module creates S3 buckets with comprehensive configuration for data lake use cases

# Data source for current AWS account and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Generate bucket suffix for uniqueness
resource "random_string" "bucket_suffix" {
  count   = var.enable_random_suffix ? 1 : 0
  length  = 8
  special = false
  upper   = false
}

locals {
  # Generate unique bucket names
  bucket_suffix = var.enable_random_suffix ? "-${random_string.bucket_suffix[0].result}" : ""
  bucket_name   = var.bucket_name_override != "" ? var.bucket_name_override : "${var.bucket_name}${local.bucket_suffix}"
  
  # Common tags
  common_tags = merge(
    var.tags,
    {
      Module      = "s3"
      Environment = var.environment
      CreatedBy   = "Terraform"
      CreatedOn   = formatdate("YYYY-MM-DD", timestamp())
    }
  )
}

# Main S3 bucket
resource "aws_s3_bucket" "main" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy

  tags = merge(
    local.common_tags,
    {
      Name = local.bucket_name
      Type = "Primary"
    }
  )
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Disabled"
  }
}

# S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_id != "" ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_id != "" ? var.kms_key_id : null
    }
    bucket_key_enabled = var.kms_key_id != "" ? true : false
  }
}

# S3 bucket public access block
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = var.block_public_access
  block_public_policy     = var.block_public_access
  ignore_public_acls      = var.block_public_access
  restrict_public_buckets = var.block_public_access
}

# S3 bucket logging (if logging bucket is specified)
resource "aws_s3_bucket_logging" "main" {
  count  = var.logging_bucket != "" ? 1 : 0
  bucket = aws_s3_bucket.main.id

  target_bucket = var.logging_bucket
  target_prefix = "${local.bucket_name}/"
}

# S3 bucket lifecycle configuration
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  count  = length(var.lifecycle_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.main.id

  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      # Filter configuration
      dynamic "filter" {
        for_each = rule.value.filter != null ? [rule.value.filter] : []
        content {
          prefix = filter.value.prefix
          dynamic "tag" {
            for_each = filter.value.tags != null ? filter.value.tags : {}
            content {
              key   = tag.key
              value = tag.value
            }
          }
        }
      }

      # Expiration configuration
      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        content {
          days                         = expiration.value.days
          expired_object_delete_marker = expiration.value.expired_object_delete_marker
        }
      }

      # Noncurrent version expiration
      dynamic "noncurrent_version_expiration" {
        for_each = rule.value.noncurrent_version_expiration != null ? [rule.value.noncurrent_version_expiration] : []
        content {
          noncurrent_days = noncurrent_version_expiration.value.days
        }
      }

      # Transition rules
      dynamic "transition" {
        for_each = rule.value.transitions != null ? rule.value.transitions : []
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      # Noncurrent version transitions
      dynamic "noncurrent_version_transition" {
        for_each = rule.value.noncurrent_version_transitions != null ? rule.value.noncurrent_version_transitions : []
        content {
          noncurrent_days = noncurrent_version_transition.value.days
          storage_class   = noncurrent_version_transition.value.storage_class
        }
      }
    }
  }

  depends_on = [aws_s3_bucket_versioning.main]
}

# S3 bucket notification configuration
resource "aws_s3_bucket_notification" "main" {
  count  = length(var.notifications) > 0 ? 1 : 0
  bucket = aws_s3_bucket.main.id

  # Lambda function notifications
  dynamic "lambda_function" {
    for_each = { for k, v in var.notifications : k => v if v.type == "lambda" }
    content {
      lambda_function_arn = lambda_function.value.destination_arn
      events              = lambda_function.value.events
      filter_prefix       = lambda_function.value.filter_prefix
      filter_suffix       = lambda_function.value.filter_suffix
    }
  }

  # SQS queue notifications
  dynamic "queue" {
    for_each = { for k, v in var.notifications : k => v if v.type == "sqs" }
    content {
      queue_arn     = queue.value.destination_arn
      events        = queue.value.events
      filter_prefix = queue.value.filter_prefix
      filter_suffix = queue.value.filter_suffix
    }
  }

  # SNS topic notifications
  dynamic "topic" {
    for_each = { for k, v in var.notifications : k => v if v.type == "sns" }
    content {
      topic_arn     = topic.value.destination_arn
      events        = topic.value.events
      filter_prefix = topic.value.filter_prefix
      filter_suffix = topic.value.filter_suffix
    }
  }
}

# S3 bucket policy (if provided)
resource "aws_s3_bucket_policy" "main" {
  count  = var.bucket_policy != "" ? 1 : 0
  bucket = aws_s3_bucket.main.id
  policy = var.bucket_policy
}

# CORS configuration
resource "aws_s3_bucket_cors_configuration" "main" {
  count  = length(var.cors_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.main.id

  dynamic "cors_rule" {
    for_each = var.cors_rules
    content {
      allowed_headers = cors_rule.value.allowed_headers
      allowed_methods = cors_rule.value.allowed_methods
      allowed_origins = cors_rule.value.allowed_origins
      expose_headers  = cors_rule.value.expose_headers
      max_age_seconds = cors_rule.value.max_age_seconds
    }
  }
}

# Website configuration (if enabled)
resource "aws_s3_bucket_website_configuration" "main" {
  count  = var.website_configuration != null ? 1 : 0
  bucket = aws_s3_bucket.main.id

  index_document {
    suffix = var.website_configuration.index_document
  }

  dynamic "error_document" {
    for_each = var.website_configuration.error_document != null ? [var.website_configuration.error_document] : []
    content {
      key = error_document.value
    }
  }

  dynamic "routing_rule" {
    for_each = var.website_configuration.routing_rules != null ? var.website_configuration.routing_rules : []
    content {
      condition {
        key_prefix_equals = routing_rule.value.condition.key_prefix_equals
        http_error_code_returned_equals = routing_rule.value.condition.http_error_code_returned_equals
      }
      redirect {
        hostname              = routing_rule.value.redirect.hostname
        http_redirect_code    = routing_rule.value.redirect.http_redirect_code
        protocol              = routing_rule.value.redirect.protocol
        replace_key_prefix_with = routing_rule.value.redirect.replace_key_prefix_with
        replace_key_with      = routing_rule.value.redirect.replace_key_with
      }
    }
  }
}

# Replication configuration (if enabled)
resource "aws_s3_bucket_replication_configuration" "main" {
  count      = var.replication_configuration != null ? 1 : 0
  role       = var.replication_configuration.role_arn
  bucket     = aws_s3_bucket.main.id
  depends_on = [aws_s3_bucket_versioning.main]

  dynamic "rule" {
    for_each = var.replication_configuration.rules
    content {
      id     = rule.value.id
      status = rule.value.status

      dynamic "filter" {
        for_each = rule.value.filter != null ? [rule.value.filter] : []
        content {
          prefix = filter.value.prefix
          dynamic "tag" {
            for_each = filter.value.tags != null ? filter.value.tags : {}
            content {
              key   = tag.key
              value = tag.value
            }
          }
        }
      }

      destination {
        bucket        = rule.value.destination.bucket
        storage_class = rule.value.destination.storage_class

        dynamic "encryption_configuration" {
          for_each = rule.value.destination.kms_key_id != null ? [rule.value.destination.kms_key_id] : []
          content {
            replica_kms_key_id = encryption_configuration.value
          }
        }
      }

      dynamic "delete_marker_replication" {
        for_each = rule.value.delete_marker_replication_status != null ? [rule.value.delete_marker_replication_status] : []
        content {
          status = delete_marker_replication.value
        }
      }
    }
  }
}

# Data lake folder structure (if enabled)
resource "aws_s3_object" "data_lake_folders" {
  for_each = var.create_data_lake_structure ? toset(var.data_lake_folders) : toset([])
  
  bucket       = aws_s3_bucket.main.id
  key          = "${each.value}/"
  content      = ""
  content_type = "application/x-directory"
  
  tags = merge(
    local.common_tags,
    {
      Name = "${each.value}-folder"
      Type = "DataLakeFolder"
    }
  )
}