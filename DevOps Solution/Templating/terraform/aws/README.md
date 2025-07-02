# AWS Terraform Modules

Infrastructure as Code for AWS data platform components using Terraform.

## Modules

### S3 Module
Comprehensive S3 bucket configuration for data lake implementations.

**Features:**
- Data lake folder structure (Bronze/Silver/Gold layers)
- Lifecycle management for cost optimization
- Server-side encryption (S3-managed or KMS)
- Versioning and public access controls
- Event notifications for data processing
- CORS configuration for web applications
- CloudWatch monitoring and alarms

**Usage:**
```hcl
module "data_lake_s3" {
  source = "./modules/s3"
  
  bucket_name    = "my-data-lake"
  environment    = "dev"
  versioning_enabled = true
  
  create_data_lake_structure = true
  data_lake_folders = [
    "bronze/raw-data/orders",
    "silver/cleaned-data/orders",
    "gold/analytics/sales-reports"
  ]
  
  tags = {
    Project = "DataLake"
    Owner   = "DataEngineering"
  }
}
```

## Examples

### Data Lake Example
Basic data lake implementation with standard medallion architecture.

**Deploy:**
```bash
cd examples/data-lake
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply
```

### Production Example
Production-ready configuration with enhanced security and compliance features.

**Configuration:**
- Enhanced security with private endpoints
- Comprehensive lifecycle rules
- Event notifications for data processing
- Compliance-ready retention policies

## Directory Structure

```
aws/
├── modules/
│   └── s3/                 # S3 module for data lake
│       ├── main.tf         # Main resources
│       ├── variables.tf    # Input variables
│       └── outputs.tf      # Output values
└── examples/
    ├── data-lake/          # Basic data lake example
    └── production/         # Production configuration
```

## Key Features

### Security
- Server-side encryption (S3-managed or KMS)
- Public access blocking
- Bucket versioning
- Access logging

### Cost Optimization
- Intelligent lifecycle transitions
- Storage class optimization
- Temporary data cleanup
- Monitoring and alerting

### Data Lake Architecture
- Medallion architecture (Bronze/Silver/Gold)
- Standardized folder structure
- Event-driven processing
- Audit and compliance logging

## Variables

### Required
- `bucket_name` - Base name for S3 bucket
- `environment` - Environment (dev/staging/prod)

### Optional
- `versioning_enabled` - Enable bucket versioning (default: true)
- `create_data_lake_structure` - Create standard folders (default: true)
- `lifecycle_rules` - Custom lifecycle rules
- `tags` - Resource tags

## Outputs

### Bucket Information
- `bucket_id` - S3 bucket name
- `bucket_arn` - S3 bucket ARN
- `bucket_region` - AWS region

### Data Lake Paths
- `data_lake_paths` - Standard tier paths
- `integration_endpoints` - Service integration URLs
- `monitoring_info` - CloudWatch configuration