# S3 Module Outputs
# Comprehensive outputs for S3 bucket resources

# Bucket Information
output "bucket_id" {
  description = "The name/ID of the S3 bucket"
  value       = aws_s3_bucket.main.id
}

output "bucket_arn" {
  description = "The ARN of the S3 bucket"
  value       = aws_s3_bucket.main.arn
}

output "bucket_domain_name" {
  description = "The bucket domain name"
  value       = aws_s3_bucket.main.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "The bucket regional domain name"
  value       = aws_s3_bucket.main.bucket_regional_domain_name
}

output "bucket_hosted_zone_id" {
  description = "The Route 53 Hosted Zone ID for this bucket's region"
  value       = aws_s3_bucket.main.hosted_zone_id
}

output "bucket_region" {
  description = "The AWS region where the bucket was created"
  value       = aws_s3_bucket.main.region
}

# Bucket URLs and Endpoints
output "bucket_website_endpoint" {
  description = "The website endpoint for the bucket (if website hosting is enabled)"
  value       = var.website_configuration != null ? aws_s3_bucket_website_configuration.main[0].website_endpoint : null
}

output "bucket_website_domain" {
  description = "The domain of the website endpoint (if website hosting is enabled)"
  value       = var.website_configuration != null ? aws_s3_bucket_website_configuration.main[0].website_domain : null
}

# Bucket Configuration Details
output "bucket_versioning_status" {
  description = "The versioning status of the bucket"
  value       = aws_s3_bucket_versioning.main.versioning_configuration[0].status
}

output "bucket_encryption_algorithm" {
  description = "The server-side encryption algorithm used"
  value       = aws_s3_bucket_server_side_encryption_configuration.main.rule[0].apply_server_side_encryption_by_default[0].sse_algorithm
}

output "bucket_kms_key_id" {
  description = "The KMS key ID used for encryption (if applicable)"
  value       = aws_s3_bucket_server_side_encryption_configuration.main.rule[0].apply_server_side_encryption_by_default[0].kms_master_key_id
}

# Public Access Block Status
output "bucket_public_access_block" {
  description = "The public access block configuration"
  value = {
    block_public_acls       = aws_s3_bucket_public_access_block.main.block_public_acls
    block_public_policy     = aws_s3_bucket_public_access_block.main.block_public_policy
    ignore_public_acls      = aws_s3_bucket_public_access_block.main.ignore_public_acls
    restrict_public_buckets = aws_s3_bucket_public_access_block.main.restrict_public_buckets
  }
}

# Lifecycle Configuration
output "bucket_lifecycle_rules" {
  description = "The lifecycle rules configured for the bucket"
  value = length(var.lifecycle_rules) > 0 ? {
    rules_count = length(var.lifecycle_rules)
    rules       = var.lifecycle_rules
  } : null
}

# Notification Configuration
output "bucket_notifications" {
  description = "The notification configurations for the bucket"
  value = length(var.notifications) > 0 ? {
    notifications_count = length(var.notifications)
    notifications       = var.notifications
  } : null
}

# CORS Configuration
output "bucket_cors_rules" {
  description = "The CORS rules configured for the bucket"
  value = length(var.cors_rules) > 0 ? {
    cors_rules_count = length(var.cors_rules)
    cors_rules       = var.cors_rules
  } : null
}

# Replication Configuration
output "bucket_replication_configuration" {
  description = "The replication configuration for the bucket"
  value = var.replication_configuration != null ? {
    role_arn    = var.replication_configuration.role_arn
    rules_count = length(var.replication_configuration.rules)
  } : null
}

# Data Lake Structure
output "data_lake_folders" {
  description = "The data lake folder structure created"
  value = var.create_data_lake_structure ? {
    folders_count = length(var.data_lake_folders)
    folders       = var.data_lake_folders
    folder_urls   = [for folder in var.data_lake_folders : "s3://${aws_s3_bucket.main.id}/${folder}/"]
  } : null
}

