# Outputs for AWS Data Lake Infrastructure
# ======================================

# S3 Bucket Information
output "raw_data_bucket_name" {
  description = "Name of the raw data S3 bucket (Bronze layer)"
  value       = aws_s3_bucket.raw_data.bucket
}

output "raw_data_bucket_arn" {
  description = "ARN of the raw data S3 bucket"
  value       = aws_s3_bucket.raw_data.arn
}

output "processed_data_bucket_name" {
  description = "Name of the processed data S3 bucket (Silver layer)"
  value       = aws_s3_bucket.processed_data.bucket
}

output "processed_data_bucket_arn" {
  description = "ARN of the processed data S3 bucket"
  value       = aws_s3_bucket.processed_data.arn
}

output "curated_data_bucket_name" {
  description = "Name of the curated data S3 bucket (Gold layer)"
  value       = aws_s3_bucket.curated_data.bucket
}

output "curated_data_bucket_arn" {
  description = "ARN of the curated data S3 bucket"
  value       = aws_s3_bucket.curated_data.arn
}

output "scripts_bucket_name" {
  description = "Name of the scripts S3 bucket"
  value       = aws_s3_bucket.scripts.bucket
}

output "scripts_bucket_arn" {
  description = "ARN of the scripts S3 bucket"
  value       = aws_s3_bucket.scripts.arn
}

output "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  value       = aws_s3_bucket.logs.bucket
}

# KMS Key Information
output "data_lake_kms_key_id" {
  description = "ID of the KMS key used for data lake encryption"
  value       = aws_kms_key.data_lake.key_id
}

output "data_lake_kms_key_arn" {
  description = "ARN of the KMS key used for data lake encryption"
  value       = aws_kms_key.data_lake.arn
}

output "data_lake_kms_alias" {
  description = "Alias of the KMS key used for data lake encryption"
  value       = aws_kms_alias.data_lake.name
}

# IAM Role Information
output "glue_role_arn" {
  description = "ARN of the Glue service role"
  value       = aws_iam_role.glue_role.arn
}

output "glue_role_name" {
  description = "Name of the Glue service role"
  value       = aws_iam_role.glue_role.name
}

output "emr_service_role_arn" {
  description = "ARN of the EMR service role"
  value       = aws_iam_role.emr_service_role.arn
}

output "emr_instance_profile_arn" {
  description = "ARN of the EMR EC2 instance profile"
  value       = aws_iam_instance_profile.emr_ec2_profile.arn
}

output "emr_instance_profile_name" {
  description = "Name of the EMR EC2 instance profile"
  value       = aws_iam_instance_profile.emr_ec2_profile.name
}

# Glue Catalog Information
output "glue_catalog_database_name" {
  description = "Name of the Glue catalog database"
  value       = aws_glue_catalog_database.data_lake.name
}

output "glue_catalog_database_arn" {
  description = "ARN of the Glue catalog database"
  value       = "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:database/${aws_glue_catalog_database.data_lake.name}"
}

# VPC Information (if created)
output "vpc_id" {
  description = "ID of the VPC created for EMR clusters"
  value       = var.create_vpc ? aws_vpc.data_lake[0].id : null
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = var.create_vpc ? aws_vpc.data_lake[0].cidr_block : null
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = var.create_vpc ? aws_subnet.private[*].id : []
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = var.create_vpc ? aws_subnet.public[*].id : []
}

output "nat_gateway_id" {
  description = "ID of the NAT Gateway"
  value       = var.create_vpc ? aws_nat_gateway.main[0].id : null
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = var.create_vpc ? aws_internet_gateway.main[0].id : null
}

# Security Group Information
output "emr_master_security_group_id" {
  description = "ID of the EMR master security group"
  value       = var.create_vpc ? aws_security_group.emr_master[0].id : null
}

output "emr_worker_security_group_id" {
  description = "ID of the EMR worker security group"
  value       = var.create_vpc ? aws_security_group.emr_worker[0].id : null
}

