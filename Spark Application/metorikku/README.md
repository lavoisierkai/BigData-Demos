# Metorikku Spark ETL Applications

This directory showcases advanced Spark ETL applications using the Metorikku framework, demonstrating modern data engineering patterns and best practices.

## About Metorikku

Metorikku is a library that simplifies writing and executing Apache Spark ETL jobs by providing:
- **Configuration-driven development** - Define ETL logic in YAML files
- **Reusable components** - Pre-built transformations and data quality checks
- **Multiple data sources** - JDBC, S3, Kafka, file systems, and more
- **Flexible deployment** - Run on EMR, Databricks, Kubernetes, or local clusters

## Architecture Overview

```
Raw Data → Metorikku ETL Jobs → Processed Data → Business Intelligence
```

### Data Flow Patterns
1. **Batch Processing**: Scheduled ETL jobs for daily/hourly data processing
2. **Streaming Processing**: Real-time data ingestion and transformation
3. **Data Quality**: Validation and monitoring of data pipeline health
4. **Multi-Source Integration**: Combining data from various sources

## Directory Structure

```
metorikku/
├── config/                    # Metorikku configuration files
│   ├── ecommerce-etl.yaml   # E-commerce data processing
│   ├── customer-360.yaml    # Customer analytics pipeline
│   ├── realtime-events.yaml # Real-time event processing
│   └── data-quality.yaml    # Data quality monitoring
├── jdbc/                     # JDBC-based data processing
│   ├── customer-sync.yaml   # Customer data synchronization
│   ├── transaction-etl.yaml # Transaction processing
│   └── dimension-load.yaml  # Dimension table loading
├── s3/                       # S3-based data lake processing
│   ├── raw-to-silver.yaml   # Bronze to Silver layer transformation
│   ├── silver-to-gold.yaml  # Silver to Gold layer aggregation
│   └── data-archival.yaml   # Data lifecycle management
├── metrics/                  # Custom metric definitions
├── sql/                      # SQL transformation scripts
├── schemas/                  # Data schema definitions
└── deployment/               # Deployment configurations
```

## Key Features Demonstrated

### 1. Configuration-Driven ETL
- **Declarative pipelines** defined in YAML
- **Parameterized jobs** for different environments
- **Template-based configurations** for reusability

### 2. Data Source Integration
- **JDBC connections** to relational databases
- **S3 data lake** access with various formats
- **Kafka streaming** for real-time processing
- **REST API** data ingestion

### 3. Data Transformations
- **SQL-based transformations** for complex business logic
- **Custom Scala/Python UDFs** for specialized processing
- **Data quality checks** with expectations framework
- **Schema evolution** handling

### 4. Output Formats
- **Parquet** for optimized analytics
- **Delta Lake** for ACID transactions
- **Elasticsearch** for search and analytics
- **Database tables** for operational systems

## Getting Started

### Prerequisites
```bash
# Required software
Java 8 or 11
Apache Spark 3.x
Scala 2.12
Maven or SBT

# Optional (for specific features)
Docker (for containerized execution)
Kubernetes (for K8s deployment)
```

### Basic Usage

#### 1. Simple ETL Job
```bash
# Run e-commerce ETL pipeline
spark-submit \
  --class com.yotpo.metorikku.Metorikku \
  metorikku.jar \
  --config config/ecommerce-etl.yaml \
  --variables environment=prod,date=2024-01-15
```

#### 2. JDBC Processing
```bash
# Sync customer data from database
spark-submit \
  --class com.yotpo.metorikku.Metorikku \
  metorikku.jar \
  --config jdbc/customer-sync.yaml \
  --variables jdbc_url=jdbc:postgresql://localhost:5432/ecommerce
```

#### 3. S3 Data Lake Processing
```bash
# Process S3 data lake layers
spark-submit \
  --class com.yotpo.metorikku.Metorikku \
  metorikku.jar \
  --config s3/raw-to-silver.yaml \
  --variables s3_bucket=my-data-lake,processing_date=2024-01-15
```

## Use Cases Demonstrated

### 1. E-commerce Analytics
- **Customer behavior analysis** - Purchase patterns and segmentation
- **Product performance** - Sales metrics and recommendations
- **Revenue optimization** - Pricing and promotion analysis

### 2. Real-time Processing
- **Event stream processing** - User activity and system events
- **Fraud detection** - Real-time transaction monitoring
- **Operational metrics** - System health and performance

### 3. Data Quality Management
- **Schema validation** - Ensure data conformity
- **Completeness checks** - Monitor data pipeline health
- **Anomaly detection** - Identify data quality issues

### 4. Multi-Source Integration
- **Customer 360** - Unified customer view from multiple systems
- **Data warehouse loading** - ETL from operational systems
- **Master data management** - Reference data synchronization

## Configuration Examples

### Basic ETL Pipeline
```yaml
# config/ecommerce-etl.yaml
steps:
  - dataFrameName: raw_transactions
    sql: |
      SELECT 
        transaction_id,
        customer_id,
        product_id,
        amount,
        transaction_date
      FROM raw_data
      WHERE transaction_date = '${processing_date}'
  
  - dataFrameName: enriched_transactions
    sql: |
      SELECT 
        t.*,
        c.customer_tier,
        p.product_category
      FROM raw_transactions t
      JOIN customers c ON t.customer_id = c.customer_id
      JOIN products p ON t.product_id = p.product_id

inputs:
  - name: raw_data
    path: s3a://data-lake/raw/transactions/
    format: parquet
  - name: customers
    path: s3a://data-lake/dimensions/customers/
    format: delta
  - name: products
    path: s3a://data-lake/dimensions/products/
    format: delta

outputs:
  - dataFrameName: enriched_transactions
    outputType: file
    outputOptions:
      path: s3a://data-lake/processed/transactions/
      format: delta
      mode: overwrite
      partitionBy: ["transaction_date"]
```

