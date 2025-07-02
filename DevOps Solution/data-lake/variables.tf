# Variables for AWS Data Lake Infrastructure
# ========================================

# Project Information
variable "project_name" {
  description = "Name of the project - used for resource naming"
  type        = string
  default     = "data-lake"
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "data-team"
}

variable "cost_center" {
  description = "Cost center for billing purposes"
  type        = string
  default     = "engineering"
}

# AWS Configuration
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

# Networking
variable "create_vpc" {
  description = "Whether to create a new VPC for EMR clusters"
  type        = bool
  default     = true
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "existing_vpc_id" {
  description = "ID of existing VPC to use (when create_vpc is false)"
  type        = string
  default     = null
}

variable "existing_subnet_ids" {
  description = "List of existing subnet IDs to use for EMR (when create_vpc is false)"
  type        = list(string)
  default     = []
}

# Data Lake Configuration
variable "enable_data_lake_logging" {
  description = "Enable access logging for data lake buckets"
  type        = bool
  default     = true
}

variable "data_retention_days" {
  description = "Number of days to retain data in Standard storage before transitioning"
  type        = number
  default     = 30
  
  validation {
    condition     = var.data_retention_days >= 1 && var.data_retention_days <= 365
    error_message = "Data retention days must be between 1 and 365."
  }
}

# AWS Glue Configuration
variable "enable_glue_catalog" {
  description = "Enable AWS Glue Data Catalog"
  type        = bool
  default     = true
}

variable "glue_crawler_schedule" {
  description = "Cron expression for Glue crawler schedule"
  type        = string
  default     = "cron(0 2 * * ? *)"  # Daily at 2 AM
}

# EMR Configuration
variable "enable_emr" {
  description = "Enable EMR cluster creation"
  type        = bool
  default     = false  # Disabled by default due to cost
}

variable "emr_instance_type" {
  description = "EC2 instance type for EMR nodes"
  type        = string
  default     = "m5.xlarge"
}

variable "emr_instance_count" {
  description = "Number of EMR worker instances"
  type        = number
  default     = 2
  
  validation {
    condition     = var.emr_instance_count >= 1 && var.emr_instance_count <= 20
    error_message = "EMR instance count must be between 1 and 20."
  }
}

variable "emr_ebs_volume_size" {
  description = "Size of EBS volumes for EMR instances (GB)"
  type        = number
  default     = 100
  
  validation {
    condition     = var.emr_ebs_volume_size >= 10 && var.emr_ebs_volume_size <= 1000
    error_message = "EBS volume size must be between 10 and 1000 GB."
  }
}

variable "emr_applications" {
  description = "List of applications to install on EMR cluster"
  type        = list(string)
  default     = ["Hadoop", "Spark", "Livy", "JupyterHub"]
}

# Athena Configuration
variable "enable_athena" {
  description = "Enable Athena query service setup"
  type        = bool
  default     = true
}

variable "athena_result_bucket" {
  description = "S3 bucket for Athena query results (optional, creates one if not specified)"
  type        = string
  default     = null
}

# Lambda Configuration
variable "enable_lambda_triggers" {
  description = "Enable Lambda functions for data pipeline triggers"
  type        = bool
  default     = false
}

# Security Configuration
variable "enable_bucket_notifications" {
  description = "Enable S3 bucket notifications for data pipeline triggers"
  type        = bool
  default     = false
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access EMR clusters"
  type        = list(string)
  default     = []
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

# Monitoring and Alerting
variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms for monitoring"
  type        = bool
  default     = true
}

variable "notification_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = null
}

# Cost Optimization
variable "enable_intelligent_tiering" {
  description = "Enable S3 Intelligent Tiering for cost optimization"
  type        = bool
  default     = true
}

variable "enable_spot_instances" {
  description = "Use Spot instances for EMR worker nodes"
  type        = bool
  default     = false
}

variable "spot_instance_max_price" {
  description = "Maximum price for Spot instances (USD per hour)"
  type        = string
  default     = "0.10"
}

# Data Processing
variable "default_file_format" {
  description = "Default file format for processed data"
  type        = string
  default     = "parquet"
  
  validation {
    condition     = contains(["parquet", "orc", "avro", "json"], var.default_file_format)
    error_message = "File format must be one of: parquet, orc, avro, json."
  }
}

variable "compression_type" {
  description = "Compression type for stored data"
  type        = string
  default     = "snappy"
  
  validation {
    condition     = contains(["snappy", "gzip", "lz4", "zstd"], var.compression_type)
    error_message = "Compression type must be one of: snappy, gzip, lz4, zstd."
  }
}

# Advanced Configuration
variable "enable_cross_region_replication" {
  description = "Enable cross-region replication for disaster recovery"
  type        = bool
  default     = false
}

variable "replication_region" {
  description = "AWS region for cross-region replication"
  type        = string
  default     = "us-east-1"
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "enable_macie" {
  description = "Enable Amazon Macie for data security and privacy"
  type        = bool
  default     = false
}

variable "enable_lake_formation" {
  description = "Enable AWS Lake Formation for data governance"
  type        = bool
  default     = false
}

# Custom Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}