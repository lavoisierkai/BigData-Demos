#!/usr/bin/env python3
"""
Sample Spark Application for EKS Deployment
Data Processing Pipeline for E-commerce Analytics

This application demonstrates:
- Reading data from S3
- Data transformation and aggregation
- Writing results back to S3 in Parquet format
- Delta Lake integration for ACID transactions
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_spark_session(app_name):
    """Create Spark session with optimized configurations for EKS"""
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128MB") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.WebIdentityTokenCredentialsProvider") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

def read_raw_data(spark, input_path):
    """Read raw e-commerce data from S3"""
    logger.info(f"Reading data from: {input_path}")
    
    # Define schema for better performance
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("product_id", StringType(), True),
        StructField("product_name", StringType(), True),
        StructField("category", StringType(), True),
        StructField("quantity", IntegerType(), True),
        StructField("unit_price", DoubleType(), True),
        StructField("order_date", TimestampType(), True),
        StructField("customer_location", StringType(), True),
        StructField("payment_method", StringType(), True)
    ])
    
    return spark.read \
        .option("header", "true") \
        .schema(schema) \
        .csv(input_path)

def transform_data(df):
    """Apply business transformations"""
    logger.info("Applying data transformations")
    
    # Calculate derived metrics
    transformed_df = df.withColumn("total_amount", col("quantity") * col("unit_price")) \
        .withColumn("order_year", year(col("order_date"))) \
        .withColumn("order_month", month(col("order_date"))) \
        .withColumn("order_day", dayofmonth(col("order_date"))) \
        .withColumn("order_hour", hour(col("order_date"))) \
        .filter(col("total_amount") > 0) \
        .filter(col("quantity") > 0)
    
    return transformed_df

def create_aggregations(df):
    """Create various business aggregations"""
    logger.info("Creating business aggregations")
    
    # Daily sales summary
    daily_sales = df.groupBy("order_year", "order_month", "order_day") \
        .agg(
            sum("total_amount").alias("daily_revenue"),
            count("order_id").alias("daily_orders"),
            countDistinct("customer_id").alias("unique_customers"),
            avg("total_amount").alias("avg_order_value")
        ) \
        .orderBy("order_year", "order_month", "order_day")
    
    # Product performance
    product_performance = df.groupBy("product_id", "product_name", "category") \
        .agg(
            sum("total_amount").alias("product_revenue"),
            sum("quantity").alias("total_quantity_sold"),
            count("order_id").alias("order_count"),
            countDistinct("customer_id").alias("unique_buyers")
        ) \
        .orderBy(desc("product_revenue"))
    
    # Customer analytics
    customer_analytics = df.groupBy("customer_id", "customer_location") \
        .agg(
            sum("total_amount").alias("customer_lifetime_value"),
            count("order_id").alias("total_orders"),
            countDistinct("product_id").alias("unique_products_purchased"),
            max("order_date").alias("last_order_date"),
            min("order_date").alias("first_order_date")
        ) \
        .orderBy(desc("customer_lifetime_value"))
    
    # Hourly patterns
    hourly_patterns = df.groupBy("order_hour") \
        .agg(
            sum("total_amount").alias("hourly_revenue"),
            count("order_id").alias("hourly_orders"),
            avg("total_amount").alias("avg_order_value_by_hour")
        ) \
        .orderBy("order_hour")
    
    return {
        "daily_sales": daily_sales,
        "product_performance": product_performance,
        "customer_analytics": customer_analytics,
        "hourly_patterns": hourly_patterns
    }

def write_to_delta_lake(df, output_path, partition_cols=None):
    """Write DataFrame to Delta Lake format"""
    logger.info(f"Writing to Delta Lake: {output_path}")
    
    writer = df.write.format("delta").mode("overwrite")
    
    if partition_cols:
        writer = writer.partitionBy(*partition_cols)
    
    writer.save(output_path)

def write_to_parquet(df, output_path, partition_cols=None):
    """Write DataFrame to Parquet format"""
    logger.info(f"Writing to Parquet: {output_path}")
    
    writer = df.write.format("parquet").mode("overwrite")
    
    if partition_cols:
        writer = writer.partitionBy(*partition_cols)
    
    writer.save(output_path)

def data_quality_checks(df):
    """Perform basic data quality checks"""
    logger.info("Performing data quality checks")
    
    total_records = df.count()
    null_orders = df.filter(col("order_id").isNull()).count()
    null_customers = df.filter(col("customer_id").isNull()).count()
    negative_amounts = df.filter(col("total_amount") < 0).count()
    
    logger.info(f"Data Quality Report:")
    logger.info(f"Total Records: {total_records}")
    logger.info(f"Null Order IDs: {null_orders}")
    logger.info(f"Null Customer IDs: {null_customers}")
    logger.info(f"Negative Amounts: {negative_amounts}")
    
    if null_orders > 0 or null_customers > 0 or negative_amounts > 0:
        logger.warning("Data quality issues detected!")
    else:
        logger.info("Data quality checks passed!")

def main():
    """Main application logic"""
    if len(sys.argv) != 3:
        print("Usage: spark-submit sample-data-processing.py <input_path> <output_path>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Create Spark session
    spark = create_spark_session("EKS-Ecommerce-Analytics")
    
    try:
        # Read raw data
        raw_df = read_raw_data(spark, input_path)
        
        # Transform data
        transformed_df = transform_data(raw_df)
        
        # Cache transformed data for multiple operations
        transformed_df.cache()
        
        # Perform data quality checks
        data_quality_checks(transformed_df)
        
        # Create aggregations
        aggregations = create_aggregations(transformed_df)
        
        # Write results to different formats
        
        # 1. Write raw transformed data to Delta Lake (partitioned by year/month)
        write_to_delta_lake(
            transformed_df, 
            f"{output_path}/delta/raw_orders",
            ["order_year", "order_month"]
        )
        
        # 2. Write aggregations to Parquet
        write_to_parquet(
            aggregations["daily_sales"], 
            f"{output_path}/parquet/daily_sales"
        )
        
        write_to_parquet(
            aggregations["product_performance"], 
            f"{output_path}/parquet/product_performance"
        )
        
        write_to_parquet(
            aggregations["customer_analytics"], 
            f"{output_path}/parquet/customer_analytics"
        )
        
        write_to_parquet(
            aggregations["hourly_patterns"], 
            f"{output_path}/parquet/hourly_patterns"
        )
        
        # Show sample results
        logger.info("Sample Daily Sales Data:")
        aggregations["daily_sales"].show(10, truncate=False)
        
        logger.info("Top 10 Products by Revenue:")
        aggregations["product_performance"].show(10, truncate=False)
        
        logger.info("Application completed successfully!")
        
    except Exception as e:
        logger.error(f"Application failed with error: {str(e)}")
        raise e
    
    finally:
        spark.stop()

if __name__ == "__main__":
    main()