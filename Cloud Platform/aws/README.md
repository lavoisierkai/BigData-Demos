# AWS Cloud Data Platform - Enterprise Data Lake Architecture

This directory demonstrates comprehensive AWS data platform implementations, showcasing modern cloud-native data lake architecture, serverless analytics, machine learning operations, and enterprise-grade big data solutions on Amazon Web Services.

## Architecture Overview

```
AWS Data Platform Ecosystem
┌─────────────────────────────────────────────────────────────────┐
│                     Data Ingestion Layer                        │
├─────────────────────────────────────────────────────────────────┤
│ Kinesis Data Streams │ MSK (Kafka) │ DMS │ DataSync │ Direct Connect │
│ API Gateway │ Lambda │ S3 Transfer Acceleration │ AWS Snow Family │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Data Lake Storage                          │
├─────────────────────────────────────────────────────────────────┤
│ S3 Data Lake (Raw/Processed/Curated) │ Lake Formation Governance │
│ Intelligent Tiering │ Cross-Region Replication │ Lifecycle Mgmt │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Processing & Analytics Layer                   │
├─────────────────────────────────────────────────────────────────┤
│ EMR (Spark/Hadoop) │ Glue (Serverless ETL) │ Lambda │ Batch     │
│ Kinesis Analytics │ Athena │ Redshift │ OpenSearch │ QuickSight │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AI/ML & Advanced Analytics                    │
├─────────────────────────────────────────────────────────────────┤
│ SageMaker │ Comprehend │ Rekognition │ Forecast │ Personalize   │
│ Textract │ Transcribe │ Translate │ Polly │ Lex │ Bedrock       │
└─────────────────────────────────────────────────────────────────┘
```

## Key Capabilities Demonstrated

### 1. **Serverless Data Lake Architecture**
- **AWS Lake Formation**: Centralized data lake governance and security
- **S3 Intelligent Tiering**: Automatic cost optimization
- **Glue Data Catalog**: Unified metadata repository
- **Athena**: Serverless SQL analytics on data lake

### 2. **Real-Time & Batch Processing**
- **Kinesis Data Streams**: Real-time data ingestion and processing
- **EMR Serverless**: Serverless big data processing
- **Lambda**: Event-driven serverless computing
- **Step Functions**: Workflow orchestration

### 3. **Machine Learning Operations**
- **SageMaker**: End-to-end ML lifecycle management
- **Feature Store**: Centralized feature management
- **Model Registry**: ML model versioning and deployment
- **Autopilot**: Automated machine learning

## Directory Structure

