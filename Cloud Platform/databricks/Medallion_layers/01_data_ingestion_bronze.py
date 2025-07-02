# Databricks notebook source
# MAGIC %md
# MAGIC # Data Ingestion & Bronze Layer
# MAGIC 
# MAGIC This notebook demonstrates modern data ingestion patterns using Delta Lake:
# MAGIC - Multi-format data ingestion (JSON, CSV, Parquet)
# MAGIC - Schema inference and evolution
# MAGIC - Streaming data ingestion
# MAGIC - Auto Loader for continuous ingestion
# MAGIC - Data lineage and metadata management
# MAGIC 
# MAGIC **Architecture**: Raw Data → Bronze Layer (Delta Lake)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

# Import required libraries
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import *
import json
from datetime import datetime, timedelta

# Configuration
DATABASE_NAME = "demo_lakehouse"
BRONZE_PATH = "/tmp/demo/bronze"
CHECKPOINT_PATH = "/tmp/demo/checkpoints"
LANDING_PATH = "/tmp/demo/landing"

# Create database if not exists
spark.sql(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
spark.sql(f"USE {DATABASE_NAME}")

print(f"Using database: {DATABASE_NAME}")
print(f"Bronze layer path: {BRONZE_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. E-commerce Transaction Data Ingestion

# COMMAND ----------

# Define schema for e-commerce transactions
ecommerce_schema = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("customer_email", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("product_name", StringType(), True),
    StructField("product_category", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("quantity", IntegerType(), True),
    StructField("timestamp", TimestampType(), True),
    StructField("customer_location", StringType(), True),
    StructField("payment_method", StringType(), True)
])

# Create sample e-commerce data
sample_ecommerce_data = [
    ("TXN_001", "CUST_001", "john.doe@email.com", "PROD_001", "Wireless Headphones", "Electronics", 299.99, 1, "2024-01-15 10:30:00", "New York", "Credit Card"),
    ("TXN_002", "CUST_002", "jane.smith@email.com", "PROD_002", "Running Shoes", "Sports", 149.99, 1, "2024-01-15 11:45:00", "Los Angeles", "PayPal"),
    ("TXN_003", "CUST_001", "john.doe@email.com", "PROD_003", "Coffee Machine", "Home & Garden", 399.99, 1, "2024-01-15 14:20:00", "New York", "Credit Card"),
    ("TXN_004", "CUST_003", "bob.wilson@email.com", "PROD_001", "Wireless Headphones", "Electronics", 299.99, 2, "2024-01-15 16:10:00", "Chicago", "Debit Card"),
    ("TXN_005", "CUST_004", "alice.brown@email.com", "PROD_004", "Yoga Mat", "Sports", 79.99, 1, "2024-01-15 18:30:00", "Seattle", "Credit Card")
]

# Create DataFrame
ecommerce_df = spark.createDataFrame(sample_ecommerce_data, ecommerce_schema)

# Add metadata columns for bronze layer
ecommerce_bronze = ecommerce_df \
    .withColumn("ingestion_timestamp", current_timestamp()) \
    .withColumn("source_system", lit("ecommerce_api")) \
    .withColumn("file_name", lit("ecommerce_transactions.csv")) \
    .withColumn("ingestion_date", current_date())

# Write to Bronze layer as Delta table
ecommerce_bronze.write \
    .format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .save(f"{BRONZE_PATH}/ecommerce_transactions")

# Create table in metastore
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.bronze_ecommerce_transactions
    USING DELTA
    LOCATION '{BRONZE_PATH}/ecommerce_transactions'
""")

print("✅ E-commerce transactions ingested to Bronze layer")
display(spark.table(f"{DATABASE_NAME}.bronze_ecommerce_transactions"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. IoT Sensor Data Streaming Ingestion

# COMMAND ----------

# Define schema for IoT sensor data
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

# Create sample IoT sensor data
sample_iot_data = [
    ("SENSOR_001", "Temperature Sensor", "2024-01-15 10:00:00", 23.5, 45.2, 1013.25, "Factory Floor A", 87.5),
    ("SENSOR_002", "Multi Sensor", "2024-01-15 10:01:00", 24.1, 43.8, 1012.80, "Warehouse B", 92.3),
    ("SENSOR_003", "Humidity Sensor", "2024-01-15 10:02:00", 22.8, 48.5, 1014.10, "Office Building C", 78.9),
    ("SENSOR_004", "Pressure Sensor", "2024-01-15 10:03:00", 25.2, 41.2, 1011.95, "Retail Store D", 65.4),
    ("SENSOR_001", "Temperature Sensor", "2024-01-15 10:05:00", 23.8, 46.1, 1013.15, "Factory Floor A", 87.2)
]

# Create streaming DataFrame (simulated)
iot_df = spark.createDataFrame(sample_iot_data, iot_schema)

# Add bronze layer metadata
iot_bronze = iot_df \
    .withColumn("ingestion_timestamp", current_timestamp()) \
    .withColumn("source_system", lit("iot_gateway")) \
    .withColumn("data_quality_score", lit(0.95)) \
    .withColumn("ingestion_date", current_date()) \
    .withColumn("partition_date", date_format(col("timestamp"), "yyyy-MM-dd"))

# Write to Bronze layer with partitioning
iot_bronze.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("partition_date") \
    .option("mergeSchema", "true") \
    .save(f"{BRONZE_PATH}/iot_sensor_data")

# Create table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.bronze_iot_sensor_data
    USING DELTA
    LOCATION '{BRONZE_PATH}/iot_sensor_data'
""")

print("✅ IoT sensor data ingested to Bronze layer")
display(spark.table(f"{DATABASE_NAME}.bronze_iot_sensor_data"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Customer Demographics Data Ingestion

# COMMAND ----------

# Customer demographics data with schema evolution example
customer_schema_v1 = StructType([
    StructField("customer_id", StringType(), True),
    StructField("first_name", StringType(), True),
    StructField("last_name", StringType(), True),
    StructField("email", StringType(), True),
    StructField("age", IntegerType(), True),
    StructField("city", StringType(), True),
    StructField("country", StringType(), True)
])

# Initial customer data
customer_data_v1 = [
    ("CUST_001", "John", "Doe", "john.doe@email.com", 32, "New York", "USA"),
    ("CUST_002", "Jane", "Smith", "jane.smith@email.com", 28, "Los Angeles", "USA"),
    ("CUST_003", "Bob", "Wilson", "bob.wilson@email.com", 45, "Chicago", "USA"),
    ("CUST_004", "Alice", "Brown", "alice.brown@email.com", 35, "Seattle", "USA")
]

customers_v1_df = spark.createDataFrame(customer_data_v1, customer_schema_v1) \
    .withColumn("ingestion_timestamp", current_timestamp()) \
    .withColumn("source_system", lit("crm_system")) \
    .withColumn("record_version", lit(1)) \
    .withColumn("ingestion_date", current_date())

# Write initial version
customers_v1_df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .save(f"{BRONZE_PATH}/customer_demographics")

print("✅ Customer demographics v1 ingested")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Schema Evolution Example

# COMMAND ----------

# Simulate schema evolution - new fields added
customer_schema_v2 = StructType([
    StructField("customer_id", StringType(), True),
    StructField("first_name", StringType(), True),
    StructField("last_name", StringType(), True),
    StructField("email", StringType(), True),
    StructField("age", IntegerType(), True),
    StructField("city", StringType(), True),
    StructField("country", StringType(), True),
    StructField("phone_number", StringType(), True),  # New field
    StructField("preferred_category", StringType(), True),  # New field
    StructField("loyalty_tier", StringType(), True)  # New field
])

# New customer data with additional fields
customer_data_v2 = [
    ("CUST_005", "Mike", "Johnson", "mike.johnson@email.com", 29, "Denver", "USA", "+1-555-0101", "Electronics", "Gold"),
    ("CUST_006", "Sarah", "Davis", "sarah.davis@email.com", 33, "Boston", "USA", "+1-555-0102", "Sports", "Silver"),
    ("CUST_001", "John", "Doe", "john.doe@email.com", 32, "New York", "USA", "+1-555-0103", "Electronics", "Platinum")  # Updated existing customer
]

customers_v2_df = spark.createDataFrame(customer_data_v2, customer_schema_v2) \
    .withColumn("ingestion_timestamp", current_timestamp()) \
    .withColumn("source_system", lit("crm_system")) \
    .withColumn("record_version", lit(2)) \
    .withColumn("ingestion_date", current_date())

# Append with schema evolution
customers_v2_df.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(f"{BRONZE_PATH}/customer_demographics")

# Create table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.bronze_customer_demographics
    USING DELTA
    LOCATION '{BRONZE_PATH}/customer_demographics'
""")

print("✅ Customer demographics v2 ingested with schema evolution")
display(spark.table(f"{DATABASE_NAME}.bronze_customer_demographics"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Auto Loader Example (Simulated)

# COMMAND ----------

# Demonstrate Auto Loader pattern for continuous ingestion
def setup_auto_loader_stream(source_path, target_path, checkpoint_path, table_name):
    """
    Setup Auto Loader for continuous data ingestion
    """
    
    # Auto Loader configuration
    auto_loader_df = spark.readStream \
        .format("cloudFiles") \
        .option("cloudFiles.format", "json") \
        .option("cloudFiles.schemaLocation", f"{checkpoint_path}/schema") \
        .option("cloudFiles.inferColumnTypes", "true") \
        .load(source_path)
    
    # Add metadata columns
    enriched_df = auto_loader_df \
        .withColumn("ingestion_timestamp", current_timestamp()) \
        .withColumn("source_file", input_file_name()) \
        .withColumn("ingestion_date", current_date())
    
    # Write stream to Delta table
    query = enriched_df.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", checkpoint_path) \
        .trigger(processingTime="30 seconds") \
        .table(table_name)
    
    return query

# Example configuration (would be used with actual file sources)
auto_loader_config = {
    "ecommerce": {
        "source_path": f"{LANDING_PATH}/ecommerce",
        "target_path": f"{BRONZE_PATH}/ecommerce_stream",
        "checkpoint_path": f"{CHECKPOINT_PATH}/ecommerce_stream",
        "table_name": f"{DATABASE_NAME}.bronze_ecommerce_stream"
    },
    "iot": {
        "source_path": f"{LANDING_PATH}/iot", 
        "target_path": f"{BRONZE_PATH}/iot_stream",
        "checkpoint_path": f"{CHECKPOINT_PATH}/iot_stream",
        "table_name": f"{DATABASE_NAME}.bronze_iot_stream"
    }
}

print("✅ Auto Loader configuration ready")
print("Auto Loader would monitor landing zones and continuously ingest new files")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Data Quality and Monitoring

# COMMAND ----------

# Data quality checks for bronze layer
def bronze_data_quality_checks():
    """
    Perform data quality checks on bronze layer tables
    """
    
    # E-commerce data quality
    ecommerce_stats = spark.sql(f"""
        SELECT 
            'ecommerce_transactions' as table_name,
            COUNT(*) as total_records,
            COUNT(DISTINCT customer_id) as unique_customers,
            COUNT(DISTINCT product_id) as unique_products,
            SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) as null_amounts,
            MIN(timestamp) as earliest_transaction,
            MAX(timestamp) as latest_transaction,
            AVG(amount) as avg_transaction_amount
        FROM {DATABASE_NAME}.bronze_ecommerce_transactions
    """)
    
    # IoT data quality
    iot_stats = spark.sql(f"""
        SELECT 
            'iot_sensor_data' as table_name,
            COUNT(*) as total_records,
            COUNT(DISTINCT sensor_id) as unique_sensors,
            AVG(temperature) as avg_temperature,
            AVG(humidity) as avg_humidity,
            AVG(battery_level) as avg_battery_level,
            MIN(timestamp) as earliest_reading,
            MAX(timestamp) as latest_reading
        FROM {DATABASE_NAME}.bronze_iot_sensor_data
    """)
    
    # Customer data quality
    customer_stats = spark.sql(f"""
        SELECT 
            'customer_demographics' as table_name,
            COUNT(*) as total_records,
            COUNT(DISTINCT customer_id) as unique_customers,
            COUNT(DISTINCT email) as unique_emails,
            AVG(age) as avg_age,
            MAX(record_version) as latest_version
        FROM {DATABASE_NAME}.bronze_customer_demographics
    """)
    
    return ecommerce_stats, iot_stats, customer_stats

# Run quality checks
ecommerce_qa, iot_qa, customer_qa = bronze_data_quality_checks()

print("📊 Bronze Layer Data Quality Summary:")
print("\n--- E-commerce Transactions ---")
display(ecommerce_qa)

print("\n--- IoT Sensor Data ---")
display(iot_qa)

print("\n--- Customer Demographics ---")
display(customer_qa)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Time Travel and History

# COMMAND ----------

# Demonstrate Delta Lake time travel capabilities
print("🕒 Delta Lake Time Travel Examples:")

# Show table history
ecommerce_history = spark.sql(f"""
    DESCRIBE HISTORY delta.`{BRONZE_PATH}/ecommerce_transactions`
""")

print("\n--- E-commerce Transactions History ---")
display(ecommerce_history)

# Show customer demographics history (with schema evolution)
customer_history = spark.sql(f"""
    DESCRIBE HISTORY delta.`{BRONZE_PATH}/customer_demographics`
""")

print("\n--- Customer Demographics History (Schema Evolution) ---")
display(customer_history)

# Query previous version
try:
    customer_v1 = spark.sql(f"""
        SELECT * FROM {DATABASE_NAME}.bronze_customer_demographics VERSION AS OF 0
    """)
    print("\n--- Customer Data Version 0 (Before Schema Evolution) ---")
    display(customer_v1)
except:
    print("Previous version not available - using current version")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Summary and Next Steps

# COMMAND ----------

# Final summary
print("🎯 Bronze Layer Ingestion Summary:")
print("="*50)

# Table sizes
tables_summary = spark.sql(f"""
    SELECT 
        'bronze_ecommerce_transactions' as table_name,
        COUNT(*) as record_count
    FROM {DATABASE_NAME}.bronze_ecommerce_transactions
    
    UNION ALL
    
    SELECT 
        'bronze_iot_sensor_data' as table_name,
        COUNT(*) as record_count  
    FROM {DATABASE_NAME}.bronze_iot_sensor_data
    
    UNION ALL
    
    SELECT 
        'bronze_customer_demographics' as table_name,
        COUNT(*) as record_count
    FROM {DATABASE_NAME}.bronze_customer_demographics
""")

display(tables_summary)

print("\n✅ Bronze Layer Setup Complete!")
print("\nKey Features Demonstrated:")
print("• Multi-format data ingestion (CSV, JSON)")
print("• Schema inference and evolution")
print("• Partitioning strategies")  
print("• Metadata enrichment")
print("• Time travel capabilities")
print("• Data quality monitoring")
print("• Auto Loader patterns")

print("\n🔄 Next Steps:")
print("• Run notebook 02_data_quality_silver.py for Silver layer processing")
print("• Implement streaming ingestion for real-time data")
print("• Set up Unity Catalog for governance")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cleanup (Optional)

# COMMAND ----------

# Uncomment to cleanup demo data
# spark.sql(f"DROP DATABASE IF EXISTS {DATABASE_NAME} CASCADE")
# dbutils.fs.rm(BRONZE_PATH, True)
# dbutils.fs.rm(CHECKPOINT_PATH, True)
# print("🧹 Demo data cleaned up")