# Data Lake Configuration
output "data_lake_configuration" {
  description = "Summary of data lake configuration"
  value = {
    project_name         = var.project_name
    environment         = var.environment
    region              = var.aws_region
    enable_encryption   = true
    data_layers = {
      bronze = aws_s3_bucket.raw_data.bucket
      silver = aws_s3_bucket.processed_data.bucket
      gold   = aws_s3_bucket.curated_data.bucket
    }
    glue_database       = aws_glue_catalog_database.data_lake.name
    kms_key_alias       = aws_kms_alias.data_lake.name
  }
}

# Connection Strings and Endpoints
output "athena_workgroup_name" {
  description = "Name of the Athena workgroup (for query execution)"
  value       = "${local.name_prefix}-workgroup"
}

output "data_lake_endpoints" {
  description = "Important endpoints and connection information"
  value = {
    s3_console_urls = {
      raw_data       = "https://console.aws.amazon.com/s3/buckets/${aws_s3_bucket.raw_data.bucket}"
      processed_data = "https://console.aws.amazon.com/s3/buckets/${aws_s3_bucket.processed_data.bucket}"
      curated_data   = "https://console.aws.amazon.com/s3/buckets/${aws_s3_bucket.curated_data.bucket}"
    }
    glue_console_url = "https://console.aws.amazon.com/glue/home?region=${data.aws_region.current.name}#catalog:tab=databases"
    athena_console_url = "https://console.aws.amazon.com/athena/home?region=${data.aws_region.current.name}"
  }
}

# Resource ARNs for Cross-Service Access
output "resource_arns" {
  description = "ARNs of key resources for cross-service access"
  value = {
    buckets = {
      raw_data       = aws_s3_bucket.raw_data.arn
      processed_data = aws_s3_bucket.processed_data.arn
      curated_data   = aws_s3_bucket.curated_data.arn
      scripts        = aws_s3_bucket.scripts.arn
      logs           = aws_s3_bucket.logs.arn
    }
    iam_roles = {
      glue_service = aws_iam_role.glue_role.arn
      emr_service  = aws_iam_role.emr_service_role.arn
      emr_ec2      = aws_iam_role.emr_ec2_role.arn
    }
    kms_key = aws_kms_key.data_lake.arn
  }
}

# Quick Start Information
output "quick_start_guide" {
  description = "Quick start information for using the data lake"
  value = {
    upload_raw_data_command = "aws s3 cp your-file.csv s3://${aws_s3_bucket.raw_data.bucket}/data/"
    athena_query_example    = "SELECT * FROM ${aws_glue_catalog_database.data_lake.name}.your_table_name LIMIT 10;"
    glue_console_url       = "https://console.aws.amazon.com/glue/home?region=${data.aws_region.current.name}"
    next_steps = [
      "1. Upload sample data to the raw data bucket",
      "2. Create Glue crawlers to catalog your data",
      "3. Run Glue ETL jobs to process data",
      "4. Query processed data with Athena",
      "5. Create EMR clusters for big data processing"
    ]
  }
}

# Cost Optimization Information
output "cost_optimization_tips" {
  description = "Tips for optimizing costs"
  value = {
    storage_classes = "Data automatically transitions to cheaper storage classes based on lifecycle policies"
    intelligent_tiering = var.enable_intelligent_tiering ? "Enabled - S3 will automatically optimize storage costs" : "Disabled"
    emr_recommendations = var.enable_emr ? "Consider using Spot instances for cost savings on non-critical workloads" : "EMR is disabled - enable only when needed"
    monitoring = "Use CloudWatch to monitor usage and set up billing alerts"
  }
}

# Security Information
output "security_features" {
  description = "Security features enabled"
  value = {
    encryption_at_rest = "All S3 buckets encrypted with customer-managed KMS key"
    encryption_in_transit = "HTTPS enforced for all S3 access"
    iam_roles = "Least privilege IAM roles created for Glue and EMR"
    vpc_isolation = var.create_vpc ? "EMR clusters deployed in private subnets" : "Using existing VPC"
    access_logging = var.enable_data_lake_logging ? "S3 access logging enabled" : "Access logging disabled"
  }
}