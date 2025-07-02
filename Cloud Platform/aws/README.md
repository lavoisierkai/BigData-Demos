# AWS Data Lake Architecture Demo

This demo showcases a modern data lake architecture using AWS services including S3, Glue, EMR, and other data engineering tools.

## Architecture Overview

```
Raw Data (S3) → AWS Glue ETL → Processed Data (S3) → Analytics (Athena/EMR)
```

### Data Lake Layers
- **Raw Layer**: Ingested data in original format
- **Processed Layer**: Cleaned and transformed data
- **Curated Layer**: Business-ready datasets

### AWS Services Used
- **S3**: Data lake storage with lifecycle policies
- **Glue**: Serverless ETL jobs and data catalog
- **EMR**: Managed Spark clusters for big data processing
- **Athena**: Serverless SQL queries
- **CloudFormation**: Infrastructure as Code

## Directory Structure

```
aws/
├── infrastructure/          # CloudFormation templates
├── glue-jobs/              # AWS Glue ETL scripts
├── emr-jobs/               # EMR Spark applications
├── sample-data/            # Test datasets
└── scripts/                # Deployment and utility scripts
```

## Getting Started

1. Deploy infrastructure: `aws cloudformation create-stack --template-body file://infrastructure/data-lake-stack.yaml`
2. Upload sample data to S3
3. Run Glue ETL jobs
4. Query data with Athena or run EMR jobs

## Use Cases Demonstrated

1. **E-commerce Analytics**: Customer behavior and sales data processing
2. **IoT Data Processing**: Sensor data ingestion and real-time analytics  
3. **Log Analytics**: Application log processing and monitoring
4. **Data Warehouse Migration**: Traditional ETL to modern ELT patterns