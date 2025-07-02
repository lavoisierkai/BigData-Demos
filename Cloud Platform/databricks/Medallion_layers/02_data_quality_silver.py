# Databricks notebook source
# MAGIC %md
# MAGIC # Data Quality & Silver Layer
# MAGIC 
# MAGIC This notebook demonstrates data quality and transformation patterns for the Silver layer:
# MAGIC - Data validation and quality checks
# MAGIC - Data cleaning and standardization
# MAGIC - Change Data Capture (CDC) processing
# MAGIC - Expectations and constraint enforcement
# MAGIC - Deduplication and merge operations
# MAGIC 
# MAGIC **Architecture**: Bronze Layer → Silver Layer (Clean & Validated Data)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import *
from pyspark.sql.window import Window
import re
from datetime import datetime, timedelta

# Configuration
DATABASE_NAME = "demo_lakehouse"
BRONZE_PATH = "/tmp/demo/bronze"
SILVER_PATH = "/tmp/demo/silver"
CHECKPOINT_PATH = "/tmp/demo/checkpoints/silver"

# Use existing database
spark.sql(f"USE {DATABASE_NAME}")

print(f"Processing Bronze → Silver layer transformation")
print(f"Silver layer path: {SILVER_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. E-commerce Data Quality & Cleaning

# COMMAND ----------

# Load bronze e-commerce data
bronze_ecommerce = spark.table(f"{DATABASE_NAME}.bronze_ecommerce_transactions")

print("📊 Bronze E-commerce Data Quality Assessment:")
bronze_ecommerce.select(
    count("*").alias("total_records"),
    count("transaction_id").alias("non_null_txn_id"),
    count("customer_id").alias("non_null_customer_id"),
    count("amount").alias("non_null_amount"),
    countDistinct("transaction_id").alias("unique_transactions"),
    min("amount").alias("min_amount"),
    max("amount").alias("max_amount"),
    avg("amount").alias("avg_amount")
).show()

# Data cleaning and validation rules
def clean_ecommerce_data(df):
    """
    Apply comprehensive data cleaning and validation
    """
    
    # 1. Remove duplicates based on transaction_id
    df_dedup = df.dropDuplicates(["transaction_id"])
    
    # 2. Data validation and filtering
    df_validated = df_dedup.filter(
        # Valid transaction ID
        (col("transaction_id").isNotNull()) &
        (length(col("transaction_id")) > 0) &
        
        # Valid customer data
        (col("customer_id").isNotNull()) &
        (col("customer_email").isNotNull()) &
        (col("customer_email").rlike("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")) &
        
        # Valid financial data
        (col("amount") > 0) &
        (col("amount") < 10000) &  # Reasonable upper limit
        (col("quantity") > 0) &
        (col("quantity") <= 100) &  # Reasonable quantity limit
        
        # Valid product data
        (col("product_id").isNotNull()) &
        (col("product_name").isNotNull()) &
        (length(col("product_name")) > 0)
    )
    
    # 3. Data standardization and enrichment
    df_clean = df_validated \
        .withColumn("customer_email_clean", lower(trim(col("customer_email")))) \
        .withColumn("product_name_clean", 
                   regexp_replace(trim(col("product_name")), "[^a-zA-Z0-9 .-]", "")) \
        .withColumn("customer_location_clean", 
                   initcap(trim(col("customer_location")))) \
        .withColumn("transaction_date", to_date(col("timestamp"))) \
        .withColumn("transaction_hour", hour(col("timestamp"))) \
        .withColumn("transaction_day_of_week", dayofweek(col("timestamp"))) \
        .withColumn("transaction_month", month(col("timestamp"))) \
        .withColumn("transaction_year", year(col("timestamp"))) \
        .withColumn("is_weekend", 
                   when(dayofweek(col("timestamp")).isin([1, 7]), True).otherwise(False)) \
        .withColumn("total_value", col("amount") * col("quantity")) \
        .withColumn("product_category_standardized",
                   when(upper(col("product_category")) == "ELECTRONICS", "Electronics")
                   .when(upper(col("product_category")) == "SPORTS", "Sports")
                   .when(upper(col("product_category")).contains("HOME"), "Home & Garden")
                   .otherwise(col("product_category"))) \
        .withColumn("customer_value_tier",
                   when(col("amount") >= 500, "Premium")
                   .when(col("amount") >= 200, "High")
                   .when(col("amount") >= 100, "Medium")
                   .otherwise("Basic")) \
        .withColumn("payment_method_category",
                   when(col("payment_method").isin(["Credit Card", "Debit Card"]), "Card")
                   .when(col("payment_method") == "PayPal", "Digital Wallet")
                   .otherwise("Other"))
    
    # 4. Add data quality scores
    df_clean = df_clean \
        .withColumn("data_quality_score",
                   when((col("customer_email_clean").isNotNull()) &
                        (col("product_name_clean").isNotNull()) &
                        (col("amount") > 0) &
                        (col("customer_location_clean").isNotNull()), 1.0)
                   .otherwise(0.8)) \
        .withColumn("processed_timestamp", current_timestamp()) \
        .withColumn("silver_layer_version", lit("v1.0"))
    
    return df_clean

# Apply cleaning transformations
silver_ecommerce = clean_ecommerce_data(bronze_ecommerce)

print("🧹 Data Cleaning Results:")
silver_ecommerce.select(
    count("*").alias("cleaned_records"),
    avg("data_quality_score").alias("avg_quality_score"),
    countDistinct("customer_id").alias("unique_customers"),
    sum("total_value").alias("total_transaction_value")
).show()

# Write to Silver layer
silver_ecommerce.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("transaction_year", "transaction_month") \
    .option("mergeSchema", "true") \
    .save(f"{SILVER_PATH}/ecommerce_transactions")

# Create table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.silver_ecommerce_transactions
    USING DELTA
    LOCATION '{SILVER_PATH}/ecommerce_transactions'
""")

print("✅ Silver E-commerce table created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. IoT Sensor Data Quality & Anomaly Detection

# COMMAND ----------

# Load bronze IoT data
bronze_iot = spark.table(f"{DATABASE_NAME}.bronze_iot_sensor_data")

def clean_iot_data(df):
    """
    Clean and validate IoT sensor data with anomaly detection
    """
    
    # Define valid ranges for sensor readings
    valid_ranges = {
        "temperature": (-40, 60),    # Celsius
        "humidity": (0, 100),        # Percentage
        "pressure": (950, 1050),     # hPa
        "battery_level": (0, 100)    # Percentage
    }
    
    # 1. Filter invalid readings
    df_validated = df.filter(
        (col("sensor_id").isNotNull()) &
        (col("timestamp").isNotNull()) &
        (col("temperature").between(*valid_ranges["temperature"])) &
        (col("humidity").between(*valid_ranges["humidity"])) &
        (col("pressure").between(*valid_ranges["pressure"])) &
        (col("battery_level").between(*valid_ranges["battery_level"]))
    )
    
    # 2. Detect anomalies using statistical methods
    # Calculate rolling statistics for anomaly detection
    window_spec = Window.partitionBy("sensor_id").orderBy("timestamp").rowsBetween(-10, 0)
    
    df_with_stats = df_validated \
        .withColumn("temp_rolling_avg", avg("temperature").over(window_spec)) \
        .withColumn("temp_rolling_std", stddev("temperature").over(window_spec)) \
        .withColumn("humidity_rolling_avg", avg("humidity").over(window_spec)) \
        .withColumn("pressure_rolling_avg", avg("pressure").over(window_spec))
    
    # 3. Flag anomalies
    df_anomaly_flagged = df_with_stats \
        .withColumn("temp_anomaly", 
                   when(abs(col("temperature") - col("temp_rolling_avg")) > 
                        2 * coalesce(col("temp_rolling_std"), lit(1)), True)
                   .otherwise(False)) \
        .withColumn("humidity_anomaly",
                   when(abs(col("humidity") - col("humidity_rolling_avg")) > 10, True)
                   .otherwise(False)) \
        .withColumn("pressure_anomaly",
                   when(abs(col("pressure") - col("pressure_rolling_avg")) > 5, True)
                   .otherwise(False)) \
        .withColumn("battery_critical",
                   when(col("battery_level") < 20, True).otherwise(False))
    
    # 4. Overall data quality assessment
    df_quality_scored = df_anomaly_flagged \
        .withColumn("anomaly_count",
                   (col("temp_anomaly").cast("int") + 
                    col("humidity_anomaly").cast("int") + 
                    col("pressure_anomaly").cast("int"))) \
        .withColumn("data_quality_score",
                   when(col("anomaly_count") == 0, 1.0)
                   .when(col("anomaly_count") == 1, 0.8)
                   .when(col("anomaly_count") == 2, 0.6)
                   .otherwise(0.4)) \
        .withColumn("sensor_status",
                   when(col("battery_critical"), "BATTERY_CRITICAL")
                   .when(col("anomaly_count") >= 2, "MULTIPLE_ANOMALIES")
                   .when(col("anomaly_count") == 1, "MINOR_ANOMALY")
                   .otherwise("NORMAL"))
    
    # 5. Add derived metrics
    df_enriched = df_quality_scored \
        .withColumn("heat_index",
                   when((col("temperature") >= 27) & (col("humidity") >= 40),
                        -42.379 + 2.04901523 * col("temperature") + 
                        10.14333127 * col("humidity") - 
                        0.22475541 * col("temperature") * col("humidity"))
                   .otherwise(col("temperature"))) \
        .withColumn("comfort_level",
                   when((col("temperature").between(20, 26)) & 
                        (col("humidity").between(40, 60)), "Comfortable")
                   .when((col("temperature") < 18) | (col("temperature") > 28), "Uncomfortable")
                   .when((col("humidity") < 30) | (col("humidity") > 70), "Uncomfortable")
                   .otherwise("Acceptable")) \
        .withColumn("reading_date", to_date(col("timestamp"))) \
        .withColumn("reading_hour", hour(col("timestamp"))) \
        .withColumn("processed_timestamp", current_timestamp()) \
        .withColumn("silver_layer_version", lit("v1.0"))
    
    return df_enriched

# Apply IoT data cleaning
silver_iot = clean_iot_data(bronze_iot)

print("🌡️ IoT Data Quality Results:")
silver_iot.groupBy("sensor_status") \
    .agg(count("*").alias("count"),
         avg("data_quality_score").alias("avg_quality_score")) \
    .show()

# Write to Silver layer
silver_iot.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("reading_date") \
    .option("mergeSchema", "true") \
    .save(f"{SILVER_PATH}/iot_sensor_data")

# Create table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.silver_iot_sensor_data
    USING DELTA
    LOCATION '{SILVER_PATH}/iot_sensor_data'
""")

