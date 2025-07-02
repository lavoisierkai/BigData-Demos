# Data Lake Example Outputs
# This file defines outputs for the data lake implementation

# Main S3 Bucket Information
output "data_lake_bucket_name" {
  description = "The name of the data lake S3 bucket"
  value       = module.data_lake_s3.bucket_id
}

output "data_lake_bucket_arn" {
  description = "The ARN of the data lake S3 bucket"
  value       = module.data_lake_s3.bucket_arn
}

output "data_lake_bucket_region" {
  description = "The AWS region where the data lake bucket was created"
  value       = module.data_lake_s3.bucket_region
}

# Data Lake Structure
output "data_lake_paths" {
  description = "Standard data lake paths for different data tiers"
  value       = module.data_lake_s3.data_lake_paths
}

output "data_lake_s3_uri" {
  description = "S3 URI for the data lake bucket"
  value       = module.data_lake_s3.integration_endpoints.s3_uri
}

output "data_processing_uri" {
  description = "S3A URI for data processing services (EMR, Spark, Glue)"
  value       = module.data_lake_s3.integration_endpoints.data_processing_uri
}

# Security Information
output "bucket_encryption_type" {
  description = "Type of encryption used for the bucket"
  value       = var.enable_kms_encryption ? "KMS" : "S3-Managed"
}

output "kms_key_arn" {
  description = "ARN of the KMS key used for encryption (if KMS is enabled)"
  value       = var.enable_kms_encryption ? aws_kms_key.s3_encryption[0].arn : null
}

output "kms_key_alias" {
  description = "Alias of the KMS key used for encryption (if KMS is enabled)"
  value       = var.enable_kms_encryption ? aws_kms_alias.s3_encryption[0].name : null
}

# Access and Integration
output "console_url" {
  description = "AWS Console URL for the S3 bucket"
  value       = "https://s3.console.aws.amazon.com/s3/buckets/${module.data_lake_s3.bucket_id}"
}

output "cloudfront_origin_domain" {
  description = "CloudFront origin domain name for the bucket"
  value       = module.data_lake_s3.integration_endpoints.cloudfront_origin_domain
}

# Lambda Function Information (if created)
output "lambda_function_name" {
  description = "Name of the Lambda function for data processing"
  value       = var.create_lambda_processor ? aws_lambda_function.data_processor[0].function_name : null
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function for data processing"
  value       = var.create_lambda_processor ? aws_lambda_function.data_processor[0].arn : null
}

output "lambda_role_arn" {
  description = "ARN of the IAM role for the Lambda function"
  value       = var.create_lambda_processor ? aws_iam_role.lambda_role[0].arn : null
}

# Logging Information
output "logging_bucket_name" {
  description = "Name of the logging bucket (if created)"
  value       = var.create_logging_bucket ? module.logging_s3[0].bucket_id : var.logging_bucket
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for Lambda function"
  value       = var.create_lambda_processor ? aws_cloudwatch_log_group.lambda_logs[0].name : null
}

# Monitoring Information
output "cloudwatch_alarm_name" {
  description = "Name of the CloudWatch alarm for bucket size monitoring"
  value       = var.enable_monitoring ? aws_cloudwatch_metric_alarm.bucket_size_alarm[0].alarm_name : null
}

output "bucket_size_threshold" {
  description = "Bucket size threshold for monitoring (in bytes)"
  value       = var.bucket_size_alarm_threshold
}

# Cost Allocation
output "cost_allocation_tags" {
  description = "Tags for cost allocation and management"
  value       = merge(var.tags, {
    BucketName  = module.data_lake_s3.bucket_id
    Environment = var.environment
    CreatedBy   = "terraform"
    Module      = "data-lake-example"
  })
}

# Environment Information
output "environment_info" {
  description = "Environment configuration summary"
  value = {
    environment         = var.environment
    aws_region         = var.aws_region
    bucket_name        = module.data_lake_s3.bucket_id
    versioning_enabled = var.versioning_enabled
    kms_encryption     = var.enable_kms_encryption
    monitoring_enabled = var.enable_monitoring
    lambda_enabled     = var.create_lambda_processor
    logging_enabled    = var.create_logging_bucket || var.logging_bucket != ""
  }
}

# Data Lake Folder Structure
output "bronze_layer_paths" {
  description = "Bronze layer S3 paths for raw data ingestion"
  value = [
    for folder in var.data_lake_folders : 
    "s3://${module.data_lake_s3.bucket_id}/${folder}/"
    if startswith(folder, "bronze/")
  ]
}

output "silver_layer_paths" {
  description = "Silver layer S3 paths for cleaned and validated data"
  value = [
    for folder in var.data_lake_folders : 
    "s3://${module.data_lake_s3.bucket_id}/${folder}/"
    if startswith(folder, "silver/")
  ]
}

output "gold_layer_paths" {
  description = "Gold layer S3 paths for analytics and aggregated data"
  value = [
    for folder in var.data_lake_folders : 
    "s3://${module.data_lake_s3.bucket_id}/${folder}/"
    if startswith(folder, "gold/")
  ]
}

# Quick Start Commands
output "quick_start_commands" {
  description = "Quick start commands for data lake operations"
  value = {
    # AWS CLI commands
    list_buckets = "aws s3 ls s3://${module.data_lake_s3.bucket_id}/"
    sync_data    = "aws s3 sync ./local-data/ s3://${module.data_lake_s3.bucket_id}/bronze/raw-data/"
    
    # Spark/EMR commands
    spark_read_bronze = "spark.read.parquet('s3a://${module.data_lake_s3.bucket_id}/bronze/raw-data/')"
    spark_write_silver = "df.write.mode('overwrite').parquet('s3a://${module.data_lake_s3.bucket_id}/silver/cleaned-data/')"
    
    # Glue commands
    glue_table_location = "s3://${module.data_lake_s3.bucket_id}/gold/analytics/"
  }
}