```
aws/
├── README.md                          # This comprehensive guide
├── data-lake/                         # Data lake architecture
│   ├── infrastructure/                # CloudFormation/CDK templates
│   │   ├── core-infrastructure.yaml   # Core S3, IAM, networking
│   │   ├── glue-catalog.yaml          # Glue Data Catalog setup
│   │   ├── lake-formation.yaml        # Lake Formation governance
│   │   ├── athena-workgroups.yaml     # Athena query optimization
│   │   └── monitoring-stack.yaml      # CloudWatch monitoring
│   ├── medallion-architecture/        # Bronze/Silver/Gold implementation
│   │   ├── bronze-layer/              # Raw data ingestion
│   │   ├── silver-layer/              # Cleaned and validated data
│   │   └── gold-layer/                # Business-ready datasets
│   ├── data-governance/               # Data governance framework
│   │   ├── lake-formation-policies/   # Fine-grained access control
│   │   ├── data-quality-rules/        # Data quality validation
│   │   ├── lineage-tracking/          # Data lineage automation
│   │   └── compliance-automation/     # Regulatory compliance
│   └── cost-optimization/             # Cost optimization strategies
│       ├── lifecycle-policies/        # S3 lifecycle management
│       ├── storage-optimization/      # Storage class optimization
│       └── query-optimization/        # Query performance tuning
├── glue-jobs/                         # AWS Glue ETL scripts
│   ├── streaming-etl/                 # Real-time data processing
│   │   ├── kinesis-to-s3.py          # Streaming data ingestion
│   │   ├── real-time-enrichment.py   # Data enrichment pipeline
│   │   ├── change-data-capture.py    # CDC processing
│   │   └── streaming-aggregations.py # Real-time aggregations
│   ├── batch-etl/                     # Batch data processing
│   │   ├── ecommerce-etl-job.py      # E-commerce data pipeline
│   │   ├── log-processing.py         # Log data processing
│   │   ├── data-quality-validation.py # Data quality checks
│   │   └── incremental-processing.py # Incremental data loads
│   ├── data-catalog/                  # Data catalog automation
│   │   ├── schema-evolution.py       # Schema evolution handling
│   │   ├── metadata-extraction.py    # Automatic metadata extraction
│   │   └── catalog-optimization.py   # Catalog performance optimization
│   └── ml-data-prep/                  # ML data preparation
│       ├── feature-engineering.py    # Feature engineering pipeline
│       ├── data-preprocessing.py     # ML data preprocessing
│       └── training-data-prep.py     # Training dataset preparation
├── emr-jobs/                          # EMR Spark applications
│   ├── batch-processing/              # Large-scale batch processing
│   │   ├── realtime-analytics-spark-job.py # Real-time analytics
│   │   ├── data-lake-etl.py          # Comprehensive ETL pipeline
│   │   ├── machine-learning-training.py # ML model training
│   │   └── data-quality-framework.py # Data quality framework
│   ├── streaming-analytics/           # Real-time streaming
│   │   ├── kafka-spark-streaming.py  # Kafka integration
│   │   ├── kinesis-spark-processing.py # Kinesis integration
│   │   ├── real-time-ml-scoring.py   # Real-time ML inference
│   │   └── event-driven-processing.py # Event-driven analytics
│   ├── optimization/                  # Performance optimization
│   │   ├── spark-tuning-examples.py  # Spark performance tuning
│   │   ├── memory-optimization.py    # Memory usage optimization
│   │   └── cost-optimization.py      # Cost optimization strategies
│   └── advanced-analytics/            # Advanced analytics patterns
│       ├── graph-analytics.py        # Graph processing with GraphX
│       ├── time-series-analysis.py   # Time series analytics
│       ├── text-analytics.py         # NLP and text processing
│       └── recommendation-engine.py  # Recommendation systems
├── kinesis-analytics/                 # Real-time stream processing
│   ├── applications/                  # Kinesis Analytics applications
│   │   ├── real-time-dashboard.sql   # Real-time dashboard queries
│   │   ├── anomaly-detection.sql     # Real-time anomaly detection
│   │   ├── fraud-detection.sql       # Fraud detection pipeline
│   │   └── iot-analytics.sql         # IoT data processing
│   ├── flink-applications/            # Apache Flink applications
│   │   ├── complex-event-processing.py # Complex event processing
│   │   ├── session-analytics.py      # Session-based analytics
│   │   └── pattern-detection.py      # Pattern detection algorithms
│   └── stream-processing-patterns/    # Common streaming patterns
│       ├── windowing-operations.sql   # Window functions
│       ├── join-patterns.sql          # Stream joins
│       └── aggregation-patterns.sql   # Stream aggregations
├── lambda-functions/                  # Serverless data processing
│   ├── data-ingestion/                # Data ingestion functions
│   │   ├── api-data-collector.py     # API data collection
│   │   ├── file-processor.py         # File processing automation
│   │   ├── real-time-validator.py    # Real-time data validation
│   │   └── error-handler.py          # Error handling and retry
│   ├── data-transformation/           # Data transformation functions
│   │   ├── json-flattener.py         # JSON data flattening
│   │   ├── data-enrichment.py        # Data enrichment pipeline
│   │   ├── format-converter.py       # Data format conversion
│   │   └── schema-validator.py       # Schema validation
│   ├── machine-learning/              # ML-related functions
│   │   ├── model-inference.py        # Real-time model inference
│   │   ├── feature-calculation.py    # Feature calculation
│   │   ├── data-drift-detector.py    # Data drift monitoring
│   │   └── model-monitoring.py       # Model performance monitoring
│   └── automation/                    # Automation functions
│       ├── job-scheduler.py          # Job scheduling automation
│       ├── cost-optimizer.py         # Automated cost optimization
│       ├── security-monitor.py       # Security monitoring
│       └── compliance-checker.py     # Compliance validation
├── sagemaker/                         # Machine learning platform
│   ├── notebooks/                     # Jupyter notebooks
│   │   ├── exploratory-analysis/     # Data exploration
│   │   ├── model-development/        # Model development
│   │   ├── feature-engineering/      # Feature engineering
│   │   └── model-evaluation/         # Model evaluation
│   ├── training-jobs/                 # Training job configurations
│   │   ├── built-in-algorithms/      # Built-in algorithm usage
│   │   ├── custom-algorithms/        # Custom algorithm implementation
│   │   ├── distributed-training/     # Distributed training setup
│   │   └── hyperparameter-tuning/    # Hyperparameter optimization
│   ├── endpoints/                     # Model deployment
│   │   ├── real-time-inference/      # Real-time endpoints
│   │   ├── batch-transform/          # Batch inference
│   │   ├── multi-model-endpoints/    # Multi-model hosting
│   │   └── serverless-inference/     # Serverless inference
│   ├── pipelines/                     # ML pipeline automation
│   │   ├── training-pipeline.py      # Training pipeline
│   │   ├── inference-pipeline.py     # Inference pipeline
│   │   ├── data-processing-pipeline.py # Data processing pipeline
│   │   └── model-monitoring-pipeline.py # Model monitoring
│   └── mlops/                         # MLOps implementation
│       ├── ci-cd-ml-pipeline/        # CI/CD for ML models
│       ├── model-registry/           # Model versioning
│       ├── feature-store/            # Feature store implementation
│       └── model-governance/         # Model governance framework
├── quicksight/                        # Business intelligence
│   ├── datasets/                      # QuickSight dataset definitions
│   ├── dashboards/                    # Dashboard templates
│   ├── analyses/                      # Analysis templates
│   └── embedded-analytics/           # Embedded analytics setup
├── athena/                            # Serverless SQL analytics
│   ├── queries/                       # SQL query library
│   │   ├── performance-optimized/    # Performance-optimized queries
│   │   ├── cost-optimized/           # Cost-optimized queries
│   │   ├── complex-analytics/        # Complex analytical queries
│   │   └── data-quality/             # Data quality queries
│   ├── workgroups/                    # Athena workgroup configs
│   ├── saved-queries/                 # Saved query templates
│   └── optimization/                  # Query optimization techniques
├── redshift/                          # Data warehouse integration
│   ├── cluster-configurations/        # Cluster setup
│   ├── data-loading/                  # Data loading strategies
│   ├── query-optimization/            # Query performance tuning
│   └── integration-patterns/          # Integration with data lake
├── opensearch/                        # Search and analytics
│   ├── index-templates/               # Index configuration
│   ├── data-pipelines/                # Data ingestion pipelines
│   ├── dashboards/                    # Kibana dashboard configs
│   └── anomaly-detection/             # Anomaly detection setup
├── security/                          # Security implementation
│   ├── iam-policies/                  # IAM policy templates
│   ├── lake-formation/                # Lake Formation security
│   ├── encryption/                    # Encryption configurations
│   ├── network-security/              # VPC and network security
│   └── compliance/                    # Compliance frameworks
├── monitoring/                        # Monitoring and observability
│   ├── cloudwatch/                    # CloudWatch configurations
│   ├── x-ray/                         # Distributed tracing
│   ├── custom-metrics/                # Custom metrics implementation
│   └── alerting/                      # Alert configurations
├── automation/                        # Infrastructure automation
│   ├── cdk-stacks/                    # AWS CDK implementations
│   ├── terraform/                     # Terraform configurations
│   ├── cloudformation/                # CloudFormation templates
│   └── ci-cd-pipelines/               # CI/CD automation
├── sample-data/                       # Sample datasets
│   ├── ecommerce/                     # E-commerce sample data
│   ├── iot-sensors/                   # IoT sensor data
│   ├── web-logs/                      # Web server logs
│   ├── financial/                     # Financial transaction data
│   └── generate-sample-data.py        # Data generation scripts
├── scripts/                           # Utility scripts
│   ├── deployment/                    # Deployment automation
│   ├── data-migration/                # Data migration tools
│   ├── performance-testing/           # Performance testing tools
│   └── cost-analysis/                 # Cost analysis utilities
└── documentation/                     # Comprehensive documentation
    ├── architecture/                  # Architecture documentation
    ├── best-practices/                # AWS best practices
    ├── troubleshooting/               # Troubleshooting guides
    └── tutorials/                     # Step-by-step tutorials
```

