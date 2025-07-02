# BigData-Demos

Modern data architecture portfolio showcasing multi-cloud data platforms, real-time analytics, and DevOps practices.

## Overview

Production-ready examples of:
- Multi-cloud data platforms (AWS, Azure, Databricks)
- Data lake architectures (Bronze/Silver/Gold medallion)
- Real-time and batch processing patterns
- Infrastructure as Code deployments
- Data quality and governance frameworks

## Architecture

```
Data Sources → Ingestion Layer → Storage Layer → Processing Layer → Analytics & ML
```

## Structure

```
BigData-Demos/
├── Cloud Platform/
│   ├── aws/                    # AWS data lake and EMR/EKS jobs
│   ├── azure/                  # Azure Data Factory pipelines
│   ├── databricks/            # Delta Live Tables and ML notebooks
│   └── dbt/                   # Data transformation and testing
├── DevOps Solution/
│   ├── Azure/                 # Azure data platform
│   ├── Azure_devops/          # CI/CD pipelines
│   ├── Bamboo/               # Build automation
│   └── Templating/           # Terraform and Jinja templates
└── Spark Application/
    └── metorikku/            # Configuration-driven Spark ETL
```

## Key Technologies

### Cloud Platforms
- **AWS**: S3, EMR, EKS, Glue
- **Azure**: Data Factory, SQL Database
- **Databricks**: Delta Live Tables, MLflow

### Processing Frameworks
- **Apache Spark**: Distributed data processing
- **Delta Lake**: ACID transactions for data lakes
- **dbt**: SQL-based data transformations
- **Metorikku**: Configuration-driven ETL

### DevOps & Infrastructure
- **Terraform**: Multi-cloud infrastructure as code
- **CI/CD**: Automated testing and deployment
- **Jinja2**: Configuration templating