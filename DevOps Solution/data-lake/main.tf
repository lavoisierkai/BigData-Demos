# AWS Data Lake Infrastructure - Terraform Configuration
# =====================================================
# 
# This Terraform configuration creates a comprehensive data lake
# infrastructure on AWS with best practices for security, scaling,
# and cost optimization.
#
# Architecture:
# - S3 Data Lake with Bronze/Silver/Gold layers
# - AWS Glue for ETL processing and data catalog
# - EMR for big data processing
# - Athena for serverless queries
# - Lambda for data pipeline orchestration
# - CloudWatch for monitoring and alerting

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

# Provider configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}

# Random suffix for unique resource names
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Local values for resource naming
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  # S3 bucket names (must be globally unique)
  raw_bucket_name        = "${local.name_prefix}-raw-${random_string.suffix.result}"
  processed_bucket_name  = "${local.name_prefix}-processed-${random_string.suffix.result}"
  curated_bucket_name    = "${local.name_prefix}-curated-${random_string.suffix.result}"
  scripts_bucket_name    = "${local.name_prefix}-scripts-${random_string.suffix.result}"
  logs_bucket_name       = "${local.name_prefix}-logs-${random_string.suffix.result}"
  
  # Common tags
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.owner
    CostCenter  = var.cost_center
  }
}

# ================================
# Data Lake Storage (S3 Buckets)
# ================================

# Raw data bucket (Bronze layer)
resource "aws_s3_bucket" "raw_data" {
  bucket = local.raw_bucket_name

  tags = merge(local.common_tags, {
    Name        = "${local.name_prefix}-raw-data"
    DataLayer   = "Bronze"
    Purpose     = "Raw data ingestion"
  })
}

resource "aws_s3_bucket_versioning" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.data_lake.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    id     = "raw_data_lifecycle"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }
}

# Processed data bucket (Silver layer)
resource "aws_s3_bucket" "processed_data" {
  bucket = local.processed_bucket_name

  tags = merge(local.common_tags, {
    Name        = "${local.name_prefix}-processed-data"
    DataLayer   = "Silver"
    Purpose     = "Cleaned and validated data"
  })
}

resource "aws_s3_bucket_versioning" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.data_lake.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# Curated data bucket (Gold layer)
resource "aws_s3_bucket" "curated_data" {
  bucket = local.curated_bucket_name

  tags = merge(local.common_tags, {
    Name        = "${local.name_prefix}-curated-data"
    DataLayer   = "Gold"
    Purpose     = "Business-ready analytics datasets"
  })
}

resource "aws_s3_bucket_versioning" "curated_data" {
  bucket = aws_s3_bucket.curated_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "curated_data" {
  bucket = aws_s3_bucket.curated_data.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.data_lake.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# Scripts and artifacts bucket
resource "aws_s3_bucket" "scripts" {
  bucket = local.scripts_bucket_name

  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-scripts"
    Purpose = "ETL scripts and artifacts"
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "scripts" {
  bucket = aws_s3_bucket.scripts.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.data_lake.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# Logs bucket
resource "aws_s3_bucket" "logs" {
  bucket = local.logs_bucket_name

  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-logs"
    Purpose = "Application and access logs"
  })
}

# ================================
# Security & Encryption
# ================================

# KMS key for data lake encryption
resource "aws_kms_key" "data_lake" {
  description             = "KMS key for ${local.name_prefix} data lake encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow AWS Glue"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow EMR"
        Effect = "Allow"
        Principal = {
          Service = "elasticmapreduce.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-data-lake-key"
  })
}

resource "aws_kms_alias" "data_lake" {
  name          = "alias/${local.name_prefix}-data-lake"
  target_key_id = aws_kms_key.data_lake.key_id
}

# ================================
# IAM Roles and Policies
# ================================

# Glue service role
resource "aws_iam_role" "glue_role" {
  name = "${local.name_prefix}-glue-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "glue_service_role" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3_access" {
  name = "${local.name_prefix}-glue-s3-access"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*",
          aws_s3_bucket.processed_data.arn,
          "${aws_s3_bucket.processed_data.arn}/*",
          aws_s3_bucket.curated_data.arn,
          "${aws_s3_bucket.curated_data.arn}/*",
          aws_s3_bucket.scripts.arn,
          "${aws_s3_bucket.scripts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = [aws_kms_key.data_lake.arn]
      }
    ]
  })
}