## Key Implementation Highlights

### 1. **Serverless Data Lake with Lake Formation**

#### Modern Data Lake Architecture
```python
# AWS Glue job for medallion architecture implementation
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql import functions as F
from pyspark.sql.types import *

def process_bronze_to_silver(glueContext, spark):
    """
    Transform raw data (bronze) to validated data (silver)
    with data quality checks and schema evolution
    """
    
    # Read from bronze layer
    bronze_df = glueContext.create_dynamic_frame.from_catalog(
        database="data_lake_catalog",
        table_name="bronze_ecommerce_orders"
    ).toDF()
    
    # Data quality validations
    quality_checks = [
        # Null checks
        bronze_df.filter(F.col("order_id").isNull()).count() == 0,
        # Date range validation
        bronze_df.filter(F.col("order_date") < "2020-01-01").count() == 0,
        # Amount validation
        bronze_df.filter(F.col("order_amount") <= 0).count() == 0
    ]
    
    if not all(quality_checks):
        raise ValueError("Data quality validation failed")
    
    # Schema standardization and enrichment
    silver_df = bronze_df \
        .withColumn("order_date", F.to_date("order_date", "yyyy-MM-dd")) \
        .withColumn("order_amount", F.col("order_amount").cast(DecimalType(10,2))) \
        .withColumn("customer_id", F.col("customer_id").cast(StringType())) \
        .withColumn("processing_timestamp", F.current_timestamp()) \
        .withColumn("data_source", F.lit("ecommerce_api")) \
        .filter(F.col("order_amount") > 0) \
        .dropDuplicates(["order_id"])
    
    # Write to silver layer with partitioning
    silver_dynamic_frame = DynamicFrame.fromDF(silver_df, glueContext, "silver_frame")
    
    glueContext.write_dynamic_frame.from_options(
        frame=silver_dynamic_frame,
        connection_type="s3",
        connection_options={
            "path": "s3://data-lake-silver/ecommerce/orders/",
            "partitionKeys": ["year", "month"]
        },
        format="glueparquet",
        transformation_ctx="write_silver"
    )

def process_silver_to_gold(glueContext, spark):
    """
    Create business-ready aggregated datasets (gold layer)
    """
    
    # Read from silver layer
    silver_df = glueContext.create_dynamic_frame.from_catalog(
        database="data_lake_catalog",
        table_name="silver_ecommerce_orders"
    ).toDF()
    
    # Business aggregations
    daily_sales = silver_df \
        .groupBy("order_date", "product_category") \
        .agg(
            F.sum("order_amount").alias("total_sales"),
            F.count("order_id").alias("order_count"),
            F.countDistinct("customer_id").alias("unique_customers"),
            F.avg("order_amount").alias("avg_order_value")
        ) \
        .withColumn("created_timestamp", F.current_timestamp())
    
    # Customer lifetime value calculation
    customer_ltv = silver_df \
        .groupBy("customer_id") \
        .agg(
            F.sum("order_amount").alias("total_spent"),
            F.count("order_id").alias("total_orders"),
            F.min("order_date").alias("first_order_date"),
            F.max("order_date").alias("last_order_date"),
            F.avg("order_amount").alias("avg_order_value")
        ) \
        .withColumn("customer_lifetime_days", 
                   F.datediff(F.col("last_order_date"), F.col("first_order_date"))) \
        .withColumn("created_timestamp", F.current_timestamp())
    
    # Write gold layer datasets
    for dataset_name, dataset_df in [("daily_sales", daily_sales), ("customer_ltv", customer_ltv)]:
        gold_dynamic_frame = DynamicFrame.fromDF(dataset_df, glueContext, f"gold_{dataset_name}")
        
        glueContext.write_dynamic_frame.from_options(
            frame=gold_dynamic_frame,
            connection_type="s3",
            connection_options={
                "path": f"s3://data-lake-gold/ecommerce/{dataset_name}/",
                "partitionKeys": ["year", "month"] if dataset_name == "daily_sales" else []
            },
            format="glueparquet",
            transformation_ctx=f"write_gold_{dataset_name}"
        )
```

