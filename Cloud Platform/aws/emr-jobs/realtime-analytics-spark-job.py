"""
EMR Spark Job: Real-time Analytics Processing
=============================================

This Spark application demonstrates advanced big data processing for real-time analytics:
1. Process streaming data from Kinesis
2. Perform complex aggregations and windowing
3. Machine learning feature engineering
4. Write results to multiple sinks (S3, DynamoDB)

Demonstrates:
- Structured Streaming
- Complex event processing
- Window operations
- ML feature engineering
- Multi-sink architecture

Author: Data Architecture Demo
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
import argparse
import sys
from datetime import datetime, timedelta

def create_spark_session(app_name="RealTimeAnalytics"):
    """
    Create Spark session with optimized configurations for real-time processing
    """
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
        .getOrCreate()

def define_schemas():
    """
    Define schemas for different data sources
    """
    # IoT sensor data schema
    iot_schema = StructType([
        StructField("sensor_id", StringType(), True),
        StructField("device_type", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("temperature", DoubleType(), True),
        StructField("humidity", DoubleType(), True),
        StructField("pressure", DoubleType(), True),
        StructField("location", StringType(), True),
        StructField("battery_level", DoubleType(), True)
    ])
    
    # User activity schema
    activity_schema = StructType([
        StructField("user_id", StringType(), True),
        StructField("session_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("page_url", StringType(), True),
        StructField("duration_seconds", IntegerType(), True),
        StructField("device_info", StringType(), True),
        StructField("location", StringType(), True)
    ])
    
    return iot_schema, activity_schema

def process_iot_data(spark, s3_input_path, s3_output_path):
    """
    Process IoT sensor data with advanced analytics
    """
    print("Processing IoT sensor data...")
    
    # Read streaming data from S3 (simulating Kinesis)
    iot_df = spark.readStream \
        .format("json") \
        .option("path", s3_input_path + "/iot-data/") \
        .load()
    
    # Data quality checks and filtering
    iot_clean = iot_df.filter(
        (col("temperature").between(-50, 100)) &
        (col("humidity").between(0, 100)) &
        (col("pressure") > 0) &
        (col("battery_level").between(0, 100))
    )
    
    # Add derived columns
    iot_enriched = iot_clean \
        .withColumn("processing_time", current_timestamp()) \
        .withColumn("date", to_date(col("timestamp"))) \
        .withColumn("hour", hour(col("timestamp"))) \
        .withColumn("temperature_celsius", col("temperature")) \
        .withColumn("temperature_fahrenheit", (col("temperature") * 9/5) + 32) \
        .withColumn("heat_index", 
                   when((col("temperature") >= 27) & (col("humidity") >= 40),
                        -42.379 + 2.04901523 * col("temperature") + 
                        10.14333127 * col("humidity") - 
                        0.22475541 * col("temperature") * col("humidity"))
                   .otherwise(col("temperature"))) \
        .withColumn("battery_status",
                   when(col("battery_level") < 20, "Critical")
                   .when(col("battery_level") < 50, "Low")
                   .when(col("battery_level") < 80, "Medium")
                   .otherwise("High"))
    
    # Time-based aggregations (sliding windows)
    iot_windowed = iot_enriched \
        .withWatermark("timestamp", "10 minutes") \
        .groupBy(
            window(col("timestamp"), "5 minutes", "1 minute"),
            col("sensor_id"),
            col("device_type"),
            col("location")
        ) \
        .agg(
            avg("temperature").alias("avg_temperature"),
            max("temperature").alias("max_temperature"),
            min("temperature").alias("min_temperature"),
            stddev("temperature").alias("temperature_stddev"),
            avg("humidity").alias("avg_humidity"),
            avg("pressure").alias("avg_pressure"),
            avg("battery_level").alias("avg_battery_level"),
            count("*").alias("reading_count"),
            collect_list("temperature").alias("temperature_readings")
        ) \
        .withColumn("temperature_range", col("max_temperature") - col("min_temperature")) \
        .withColumn("anomaly_score",
                   when(col("temperature_stddev") > 5, "High")
                   .when(col("temperature_stddev") > 2, "Medium")
                   .otherwise("Low"))
    
    # Write aggregated results
    query_iot = iot_windowed.writeStream \
        .outputMode("append") \
        .format("parquet") \
        .option("path", s3_output_path + "/iot-analytics/") \
        .option("checkpointLocation", "/tmp/checkpoint/iot") \
        .partitionBy("window") \
        .start()
    
    return query_iot

def process_user_activity(spark, s3_input_path, s3_output_path):
    """
    Process user activity data for behavioral analytics
    """
    print("Processing user activity data...")
    
    # Read user activity stream
    activity_df = spark.readStream \
        .format("json") \
        .option("path", s3_input_path + "/user-activity/") \
        .load()
    
    # Sessionization and user journey analysis
    windowSpec = Window.partitionBy("user_id", "session_id").orderBy("timestamp")
    
    activity_enriched = activity_df \
        .withColumn("processing_time", current_timestamp()) \
        .withColumn("event_sequence", row_number().over(windowSpec)) \
        .withColumn("time_since_last_event", 
                   col("timestamp").cast("long") - 
                   lag("timestamp").over(windowSpec).cast("long")) \
        .withColumn("session_duration_so_far",
                   col("timestamp").cast("long") - 
                   first("timestamp").over(windowSpec).cast("long")) \
        .withColumn("is_bounce", 
                   when(col("event_sequence") == 1, True).otherwise(False)) \
        .withColumn("page_category",
                   when(col("page_url").contains("product"), "Product")
                   .when(col("page_url").contains("cart"), "Shopping")
                   .when(col("page_url").contains("checkout"), "Checkout")
                   .when(col("page_url").contains("search"), "Search")
                   .otherwise("Other"))
    
    # Real-time user behavior aggregations
    user_behavior = activity_enriched \
        .withWatermark("timestamp", "30 minutes") \
        .groupBy(
            window(col("timestamp"), "10 minutes", "2 minutes"),
            col("user_id"),
            col("page_category")
        ) \
        .agg(
            count("*").alias("page_views"),
            sum("duration_seconds").alias("total_time_spent"),
            avg("duration_seconds").alias("avg_time_per_page"),
            countDistinct("page_url").alias("unique_pages_viewed"),
            max("event_sequence").alias("max_sequence"),
            first("device_info").alias("device_info"),
            first("location").alias("location")
        ) \
        .withColumn("engagement_score",
                   (col("total_time_spent") * 0.3 + 
                    col("unique_pages_viewed") * 0.4 + 
                    col("page_views") * 0.3)) \
        .withColumn("user_segment",
                   when(col("engagement_score") > 100, "Highly Engaged")
                   .when(col("engagement_score") > 50, "Moderately Engaged")
                   .when(col("engagement_score") > 20, "Low Engagement")
                   .otherwise("Casual Browser"))
    
    # Write user behavior analytics
    query_activity = user_behavior.writeStream \
        .outputMode("append") \
        .format("parquet") \
        .option("path", s3_output_path + "/user-behavior-analytics/") \
        .option("checkpointLocation", "/tmp/checkpoint/activity") \
        .partitionBy("window") \
        .start()
    
    return query_activity

def calculate_business_kpis(spark, s3_input_path, s3_output_path):
    """
    Calculate real-time business KPIs and alerts
    """
    print("Calculating business KPIs...")
    
    # Read processed transaction data
    transactions_df = spark.readStream \
        .format("parquet") \
        .option("path", s3_input_path + "/processed-transactions/") \
        .load()
    
    # Real-time KPI calculations
    kpis = transactions_df \
        .withWatermark("timestamp", "1 hour") \
        .groupBy(window(col("timestamp"), "15 minutes", "5 minutes")) \
        .agg(
            count("*").alias("total_transactions"),
            sum("amount").alias("total_revenue"),
            avg("amount").alias("avg_transaction_value"),
            countDistinct("customer_id").alias("unique_customers"),
            countDistinct("product_id").alias("unique_products_sold"),
            max("amount").alias("max_transaction"),
            min("amount").alias("min_transaction")
        ) \
        .withColumn("revenue_per_customer", col("total_revenue") / col("unique_customers")) \
        .withColumn("conversion_rate", col("total_transactions") / col("unique_customers")) \
        .withColumn("kpi_timestamp", current_timestamp()) \
        .withColumn("alert_status",
                   when(col("total_revenue") < 1000, "Revenue Alert")
                   .when(col("avg_transaction_value") < 50, "Low AOV Alert")
                   .otherwise("Normal"))
    
    # Write KPIs for dashboard consumption
    query_kpis = kpis.writeStream \
        .outputMode("append") \
        .format("json") \
        .option("path", s3_output_path + "/business-kpis/") \
        .option("checkpointLocation", "/tmp/checkpoint/kpis") \
        .start()
    
    return query_kpis

def main():
    """
    Main function to orchestrate real-time analytics processing
    """
    parser = argparse.ArgumentParser(description='Real-time Analytics Spark Job')
    parser.add_argument('--input-path', required=True, help='S3 input path')
    parser.add_argument('--output-path', required=True, help='S3 output path')
    parser.add_argument('--duration', type=int, default=300, help='Streaming duration in seconds')
    
    args = parser.parse_args()
    
    # Create Spark session
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        print(f"Starting real-time analytics processing...")
        print(f"Input path: {args.input_path}")
        print(f"Output path: {args.output_path}")
        
        # Start multiple streaming queries
        queries = []
        
        # Process IoT data
        query_iot = process_iot_data(spark, args.input_path, args.output_path)
        queries.append(query_iot)
        
        # Process user activity
        query_activity = process_user_activity(spark, args.input_path, args.output_path)
        queries.append(query_activity)
        
        # Calculate business KPIs
        query_kpis = calculate_business_kpis(spark, args.input_path, args.output_path)
        queries.append(query_kpis)
        
        print(f"Started {len(queries)} streaming queries")
        
        # Wait for all queries to complete or timeout
        for i, query in enumerate(queries):
            print(f"Waiting for query {i+1} to complete...")
            if args.duration > 0:
                query.awaitTermination(args.duration)
            else:
                query.awaitTermination()
        
        print("All streaming queries completed successfully!")
        
    except Exception as e:
        print(f"Error in real-time analytics job: {str(e)}")
        raise e
    
    finally:
        spark.stop()

if __name__ == "__main__":
    main()