print("✅ Silver IoT sensor table created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Customer Data Deduplication & SCD Type 2

# COMMAND ----------

# Load bronze customer data
bronze_customers = spark.table(f"{DATABASE_NAME}.bronze_customer_demographics")

def process_customer_scd(df):
    """
    Implement Slowly Changing Dimension Type 2 for customer data
    """
    
    # 1. Data cleaning and standardization
    df_clean = df \
        .withColumn("email_clean", lower(trim(col("email")))) \
        .withColumn("first_name_clean", initcap(trim(col("first_name")))) \
        .withColumn("last_name_clean", initcap(trim(col("last_name")))) \
        .withColumn("city_clean", initcap(trim(col("city")))) \
        .withColumn("country_clean", upper(trim(col("country")))) \
        .withColumn("phone_clean", 
                   regexp_replace(coalesce(col("phone_number"), lit("")), "[^0-9+\\-]", ""))
    
    # 2. Create customer dimension with SCD Type 2 structure
    # Get the latest record for each customer
    window_spec = Window.partitionBy("customer_id").orderBy(desc("ingestion_timestamp"))
    
    df_with_rank = df_clean.withColumn("rank", row_number().over(window_spec))
    
    # Get current records (latest version)
    current_records = df_with_rank.filter(col("rank") == 1)
    
    # 3. Add SCD Type 2 columns
    df_scd = current_records \
        .withColumn("effective_start_date", col("ingestion_timestamp")) \
        .withColumn("effective_end_date", lit(None).cast(TimestampType())) \
        .withColumn("is_current", lit(True)) \
        .withColumn("customer_hash", 
                   sha2(concat_ws("|", 
                                col("first_name_clean"),
                                col("last_name_clean"), 
                                col("email_clean"),
                                col("city_clean"),
                                col("country_clean"),
                                coalesce(col("phone_clean"), lit("")),
                                coalesce(col("preferred_category"), lit("")),
                                coalesce(col("loyalty_tier"), lit(""))), 256))
    
    # 4. Add customer analytics
    df_analytics = df_scd \
        .withColumn("age_group",
                   when(col("age") < 25, "18-24")
                   .when(col("age") < 35, "25-34")
                   .when(col("age") < 45, "35-44")
                   .when(col("age") < 55, "45-54")
                   .when(col("age") < 65, "55-64")
                   .otherwise("65+")) \
        .withColumn("customer_tier",
                   when(col("loyalty_tier") == "Platinum", 1)
                   .when(col("loyalty_tier") == "Gold", 2)
                   .when(col("loyalty_tier") == "Silver", 3)
                   .otherwise(4)) \
        .withColumn("has_phone", col("phone_clean").isNotNull() & (length(col("phone_clean")) > 0)) \
        .withColumn("data_completeness_score",
                   (when(col("first_name_clean").isNotNull(), 0.2).otherwise(0) +
                    when(col("last_name_clean").isNotNull(), 0.2).otherwise(0) +
                    when(col("email_clean").isNotNull(), 0.3).otherwise(0) +
                    when(col("age").isNotNull(), 0.1).otherwise(0) +
                    when(col("city_clean").isNotNull(), 0.1).otherwise(0) +
                    when(col("has_phone"), 0.1).otherwise(0))) \
        .withColumn("processed_timestamp", current_timestamp()) \
        .withColumn("silver_layer_version", lit("v1.0"))
    
    return df_analytics

# Process customer SCD
silver_customers = process_customer_scd(bronze_customers)

print("👥 Customer Data Processing Results:")
silver_customers.groupBy("age_group", "customer_tier") \
    .agg(count("*").alias("count"),
         avg("data_completeness_score").alias("avg_completeness")) \
    .orderBy("customer_tier", "age_group") \
    .show()

# Write to Silver layer
silver_customers.write \
    .format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .save(f"{SILVER_PATH}/customer_demographics")

# Create table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.silver_customer_demographics
    USING DELTA  
    LOCATION '{SILVER_PATH}/customer_demographics'
""")

print("✅ Silver customer demographics table created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Data Quality Constraints & Expectations

# COMMAND ----------

# Add table constraints for data quality enforcement
def add_data_quality_constraints():
    """
    Add Delta Lake constraints for data quality enforcement
    """
    
    # E-commerce transactions constraints
    try:
        spark.sql(f"""
            ALTER TABLE {DATABASE_NAME}.silver_ecommerce_transactions 
            ADD CONSTRAINT valid_amount CHECK (amount > 0 AND amount < 10000)
        """)
        print("✅ Amount constraint added to e-commerce table")
    except:
        print("ℹ️ Amount constraint already exists")
    
    try:
        spark.sql(f"""
            ALTER TABLE {DATABASE_NAME}.silver_ecommerce_transactions 
            ADD CONSTRAINT valid_quantity CHECK (quantity > 0 AND quantity <= 100)
        """)
        print("✅ Quantity constraint added to e-commerce table")
    except:
        print("ℹ️ Quantity constraint already exists")
    
    # IoT sensor constraints
    try:
        spark.sql(f"""
            ALTER TABLE {DATABASE_NAME}.silver_iot_sensor_data 
            ADD CONSTRAINT valid_temperature CHECK (temperature >= -40 AND temperature <= 60)
        """)
        print("✅ Temperature constraint added to IoT table")
    except:
        print("ℹ️ Temperature constraint already exists")
    
    try:
        spark.sql(f"""
            ALTER TABLE {DATABASE_NAME}.silver_iot_sensor_data 
            ADD CONSTRAINT valid_humidity CHECK (humidity >= 0 AND humidity <= 100)
        """)
        print("✅ Humidity constraint added to IoT table")
    except:
        print("ℹ️ Humidity constraint already exists")

add_data_quality_constraints()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Change Data Capture (CDC) Processing

# COMMAND ----------

def simulate_cdc_processing():
    """
    Simulate CDC processing for incremental updates
    """
    
    # Simulate new e-commerce transactions (CDC inserts)
    new_transactions = [
        ("TXN_006", "CUST_002", "jane.smith@email.com", "PROD_005", "Bluetooth Speaker", "Electronics", 199.99, 1, "2024-01-16 09:15:00", "Los Angeles", "Credit Card"),
        ("TXN_007", "CUST_005", "mike.johnson@email.com", "PROD_006", "Tennis Racket", "Sports", 249.99, 1, "2024-01-16 11:30:00", "Denver", "PayPal"),
        ("TXN_008", "CUST_001", "john.doe@email.com", "PROD_007", "Smart Thermostat", "Electronics", 299.99, 1, "2024-01-16 14:45:00", "New York", "Credit Card")
    ]
    
    # Create schema
    schema = StructType([
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
    
    # Create CDC DataFrame
    cdc_df = spark.createDataFrame([
        (txn[0], txn[1], txn[2], txn[3], txn[4], txn[5], txn[6], txn[7], 
         datetime.strptime(txn[8], "%Y-%m-%d %H:%M:%S"), txn[9], txn[10])
        for txn in new_transactions
    ], schema)
    
    # Add metadata
    cdc_df_enriched = cdc_df \
        .withColumn("ingestion_timestamp", current_timestamp()) \
        .withColumn("source_system", lit("ecommerce_api")) \
        .withColumn("cdc_operation", lit("INSERT")) \
        .withColumn("ingestion_date", current_date())
    
    # Clean the CDC data using the same function
    cdc_clean = clean_ecommerce_data(cdc_df_enriched)
    
    # Merge into Silver table using Delta Lake MERGE
    silver_table = DeltaTable.forPath(spark, f"{SILVER_PATH}/ecommerce_transactions")
    
    silver_table.alias("target").merge(
        cdc_clean.alias("source"),
        "target.transaction_id = source.transaction_id"
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
    
    print("🔄 CDC processing completed - new transactions merged")
    
    # Show merge statistics
    print("Updated Silver table record count:")
    spark.table(f"{DATABASE_NAME}.silver_ecommerce_transactions").count()

simulate_cdc_processing()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Data Quality Dashboard & Metrics

# COMMAND ----------

def generate_data_quality_report():
    """
    Generate comprehensive data quality report
    """
    
    print("📊 Silver Layer Data Quality Report")
    print("=" * 50)
    
    # E-commerce data quality metrics
    ecommerce_metrics = spark.sql(f"""
        SELECT 
            'E-commerce Transactions' as dataset,
            COUNT(*) as total_records,
            AVG(data_quality_score) as avg_quality_score,
            SUM(CASE WHEN data_quality_score >= 0.9 THEN 1 ELSE 0 END) as high_quality_records,
            SUM(CASE WHEN data_quality_score < 0.8 THEN 1 ELSE 0 END) as low_quality_records,
            COUNT(DISTINCT customer_id) as unique_customers,
            COUNT(DISTINCT product_id) as unique_products,
            SUM(total_value) as total_transaction_value,
            MIN(transaction_date) as earliest_date,
            MAX(transaction_date) as latest_date
        FROM {DATABASE_NAME}.silver_ecommerce_transactions
    """)
    
    # IoT data quality metrics  
    iot_metrics = spark.sql(f"""
        SELECT 
            'IoT Sensor Data' as dataset,
            COUNT(*) as total_records,
            AVG(data_quality_score) as avg_quality_score,
            SUM(CASE WHEN sensor_status = 'NORMAL' THEN 1 ELSE 0 END) as normal_readings,
            SUM(CASE WHEN sensor_status LIKE '%ANOMALY%' THEN 1 ELSE 0 END) as anomaly_readings,
            SUM(CASE WHEN battery_critical THEN 1 ELSE 0 END) as critical_battery_readings,
            COUNT(DISTINCT sensor_id) as unique_sensors,
            AVG(temperature) as avg_temperature,
            AVG(humidity) as avg_humidity
        FROM {DATABASE_NAME}.silver_iot_sensor_data
    """)
    
    # Customer data quality metrics
    customer_metrics = spark.sql(f"""
        SELECT 
            'Customer Demographics' as dataset,
            COUNT(*) as total_records,
            AVG(data_completeness_score) as avg_completeness_score,
            COUNT(DISTINCT customer_id) as unique_customers,
            SUM(CASE WHEN has_phone THEN 1 ELSE 0 END) as customers_with_phone,
            AVG(age) as avg_age,
            COUNT(DISTINCT loyalty_tier) as loyalty_tiers
        FROM {DATABASE_NAME}.silver_customer_demographics
    """)
    
    print("\n--- E-commerce Transactions Quality ---")
    display(ecommerce_metrics)
    
    print("\n--- IoT Sensor Data Quality ---")
    display(iot_metrics)
    
    print("\n--- Customer Demographics Quality ---")
    display(customer_metrics)
    
    # Data freshness metrics
    freshness_metrics = spark.sql(f"""
        SELECT 
            'silver_ecommerce_transactions' as table_name,
            MAX(processed_timestamp) as last_processed,
            COUNT(*) as record_count
        FROM {DATABASE_NAME}.silver_ecommerce_transactions
        
        UNION ALL
        
        SELECT 
            'silver_iot_sensor_data' as table_name,
            MAX(processed_timestamp) as last_processed,
            COUNT(*) as record_count
        FROM {DATABASE_NAME}.silver_iot_sensor_data
        
        UNION ALL
        
        SELECT 
            'silver_customer_demographics' as table_name,
            MAX(processed_timestamp) as last_processed,
            COUNT(*) as record_count
        FROM {DATABASE_NAME}.silver_customer_demographics
    """)
    
    print("\n--- Data Freshness ---")
    display(freshness_metrics)

generate_data_quality_report()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Summary and Next Steps

# COMMAND ----------

print("🎯 Silver Layer Processing Summary:")
print("=" * 50)

# Final metrics
final_summary = spark.sql(f"""
    SELECT 
        'Total Silver Records' as metric,
        CAST(
            (SELECT COUNT(*) FROM {DATABASE_NAME}.silver_ecommerce_transactions) +
            (SELECT COUNT(*) FROM {DATABASE_NAME}.silver_iot_sensor_data) +
            (SELECT COUNT(*) FROM {DATABASE_NAME}.silver_customer_demographics)
        AS STRING) as value
    
    UNION ALL
    
    SELECT 
        'Average Data Quality Score' as metric,
        CAST(ROUND((
            (SELECT AVG(data_quality_score) FROM {DATABASE_NAME}.silver_ecommerce_transactions) +
            (SELECT AVG(data_quality_score) FROM {DATABASE_NAME}.silver_iot_sensor_data) +
            (SELECT AVG(data_completeness_score) FROM {DATABASE_NAME}.silver_customer_demographics)
        ) / 3, 3) AS STRING) as value
    
    UNION ALL
    
    SELECT 
        'Unique Customers' as metric,
        CAST((SELECT COUNT(DISTINCT customer_id) FROM {DATABASE_NAME}.silver_customer_demographics) AS STRING) as value
        
    UNION ALL
    
    SELECT 
        'Unique Sensors' as metric,  
        CAST((SELECT COUNT(DISTINCT sensor_id) FROM {DATABASE_NAME}.silver_iot_sensor_data) AS STRING) as value
""")

display(final_summary)

print("\n✅ Silver Layer Processing Complete!")
print("\nKey Features Demonstrated:")
print("• Comprehensive data validation and cleaning")
print("• Anomaly detection for IoT sensor data")
print("• Slowly Changing Dimensions (SCD Type 2)")
print("• Change Data Capture (CDC) processing")
print("• Data quality constraints and expectations")
print("• Data quality monitoring and reporting")
print("• Delta Lake MERGE operations")

print("\n🔄 Next Steps:")
print("• Run notebook 03_business_intelligence_gold.py for Gold layer aggregations")
print("• Implement real-time streaming quality checks")
print("• Set up automated data quality alerts")
print("• Configure data lineage tracking")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optional: View Table Details

# COMMAND ----------

# Show table details and constraints
for table in ["silver_ecommerce_transactions", "silver_iot_sensor_data", "silver_customer_demographics"]:
    print(f"\n--- {table.upper()} DETAILS ---")
    try:
        # Show table properties
        spark.sql(f"DESCRIBE DETAIL {DATABASE_NAME}.{table}").show(truncate=False)
        
        # Show constraints
        constraints = spark.sql(f"SHOW TBLPROPERTIES {DATABASE_NAME}.{table}").collect()
        constraint_list = [row for row in constraints if 'constraint' in row.key.lower()]
        if constraint_list:
            print(f"Constraints for {table}:")
            for constraint in constraint_list:
                print(f"  • {constraint.key}: {constraint.value}")
        
    except Exception as e:
        print(f"Could not show details for {table}: {e}")

print("\n📋 Silver layer tables ready for Gold layer processing!")