### 2. **Real-Time Analytics with Kinesis**

#### Streaming Data Pipeline
```python
# EMR Spark Streaming job for real-time analytics
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json

def create_spark_session():
    return SparkSession.builder \
        .appName("RealTimeEcommerceAnalytics") \
        .config("spark.streaming.receiver.writeAheadLog.enable", "true") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()

def process_kinesis_stream(spark):
    """
    Process real-time e-commerce events from Kinesis Data Streams
    """
    
    # Define schema for incoming events
    event_schema = StructType([
        StructField("event_id", StringType(), True),
        StructField("user_id", StringType(), True),
        StructField("session_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("product_id", StringType(), True),
        StructField("category", StringType(), True),
        StructField("price", DoubleType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("user_agent", StringType(), True),
        StructField("ip_address", StringType(), True)
    ])
    
    # Read from Kinesis stream
    kinesis_df = spark \
        .readStream \
        .format("kinesis") \
        .option("streamName", "ecommerce-events") \
        .option("region", "us-east-1") \
        .option("initialPosition", "latest") \
        .option("awsAccessKeyId", "<access-key>") \
        .option("awsSecretKey", "<secret-key>") \
        .load()
    
    # Parse JSON events
    parsed_df = kinesis_df \
        .select(from_json(col("data").cast("string"), event_schema).alias("event")) \
        .select("event.*") \
        .withWatermark("timestamp", "10 minutes")
    
    # Real-time aggregations
    # 1. Event counts by type in 5-minute windows
    event_counts = parsed_df \
        .groupBy(
            window(col("timestamp"), "5 minutes", "1 minute"),
            col("event_type")
        ) \
        .count() \
        .withColumn("window_start", col("window.start")) \
        .withColumn("window_end", col("window.end")) \
        .drop("window")
    
    # 2. Revenue tracking in real-time
    revenue_stream = parsed_df \
        .filter(col("event_type") == "purchase") \
        .groupBy(
            window(col("timestamp"), "5 minutes", "1 minute"),
            col("category")
        ) \
        .agg(
            sum("price").alias("total_revenue"),
            count("*").alias("purchase_count"),
            avg("price").alias("avg_order_value")
        ) \
        .withColumn("window_start", col("window.start")) \
        .withColumn("window_end", col("window.end")) \
        .drop("window")
    
    # 3. User behavior analysis
    user_behavior = parsed_df \
        .groupBy(
            window(col("timestamp"), "10 minutes", "2 minutes"),
            col("user_id")
        ) \
        .agg(
            count("*").alias("event_count"),
            countDistinct("product_id").alias("unique_products_viewed"),
            collect_list("event_type").alias("event_sequence")
        ) \
        .withColumn("session_duration_minutes", lit(10)) \
        .withColumn("window_start", col("window.start")) \
        .withColumn("window_end", col("window.end")) \
        .drop("window")
    
    # Output streams to different destinations
    # Write event counts to S3
    event_counts_query = event_counts.writeStream \
        .outputMode("append") \
        .format("json") \
        .option("path", "s3a://real-time-analytics/event-counts/") \
        .option("checkpointLocation", "s3a://real-time-analytics/checkpoints/event-counts/") \
        .trigger(processingTime="30 seconds") \
        .start()
    
    # Write revenue data to DynamoDB for real-time dashboards
    revenue_query = revenue_stream.writeStream \
        .outputMode("append") \
        .format("org.apache.spark.sql.dynamodb") \
        .option("tableName", "real-time-revenue") \
        .option("region", "us-east-1") \
        .trigger(processingTime="30 seconds") \
        .start()
    
    # Write user behavior to Kinesis for further processing
    behavior_query = user_behavior.writeStream \
        .outputMode("append") \
        .format("kinesis") \
        .option("streamName", "user-behavior-insights") \
        .option("region", "us-east-1") \
        .trigger(processingTime="60 seconds") \
        .start()
    
    return [event_counts_query, revenue_query, behavior_query]

# Anomaly detection with machine learning
def detect_anomalies(parsed_df):
    """
    Real-time anomaly detection using statistical methods
    """
    
    # Calculate baseline metrics
    baseline_metrics = parsed_df \
        .groupBy(window(col("timestamp"), "1 hour", "10 minutes")) \
        .agg(
            avg("price").alias("avg_price"),
            stddev("price").alias("stddev_price"),
            count("*").alias("event_count")
        )
    
    # Join with real-time data to detect anomalies
    anomaly_detection = parsed_df \
        .join(baseline_metrics, 
              parsed_df.timestamp.between(
                  baseline_metrics.window.start,
                  baseline_metrics.window.end
              )) \
        .withColumn("z_score", 
                   abs(col("price") - col("avg_price")) / col("stddev_price")) \
        .filter(col("z_score") > 3) \
        .select("event_id", "user_id", "product_id", "price", "z_score", "timestamp")
    
    # Alert on anomalies
    anomaly_alerts = anomaly_detection.writeStream \
        .outputMode("append") \
        .format("kinesis") \
        .option("streamName", "anomaly-alerts") \
        .option("region", "us-east-1") \
        .trigger(processingTime="10 seconds") \
        .start()
    
    return anomaly_alerts

if __name__ == "__main__":
    spark = create_spark_session()
    
    # Start streaming queries
    queries = process_kinesis_stream(spark)
    
    # Wait for termination
    for query in queries:
        query.awaitTermination()
```