# EMR service role
resource "aws_iam_role" "emr_service_role" {
  name = "${local.name_prefix}-emr-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "elasticmapreduce.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "emr_service_role" {
  role       = aws_iam_role.emr_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole"
}

# EMR EC2 instance profile
resource "aws_iam_role" "emr_ec2_role" {
  name = "${local.name_prefix}-emr-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "emr_ec2_role" {
  role       = aws_iam_role.emr_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role"
}

resource "aws_iam_instance_profile" "emr_ec2_profile" {
  name = "${local.name_prefix}-emr-ec2-profile"
  role = aws_iam_role.emr_ec2_role.name

  tags = local.common_tags
}

# ================================
# AWS Glue Data Catalog
# ================================

resource "aws_glue_catalog_database" "data_lake" {
  name        = "${replace(local.name_prefix, "-", "_")}_catalog"
  description = "Data catalog for ${local.name_prefix} data lake"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-data-catalog"
  })
}

# ================================
# Networking (VPC for EMR)
# ================================

# Get available AZs
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC for EMR clusters
resource "aws_vpc" "data_lake" {
  count = var.create_vpc ? 1 : 0
  
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

# Private subnet for EMR
resource "aws_subnet" "private" {
  count = var.create_vpc ? 2 : 0
  
  vpc_id            = aws_vpc.data_lake[0].id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-subnet-${count.index + 1}"
    Type = "Private"
  })
}

# Public subnet for NAT Gateway
resource "aws_subnet" "public" {
  count = var.create_vpc ? 1 : 0
  
  vpc_id                  = aws_vpc.data_lake[0].id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, 10)
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-subnet"
    Type = "Public"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  count = var.create_vpc ? 1 : 0
  
  vpc_id = aws_vpc.data_lake[0].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-igw"
  })
}

# NAT Gateway
resource "aws_eip" "nat" {
  count = var.create_vpc ? 1 : 0
  
  domain = "vpc"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-eip"
  })
}

resource "aws_nat_gateway" "main" {
  count = var.create_vpc ? 1 : 0
  
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-gateway"
  })

  depends_on = [aws_internet_gateway.main]
}

# Route tables
resource "aws_route_table" "public" {
  count = var.create_vpc ? 1 : 0
  
  vpc_id = aws_vpc.data_lake[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-rt"
  })
}

resource "aws_route_table" "private" {
  count = var.create_vpc ? 1 : 0
  
  vpc_id = aws_vpc.data_lake[0].id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[0].id
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-rt"
  })
}

resource "aws_route_table_association" "public" {
  count = var.create_vpc ? 1 : 0
  
  subnet_id      = aws_subnet.public[0].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table_association" "private" {
  count = var.create_vpc ? 2 : 0
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[0].id
}

# Security group for EMR
resource "aws_security_group" "emr_master" {
  count = var.create_vpc ? 1 : 0
  
  name_prefix = "${local.name_prefix}-emr-master"
  vpc_id      = aws_vpc.data_lake[0].id

  # Required EMR rules
  ingress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    self      = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-emr-master-sg"
  })
}

resource "aws_security_group" "emr_worker" {
  count = var.create_vpc ? 1 : 0
  
  name_prefix = "${local.name_prefix}-emr-worker"
  vpc_id      = aws_vpc.data_lake[0].id

  # Required EMR rules
  ingress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    self      = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-emr-worker-sg"
  })
}

# ================================
# Data Sources
# ================================

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}