# Access Information for Applications
output "bucket_access_info" {
  description = "Access information for applications and services"
  value = {
    bucket_name = aws_s3_bucket.main.id
    bucket_arn  = aws_s3_bucket.main.arn
    region      = aws_s3_bucket.main.region
    s3_uri      = "s3://${aws_s3_bucket.main.id}"
    console_url = "https://s3.console.aws.amazon.com/s3/buckets/${aws_s3_bucket.main.id}"
  }
}

# Cost and Performance Information
output "bucket_cost_allocation_tags" {
  description = "Tags that can be used for cost allocation"
  value = {
    environment = var.environment
    module      = "s3"
    bucket_name = aws_s3_bucket.main.id
    created_by  = "terraform"
  }
}

# Security Information
output "bucket_security_info" {
  description = "Security configuration summary"
  value = {
    versioning_enabled     = var.versioning_enabled
    encryption_enabled     = true
    encryption_type        = var.kms_key_id != "" ? "KMS" : "S3-Managed"
    public_access_blocked  = var.block_public_access
    logging_enabled        = var.logging_bucket != ""
    policy_attached        = var.bucket_policy != ""
  }
}

# Integration Endpoints
output "integration_endpoints" {
  description = "Various endpoints for service integrations"
  value = {
    # For AWS CLI and SDKs
    s3_uri = "s3://${aws_s3_bucket.main.id}"
    
    # For REST API calls
    rest_endpoint = "https://s3.${aws_s3_bucket.main.region}.amazonaws.com/${aws_s3_bucket.main.id}"
    
    # For website hosting (if enabled)
    website_endpoint = var.website_configuration != null ? "http://${aws_s3_bucket.main.id}.s3-website-${aws_s3_bucket.main.region}.amazonaws.com" : null
    
    # For CloudFront distribution
    cloudfront_origin_domain = aws_s3_bucket.main.bucket_regional_domain_name
    
    # For data processing services (EMR, Glue, etc.)
    data_processing_uri = "s3a://${aws_s3_bucket.main.id}"
  }
}

# Monitoring and Logging
output "monitoring_info" {
  description = "Information for monitoring and observability setup"
  value = {
    bucket_name         = aws_s3_bucket.main.id
    bucket_arn          = aws_s3_bucket.main.arn
    cloudwatch_log_group = "/aws/s3/${aws_s3_bucket.main.id}"
    metrics_namespace    = "AWS/S3"
    cost_allocation_tags = local.common_tags
  }
}

# Data Lake Specific Outputs
output "data_lake_paths" {
  description = "Standard data lake paths for different data tiers"
  value = var.create_data_lake_structure ? {
    bronze_raw      = "s3://${aws_s3_bucket.main.id}/bronze/raw-data/"
    bronze_staging  = "s3://${aws_s3_bucket.main.id}/bronze/staging/"
    silver_cleaned  = "s3://${aws_s3_bucket.main.id}/silver/cleaned-data/"
    silver_validated = "s3://${aws_s3_bucket.main.id}/silver/validated-data/"
    gold_analytics  = "s3://${aws_s3_bucket.main.id}/gold/analytics/"
    gold_aggregated = "s3://${aws_s3_bucket.main.id}/gold/aggregated/"
    archive_backup  = "s3://${aws_s3_bucket.main.id}/archive/backup/"
    logs_application = "s3://${aws_s3_bucket.main.id}/logs/application/"
    logs_audit      = "s3://${aws_s3_bucket.main.id}/logs/audit/"
    temp_processing = "s3://${aws_s3_bucket.main.id}/temp/processing/"
  } : null
}

# Terraform State Information
output "terraform_metadata" {
  description = "Terraform metadata for state management"
  value = {
    module_version = "1.0.0"
    created_at     = timestamp()
    workspace      = terraform.workspace
    configuration_hash = sha256(jsonencode({
      bucket_name              = var.bucket_name
      environment             = var.environment
      versioning_enabled      = var.versioning_enabled
      block_public_access     = var.block_public_access
      create_data_lake_structure = var.create_data_lake_structure
    }))
  }
}