### 3. **Machine Learning with SageMaker**

#### MLOps Pipeline Implementation
```python
# SageMaker MLOps pipeline for customer churn prediction
import boto3
import sagemaker
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep, CreateModelStep
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.sklearn.estimator import SKLearn

def create_churn_prediction_pipeline():
    """
    Create an end-to-end ML pipeline for customer churn prediction
    """
    
    # Initialize SageMaker session
    pipeline_session = PipelineSession()
    region = boto3.Session().region_name
    sagemaker_session = sagemaker.Session()
    bucket = sagemaker_session.default_bucket()
    role = sagemaker.get_execution_role()
    
    # Data processing step
    sklearn_processor = SKLearnProcessor(
        framework_version="0.23-1",
        instance_type="ml.m5.large",
        instance_count=1,
        base_job_name="churn-preprocessing",
        sagemaker_session=pipeline_session,
        role=role
    )
    
    processing_step = ProcessingStep(
        name="ChurnDataProcessing",
        processor=sklearn_processor,
        code="preprocessing.py",
        inputs=[
            ProcessingInput(
                source="s3://{}/data/raw/customer_data.csv".format(bucket),
                destination="/opt/ml/processing/input"
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name="train_data",
                source="/opt/ml/processing/train",
                destination="s3://{}/data/processed/train".format(bucket)
            ),
            ProcessingOutput(
                output_name="validation_data", 
                source="/opt/ml/processing/validation",
                destination="s3://{}/data/processed/validation".format(bucket)
            ),
            ProcessingOutput(
                output_name="test_data",
                source="/opt/ml/processing/test", 
                destination="s3://{}/data/processed/test".format(bucket)
            )
        ]
    )
    
    # Model training step
    sklearn_estimator = SKLearn(
        entry_point="train.py",
        framework_version="0.23-1",
        instance_type="ml.m5.large",
        role=role,
        sagemaker_session=pipeline_session,
        hyperparameters={
            "n_estimators": 100,
            "max_depth": 10,
            "random_state": 42
        }
    )
    
    training_step = TrainingStep(
        name="ChurnModelTraining",
        estimator=sklearn_estimator,
        inputs={
            "train": TrainingInput(
                s3_data=processing_step.properties.ProcessingOutputConfig.Outputs[
                    "train_data"
                ].S3Output.S3Uri,
                content_type="text/csv"
            ),
            "validation": TrainingInput(
                s3_data=processing_step.properties.ProcessingOutputConfig.Outputs[
                    "validation_data"
                ].S3Output.S3Uri,
                content_type="text/csv"
            )
        }
    )
    
    # Model evaluation step
    evaluation_processor = SKLearnProcessor(
        framework_version="0.23-1",
        instance_type="ml.m5.large",
        instance_count=1,
        base_job_name="churn-evaluation",
        sagemaker_session=pipeline_session,
        role=role
    )
    
    evaluation_step = ProcessingStep(
        name="ChurnModelEvaluation",
        processor=evaluation_processor,
        code="evaluate.py",
        inputs=[
            ProcessingInput(
                source=training_step.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model"
            ),
            ProcessingInput(
                source=processing_step.properties.ProcessingOutputConfig.Outputs[
                    "test_data"
                ].S3Output.S3Uri,
                destination="/opt/ml/processing/test"
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name="evaluation_report",
                source="/opt/ml/processing/evaluation",
                destination="s3://{}/evaluation/churn-model".format(bucket)
            )
        ]
    )
    
    # Model creation step
    model_step = CreateModelStep(
        name="ChurnCreateModel",
        model=Model(
            image_uri=sklearn_estimator.training_image_uri(),
            model_data=training_step.properties.ModelArtifacts.S3ModelArtifacts,
            sagemaker_session=pipeline_session,
            role=role
        )
    )
    
    # Create pipeline
    pipeline = Pipeline(
        name="CustomerChurnPredictionPipeline",
        parameters=[],
        steps=[processing_step, training_step, evaluation_step, model_step],
        sagemaker_session=pipeline_session
    )
    
    return pipeline

# Feature engineering for churn prediction
def feature_engineering_pipeline():
    """
    Advanced feature engineering for customer churn prediction
    """
    
    feature_engineering_code = """
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif

def create_churn_features(df):
    # Recency, Frequency, Monetary (RFM) analysis
    current_date = df['last_activity_date'].max()
    
    customer_features = df.groupby('customer_id').agg({
        'order_date': ['count', 'min', 'max'],
        'order_amount': ['sum', 'mean', 'std', 'min', 'max'],
        'last_activity_date': 'max',
        'support_tickets': 'sum',
        'product_returns': 'sum'
    }).reset_index()
    
    # Flatten column names
    customer_features.columns = ['_'.join(col).strip() if col[1] else col[0] 
                               for col in customer_features.columns.values]
    
    # Calculate recency (days since last activity)
    customer_features['recency_days'] = (
        current_date - customer_features['last_activity_date_max']
    ).dt.days
    
    # Calculate customer lifetime (days between first and last order)
    customer_features['customer_lifetime_days'] = (
        customer_features['order_date_max'] - customer_features['order_date_min']
    ).dt.days
    
    # Calculate frequency metrics
    customer_features['order_frequency'] = (
        customer_features['order_date_count'] / 
        (customer_features['customer_lifetime_days'] + 1)
    )
    
    # Create risk segments
    customer_features['high_value_customer'] = (
        customer_features['order_amount_sum'] > 
        customer_features['order_amount_sum'].quantile(0.8)
    ).astype(int)
    
    customer_features['frequent_returner'] = (
        customer_features['product_returns_sum'] > 
        customer_features['product_returns_sum'].quantile(0.9)
    ).astype(int)
    
    customer_features['support_heavy'] = (
        customer_features['support_tickets_sum'] > 
        customer_features['support_tickets_sum'].quantile(0.8)
    ).astype(int)
    
    # Behavioral features
    customer_features['avg_days_between_orders'] = (
        customer_features['customer_lifetime_days'] / 
        customer_features['order_date_count']
    )
    
    customer_features['order_amount_consistency'] = (
        customer_features['order_amount_std'] / 
        customer_features['order_amount_mean']
    )
    
    # Churn indicator (no activity in last 90 days)
    customer_features['is_churned'] = (
        customer_features['recency_days'] > 90
    ).astype(int)
    
    return customer_features

def select_features(X, y, k=20):
    selector = SelectKBest(score_func=f_classif, k=k)
    X_selected = selector.fit_transform(X, y)
    selected_features = X.columns[selector.get_support()].tolist()
    return X_selected, selected_features
"""
    
    return feature_engineering_code
```

