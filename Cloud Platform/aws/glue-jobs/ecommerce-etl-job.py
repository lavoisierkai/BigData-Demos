"""
AWS Glue ETL Job: E-commerce Data Processing
==================================================

This job demonstrates a complete ETL pipeline for e-commerce data:
1. Read raw CSV data from S3
2. Clean and validate data
3. Apply business transformations
4. Partition and write to processed layer
5. Update Glue Data Catalog

Author: Data Architecture Demo
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql import functions as F
from pyspark.sql.types import *
import boto3
from datetime import datetime

# Initialize Glue context
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'raw_data_bucket',
    'processed_data_bucket',
    'database_name'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Configuration
RAW_BUCKET = args['raw_data_bucket']
PROCESSED_BUCKET = args['processed_data_bucket']
DATABASE_NAME = args['database_name']
TABLE_NAME = 'ecommerce_transactions'

def clean_and_validate_data(df):
    """
    Clean and validate the raw e-commerce data
    """
    # Remove duplicates
    df_clean = df.dropDuplicates(['transaction_id'])
    
    # Filter out invalid transactions
    df_clean = df_clean.filter(
        (F.col('amount') > 0) & 
        (F.col('amount') < 10000) &  # Reasonable upper limit
        (F.col('customer_id').isNotNull()) &
        (F.col('product_id').isNotNull())
    )
    
    # Clean product names
    df_clean = df_clean.withColumn(
        'product_name',
        F.regexp_replace(F.col('product_name'), '[^a-zA-Z0-9 ]', '')
    )
    
    # Standardize customer email
    df_clean = df_clean.withColumn(
        'customer_email',
        F.lower(F.trim(F.col('customer_email')))
    )
    
    return df_clean

def apply_business_transformations(df):
    """
    Apply business logic and create derived columns
    """
    # Calculate customer lifetime value category
    df_transformed = df.withColumn(
        'customer_value_category',
        F.when(F.col('amount') < 50, 'Low')
        .when(F.col('amount') < 200, 'Medium')
        .when(F.col('amount') < 500, 'High')
        .otherwise('Premium')
    )
    
    # Extract date components for partitioning
    df_transformed = df_transformed.withColumn(
        'transaction_date',
        F.to_date(F.col('timestamp'))
    ).withColumn(
        'year',
        F.year(F.col('transaction_date'))
    ).withColumn(
        'month',
        F.month(F.col('transaction_date'))
    ).withColumn(
        'day',
        F.dayofmonth(F.col('transaction_date'))
    )
    
    # Calculate product category performance metrics
    df_transformed = df_transformed.withColumn(
        'is_weekend',
        F.when(F.dayofweek(F.col('transaction_date')).isin([1, 7]), True)
        .otherwise(False)
    )
    
    # Add processing timestamp
    df_transformed = df_transformed.withColumn(
        'processed_timestamp',
        F.current_timestamp()
    )
    
    return df_transformed

def calculate_customer_metrics(df):
    """
    Calculate customer-level aggregations
    """
    customer_metrics = df.groupBy('customer_id', 'customer_email').agg(
        F.count('transaction_id').alias('total_transactions'),
        F.sum('amount').alias('total_spent'),
        F.avg('amount').alias('avg_transaction_amount'),
        F.max('transaction_date').alias('last_transaction_date'),
        F.min('transaction_date').alias('first_transaction_date'),
        F.countDistinct('product_category').alias('unique_categories_purchased')
    )
    
    # Calculate customer lifetime days
    customer_metrics = customer_metrics.withColumn(
        'customer_lifetime_days',
        F.datediff(F.col('last_transaction_date'), F.col('first_transaction_date'))
    )
    
    # Calculate customer segment
    customer_metrics = customer_metrics.withColumn(
        'customer_segment',
        F.when(
            (F.col('total_transactions') >= 10) & (F.col('total_spent') >= 1000), 'VIP'
        ).when(
            (F.col('total_transactions') >= 5) & (F.col('total_spent') >= 500), 'Gold'
        ).when(
            (F.col('total_transactions') >= 2) & (F.col('total_spent') >= 100), 'Silver'
        ).otherwise('Bronze')
    )
    
    return customer_metrics

def main():
    """
    Main ETL process
    """
    try:
        print("Starting E-commerce ETL Job...")
        
        # Read raw data from S3
        raw_data_path = f"s3://{RAW_BUCKET}/ecommerce/transactions/"
        print(f"Reading raw data from: {raw_data_path}")
        
        # Create dynamic frame from S3
        raw_dynamic_frame = glueContext.create_dynamic_frame.from_options(
            format_options={"quoteChar": "\"", "withHeader": True, "separator": ","},
            connection_type="s3",
            format="csv",
            connection_options={"paths": [raw_data_path], "recurse": True},
            transformation_ctx="raw_data"
        )
        
        # Convert to Spark DataFrame for easier manipulation
        raw_df = raw_dynamic_frame.toDF()
        
        print(f"Raw data count: {raw_df.count()}")
        
        # Data cleaning and validation
        clean_df = clean_and_validate_data(raw_df)
        print(f"Clean data count: {clean_df.count()}")
        
        # Apply business transformations
        transformed_df = apply_business_transformations(clean_df)
        
        # Write main transaction data partitioned by year/month
        processed_path = f"s3://{PROCESSED_BUCKET}/ecommerce/transactions/"
        print(f"Writing processed data to: {processed_path}")
        
        # Convert back to dynamic frame for writing
        processed_dynamic_frame = DynamicFrame.fromDF(transformed_df, glueContext, "processed_transactions")
        
        # Write partitioned data
        glueContext.write_dynamic_frame.from_options(
            frame=processed_dynamic_frame,
            connection_type="s3",
            connection_options={
                "path": processed_path,
                "partitionKeys": ["year", "month"]
            },
            format="parquet",
            transformation_ctx="write_processed_data"
        )
        
        # Calculate and write customer metrics
        customer_metrics_df = calculate_customer_metrics(transformed_df)
        customer_metrics_path = f"s3://{PROCESSED_BUCKET}/ecommerce/customer_metrics/"
        
        customer_metrics_dynamic_frame = DynamicFrame.fromDF(customer_metrics_df, glueContext, "customer_metrics")
        
        glueContext.write_dynamic_frame.from_options(
            frame=customer_metrics_dynamic_frame,
            connection_type="s3",
            connection_options={"path": customer_metrics_path},
            format="parquet",
            transformation_ctx="write_customer_metrics"
        )
        
        # Update Glue Data Catalog
        print("Updating Glue Data Catalog...")
        
        # Create or update table definition
        try:
            glueContext.create_dynamic_frame.from_catalog(
                database=DATABASE_NAME,
                table_name=TABLE_NAME
            )
        except:
            # Table doesn't exist, will be created automatically
            pass
        
        print("ETL Job completed successfully!")
        
        # Log job statistics
        job_stats = {
            'job_name': args['JOB_NAME'],
            'processed_records': transformed_df.count(),
            'customer_metrics_records': customer_metrics_df.count(),
            'completion_time': datetime.now().isoformat()
        }
        
        print(f"Job Statistics: {job_stats}")
        
    except Exception as e:
        print(f"Error in ETL job: {str(e)}")
        raise e
    
    finally:
        job.commit()

if __name__ == "__main__":
    main()