### JDBC Integration
```yaml
# jdbc/customer-sync.yaml
inputs:
  - name: source_customers
    jdbcOptions:
      url: ${jdbc_url}
      dbtable: customers
      user: ${jdbc_user}
      password: ${jdbc_password}
      driver: org.postgresql.Driver

steps:
  - dataFrameName: validated_customers
    sql: |
      SELECT 
        customer_id,
        email,
        first_name,
        last_name,
        registration_date,
        CURRENT_TIMESTAMP() as sync_timestamp
      FROM source_customers
      WHERE email IS NOT NULL
        AND registration_date >= '2020-01-01'

outputs:
  - dataFrameName: validated_customers
    outputType: file
    outputOptions:
      path: s3a://data-lake/dimensions/customers/
      format: delta
      mode: upsert
      mergeKey: customer_id
```

## Advanced Features

### 1. Data Quality Checks
```yaml
# Built-in data quality validations
dataQuality:
  - dataFrameName: validated_customers
    checks:
      - type: not_null
        column: customer_id
      - type: unique
        column: email
      - type: range
        column: age
        min: 18
        max: 120
```

### 2. Custom Metrics
```yaml
# Custom business metrics
metrics:
  - name: daily_revenue
    dataFrameName: enriched_transactions
    aggregation: sum
    column: amount
  - name: active_customers
    dataFrameName: enriched_transactions
    aggregation: count_distinct
    column: customer_id
```

### 3. Streaming Configuration
```yaml
# Real-time stream processing
streaming:
  triggerMode: ProcessingTime
  triggerDuration: "30 seconds"
  checkpointLocation: s3a://data-lake/checkpoints/events/

inputs:
  - name: user_events
    kafka:
      servers: kafka-cluster:9092
      topic: user_events
      startingOffsets: latest
```

## Deployment Options

### 1. AWS EMR
```bash
# Submit to EMR cluster
aws emr add-steps \
  --cluster-id j-XXXXXXXXX \
  --steps file://emr-step.json
```

### 2. Kubernetes
```yaml
# k8s-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: metorikku-etl
spec:
  template:
    spec:
      containers:
      - name: spark-job
        image: metorikku:latest
        args: ["--config", "config/ecommerce-etl.yaml"]
```

### 3. Databricks
```python
# Databricks notebook cell
%sh
/databricks/spark/bin/spark-submit \
  --class com.yotpo.metorikku.Metorikku \
  /mnt/jars/metorikku.jar \
  --config /mnt/configs/ecommerce-etl.yaml
```

## Monitoring & Observability

### 1. Spark UI Integration
- Custom metrics displayed in Spark UI
- Job progress and performance monitoring
- SQL query execution plans

### 2. External Monitoring
- CloudWatch metrics for AWS deployments
- Prometheus metrics for Kubernetes
- Custom dashboards with Grafana

### 3. Data Lineage
- Automatic lineage tracking
- Integration with data catalogs
- Impact analysis for schema changes

## Testing Framework

### 1. Unit Tests
```scala
// Scala test example
class EcommerceETLTest extends FunSuite with SparkSessionTestWrapper {
  test("should enrich transactions with customer data") {
    val result = runMetorikkuJob("config/test-ecommerce-etl.yaml")
    assert(result.count() > 0)
    assert(result.columns.contains("customer_tier"))
  }
}
```

### 2. Integration Tests
```bash
# Run integration test suite
docker-compose up -d postgres kafka
./run-integration-tests.sh
docker-compose down
```

### 3. Data Quality Tests
```yaml
# Automated data quality testing
tests:
  - name: transaction_completeness
    sql: |
      SELECT COUNT(*) as missing_count
      FROM processed_transactions 
      WHERE customer_id IS NULL
    expect: 0
```

## Performance Optimization

### 1. Spark Configuration
```yaml
# Optimized Spark settings
spark:
  executor:
    memory: "4g"
    cores: 2
    instances: 10
  sql:
    adaptive:
      enabled: true
      coalescePartitions:
        enabled: true
```

### 2. Data Partitioning
```yaml
# Optimal partitioning strategy
outputs:
  - dataFrameName: transactions
    outputOptions:
      partitionBy: ["year", "month"]
      bucketBy: 
        columns: ["customer_id"]
        numBuckets: 50
```

## Best Practices

1. **Configuration Management**
   - Use environment-specific variables
   - Externalize sensitive credentials
   - Version control all configurations

2. **Error Handling**
   - Implement retry mechanisms
   - Use dead letter queues for failed records
   - Monitor job failures and alerts

3. **Resource Management**
   - Right-size Spark executors
   - Use dynamic allocation
   - Implement auto-scaling

4. **Data Governance**
   - Document data lineage
   - Implement access controls
   - Monitor data quality metrics

## Next Steps

1. **Extend Configurations** - Add more complex ETL scenarios
2. **Custom Functions** - Develop domain-specific transformations
3. **MLOps Integration** - Add machine learning pipeline steps
4. **Real-time Analytics** - Implement streaming analytics use cases