## Performance Optimization Strategies

### 1. **S3 Performance Optimization**
```yaml
# S3 optimization configurations
S3OptimizationConfig:
  RequestPatterns:
    HighThroughput:
      - Use request rate optimization
      - Implement exponential backoff
      - Distribute keys across prefixes
    MixedWorkloads:
      - Separate read/write patterns  
      - Use appropriate storage classes
      - Implement lifecycle policies
  
  TransferAcceleration:
    Enabled: true
    UseFor: 
      - Large file uploads
      - Global data distribution
      - Cross-region transfers
  
  MultipartUpload:
    Threshold: 100MB
    ChunkSize: 10MB
    MaxConcurrency: 5
```

### 2. **EMR Performance Tuning**
```python
# EMR cluster optimization configuration
emr_cluster_config = {
    "Name": "OptimizedDataProcessingCluster",
    "ReleaseLabel": "emr-6.9.0",
    "Applications": [
        {"Name": "Spark"},
        {"Name": "Hadoop"},
        {"Name": "Hive"},
        {"Name": "JupyterHub"}
    ],
    "Instances": {
        "MasterInstanceType": "m5.xlarge",
        "SlaveInstanceType": "m5.2xlarge", 
        "InstanceCount": 5,
        "Ec2KeyName": "data-platform-key",
        "InstanceFleets": [
            {
                "Name": "MasterFleet",
                "InstanceFleetType": "MASTER",
                "TargetOnDemandCapacity": 1,
                "InstanceTypeConfigs": [
                    {
                        "InstanceType": "m5.xlarge",
                        "WeightedCapacity": 1
                    }
                ]
            },
            {
                "Name": "CoreFleet", 
                "InstanceFleetType": "CORE",
                "TargetOnDemandCapacity": 2,
                "TargetSpotCapacity": 3,
                "InstanceTypeConfigs": [
                    {
                        "InstanceType": "m5.2xlarge",
                        "WeightedCapacity": 1,
                        "BidPriceAsPercentageOfOnDemandPrice": 50
                    },
                    {
                        "InstanceType": "c5.2xlarge", 
                        "WeightedCapacity": 1,
                        "BidPriceAsPercentageOfOnDemandPrice": 50
                    }
                ]
            }
        ]
    },
    "Configurations": [
        {
            "Classification": "spark-defaults",
            "Properties": {
                "spark.sql.adaptive.enabled": "true",
                "spark.sql.adaptive.coalescePartitions.enabled": "true",
                "spark.sql.adaptive.skewJoin.enabled": "true",
                "spark.sql.adaptive.localShuffleReader.enabled": "true",
                "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
                "spark.dynamicAllocation.enabled": "true",
                "spark.dynamicAllocation.minExecutors": "1",
                "spark.dynamicAllocation.maxExecutors": "100",
                "spark.sql.execution.arrow.pyspark.enabled": "true",
                "spark.sql.parquet.columnarReaderBatchSize": "8192",
                "spark.sql.parquet.compression.codec": "snappy"
            }
        },
        {
            "Classification": "yarn-site",
            "Properties": {
                "yarn.nodemanager.resource.memory-mb": "14336",
                "yarn.scheduler.maximum-allocation-mb": "14336", 
                "yarn.nodemanager.vmem-check-enabled": "false",
                "yarn.log-aggregation-enable": "true"
            }
        }
    ],
    "AutoScalingRole": "EMR_AutoScaling_DefaultRole",
    "ScaleDownBehavior": "TERMINATE_AT_TASK_COMPLETION"
}
```

## Best Practices Implemented

### 1. **Data Lake Governance**
- **Lake Formation**: Centralized permissions and fine-grained access control
- **Data Catalog**: Automated schema discovery and metadata management
- **Data Quality**: Comprehensive validation and monitoring frameworks
- **Lineage Tracking**: End-to-end data lineage with AWS Glue

### 2. **Cost Optimization**
- **S3 Intelligent Tiering**: Automatic cost optimization
- **Spot Instances**: 50-80% cost reduction for EMR workloads
- **Reserved Capacity**: Predictable workload cost optimization
- **Lifecycle Policies**: Automated data archival and deletion

### 3. **Security & Compliance**
- **IAM Policies**: Least privilege access controls
- **Encryption**: End-to-end encryption at rest and in transit
- **VPC Integration**: Network isolation and security
- **CloudTrail**: Comprehensive audit logging

### 4. **Operational Excellence**
- **Infrastructure as Code**: CDK and CloudFormation templates
- **Monitoring**: CloudWatch metrics and custom dashboards
- **Alerting**: Proactive alerting and incident response
- **Automation**: Event-driven serverless automation

This comprehensive AWS implementation demonstrates enterprise-grade data platform capabilities, providing a complete foundation for modern data-driven organizations on Amazon Web Services.