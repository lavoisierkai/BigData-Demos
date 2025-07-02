# Data Lake Example - S3 Module Usage
# This example demonstrates how to use the S3 module for a data lake implementation

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

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project      = "BigData-Demo"
      Environment  = var.environment
      ManagedBy    = "Terraform"
      Repository   = "BigData-Demos"
    }
  }
}

# Data sources for account and region information
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# KMS Key for S3 encryption (optional)
resource "aws_kms_key" "s3_encryption" {
  count                   = var.enable_kms_encryption ? 1 : 0
  description             = "KMS key for S3 bucket encryption - ${var.environment}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Name        = "s3-encryption-key-${var.environment}"
    Purpose     = "S3Encryption"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "s3_encryption" {
  count         = var.enable_kms_encryption ? 1 : 0
  name          = "alias/s3-${var.environment}-encryption"
  target_key_id = aws_kms_key.s3_encryption[0].key_id
}

# Main Data Lake S3 Bucket using our module
module "data_lake_s3" {
  source = "../../modules/s3"

  # Basic Configuration
  bucket_name           = var.bucket_name
  environment          = var.environment
  enable_random_suffix = var.enable_random_suffix
  force_destroy        = var.force_destroy

  # Security Configuration
  versioning_enabled  = var.versioning_enabled
  kms_key_id          = var.enable_kms_encryption ? aws_kms_key.s3_encryption[0].arn : ""
  block_public_access = var.block_public_access
  logging_bucket      = var.logging_bucket

  # Data Lake Structure
  create_data_lake_structure = var.create_data_lake_structure
  data_lake_folders         = var.data_lake_folders

  # Lifecycle Management
  lifecycle_rules = var.lifecycle_rules

  # Event Notifications
  notifications = var.notifications

  # CORS Configuration
  cors_rules = var.cors_rules

  # Tags
  tags = var.tags
}

# Secondary bucket for logs (if logging is enabled locally)
module "logging_s3" {
  count  = var.create_logging_bucket ? 1 : 0
  source = "../../modules/s3"

  # Basic Configuration
  bucket_name           = "${var.bucket_name}-logs"
  environment          = var.environment
  enable_random_suffix = var.enable_random_suffix
  force_destroy        = var.force_destroy

  # Security Configuration
  versioning_enabled  = true
  block_public_access = true

  # Lifecycle for log retention
  lifecycle_rules = [
    {
      id      = "log_retention"
      enabled = true
      filter = {
        prefix = ""
      }
      expiration = {
        days = 90
      }
      transitions = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        }
      ]
    }
  ]

  # Tags
  tags = merge(var.tags, {
    Purpose = "AccessLogging"
    Type    = "LoggingBucket"
  })
}

# Lambda function for data processing (example)
resource "aws_lambda_function" "data_processor" {
  count            = var.create_lambda_processor ? 1 : 0
  filename         = "data_processor.zip"
  function_name    = "${var.bucket_name}-data-processor"
  role            = aws_iam_role.lambda_role[0].arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.lambda_zip[0].output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      BUCKET_NAME    = module.data_lake_s3.bucket_id
      ENVIRONMENT    = var.environment
      LOG_LEVEL      = "INFO"
    }
  }

  tags = merge(var.tags, {
    Purpose = "DataProcessing"
    Type    = "LambdaFunction"
  })
}

# Lambda function code (example)
data "archive_file" "lambda_zip" {
  count       = var.create_lambda_processor ? 1 : 0
  type        = "zip"
  output_path = "data_processor.zip"
  source {
    content = templatefile("${path.module}/lambda/data_processor.py", {
      bucket_name = module.data_lake_s3.bucket_id
    })
    filename = "index.py"
  }
}

# IAM role for Lambda function
resource "aws_iam_role" "lambda_role" {
  count = var.create_lambda_processor ? 1 : 0
  name  = "${var.bucket_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for Lambda to access S3
resource "aws_iam_role_policy" "lambda_s3_policy" {
  count = var.create_lambda_processor ? 1 : 0
  name  = "${var.bucket_name}-lambda-s3-policy"
  role  = aws_iam_role.lambda_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.data_lake_s3.bucket_arn,
          "${module.data_lake_s3.bucket_arn}/*"
        ]
      }
    ]
  })
}

# Lambda permission for S3 to invoke the function
resource "aws_lambda_permission" "s3_invoke_lambda" {
  count         = var.create_lambda_processor ? 1 : 0
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_processor[0].function_name
  principal     = "s3.amazonaws.com"
  source_arn    = module.data_lake_s3.bucket_arn
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  count             = var.create_lambda_processor ? 1 : 0
  name              = "/aws/lambda/${aws_lambda_function.data_processor[0].function_name}"
  retention_in_days = 14

  tags = merge(var.tags, {
    Purpose = "LambdaLogging"
    Type    = "CloudWatchLogGroup"
  })
}

# CloudWatch Metric Alarm for S3 bucket size
resource "aws_cloudwatch_metric_alarm" "bucket_size_alarm" {
  count               = var.enable_monitoring ? 1 : 0
  alarm_name          = "${module.data_lake_s3.bucket_id}-size-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BucketSizeBytes"
  namespace           = "AWS/S3"
  period              = "86400"  # 24 hours
  statistic           = "Average"
  threshold           = var.bucket_size_alarm_threshold
  alarm_description   = "This metric monitors S3 bucket size"
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []

  dimensions = {
    BucketName  = module.data_lake_s3.bucket_id
    StorageType = "StandardStorage"
  }

  tags = merge(var.tags, {
    Purpose = "Monitoring"
    Type    = "CloudWatchAlarm"
  })
}