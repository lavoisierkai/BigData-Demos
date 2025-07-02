# Databricks Delta Live Tables Pipeline for Kafka Streaming
# ========================================================
#
# This DLT pipeline demonstrates real-time data processing from Kafka topics
# through the medallion architecture (Bronze → Silver → Gold) using Delta Live Tables.
#
# Key Features:
# - Multi-topic Kafka ingestion
# - Real-time data quality validation
# - Complex event processing
# - Automatic schema evolution
# - Built-in monitoring and alerting

import dlt
from pyspark.sql import functions as F, types as T
from pyspark.sql.window import Window
from delta.tables import DeltaTable

# Pipeline configuration
KAFKA_BOOTSTRAP_SERVERS = "your-kafka-cluster:9092"
CHECKPOINT_LOCATION = "/tmp/dlt_checkpoint"

# =====================================================
# BRONZE LAYER - Raw Data Ingestion from Kafka
# =====================================================

@dlt.table(
    comment="Raw user events from Kafka topic",
    table_properties={
        "quality": "bronze",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true"
    }
)
def user_events_bronze():
    """
    Ingest raw user events from Kafka topic with minimal transformation
    """
    return (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", "user_events")
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
        .select(
            F.col("key").cast("string").alias("event_key"),
            F.col("value").cast("string").alias("event_value"),
            F.col("topic").alias("kafka_topic"),
            F.col("partition").alias("kafka_partition"),
            F.col("offset").alias("kafka_offset"),
            F.col("timestamp").alias("kafka_timestamp"),
            F.current_timestamp().alias("ingestion_timestamp")
        )
    )

@dlt.table(
    comment="Raw transaction events from Kafka topic",
    table_properties={
        "quality": "bronze",
        "delta.autoOptimize.optimizeWrite": "true"
    }
)
def transactions_bronze():
    """
    Ingest financial transaction events from Kafka
    """
    return (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", "transactions")
        .option("startingOffsets", "latest")
        .load()
        .select(
            F.col("key").cast("string").alias("transaction_key"),
            F.col("value").cast("string").alias("transaction_value"),
            F.col("topic").alias("kafka_topic"),
            F.col("partition").alias("kafka_partition"),
            F.col("offset").alias("kafka_offset"),
            F.col("timestamp").alias("kafka_timestamp"),
            F.current_timestamp().alias("ingestion_timestamp")
        )
    )

@dlt.table(
    comment="Raw IoT sensor data from Kafka topic",
    table_properties={
        "quality": "bronze"
    }
)
def iot_sensors_bronze():
    """
    Ingest IoT sensor readings from multiple device types
    """
    return (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", "iot_sensors")
        .option("startingOffsets", "latest")
        .load()
        .select(
            F.col("key").cast("string").alias("sensor_key"),
            F.col("value").cast("string").alias("sensor_value"),
            F.col("topic").alias("kafka_topic"),
            F.col("partition").alias("kafka_partition"),
            F.col("offset").alias("kafka_offset"),
            F.col("timestamp").alias("kafka_timestamp"),
            F.current_timestamp().alias("ingestion_timestamp")
        )
    )

# =====================================================
# SILVER LAYER - Cleaned and Validated Data
# =====================================================

@dlt.table(
    comment="Cleaned and validated user events with parsed JSON",
    table_properties={
        "quality": "silver",
        "delta.autoOptimize.optimizeWrite": "true"
    }
)
@dlt.expect_or_drop("valid_user_id", "user_id IS NOT NULL")
@dlt.expect_or_drop("valid_timestamp", "event_timestamp IS NOT NULL")
@dlt.expect_or_drop("valid_event_type", "event_type IN ('page_view', 'click', 'purchase', 'signup', 'login')")
@dlt.expect("valid_session_duration", "session_duration >= 0")
def user_events_silver():
    """
    Parse JSON user events and apply data quality rules
    """
    return (
        dlt.read_stream("user_events_bronze")
        .select(
            F.get_json_object("event_value", "$.user_id").cast("string").alias("user_id"),
            F.get_json_object("event_value", "$.session_id").cast("string").alias("session_id"),
            F.get_json_object("event_value", "$.event_type").cast("string").alias("event_type"),
            F.get_json_object("event_value", "$.timestamp").cast("timestamp").alias("event_timestamp"),
            F.get_json_object("event_value", "$.page_url").cast("string").alias("page_url"),
            F.get_json_object("event_value", "$.referrer").cast("string").alias("referrer"),
            F.get_json_object("event_value", "$.user_agent").cast("string").alias("user_agent"),
            F.get_json_object("event_value", "$.ip_address").cast("string").alias("ip_address"),
            F.get_json_object("event_value", "$.session_duration").cast("integer").alias("session_duration"),
            F.get_json_object("event_value", "$.device_type").cast("string").alias("device_type"),
            "kafka_timestamp",
            "ingestion_timestamp"
        )
        .withColumn("processing_date", F.to_date("event_timestamp"))
        .withColumn("processing_hour", F.hour("event_timestamp"))
        .withColumn("is_mobile", F.when(F.col("device_type") == "mobile", True).otherwise(False))
        .withColumn("domain", F.regexp_extract("page_url", "https?://([^/]+)", 1))
        .withColumn("event_id", F.concat(F.col("user_id"), F.lit("_"), F.col("event_timestamp").cast("string")))
    )

@dlt.table(
    comment="Validated financial transactions with fraud scoring",
    table_properties={
        "quality": "silver",
        "delta.autoOptimize.optimizeWrite": "true"
    }
)
@dlt.expect_or_drop("valid_transaction_id", "transaction_id IS NOT NULL")
@dlt.expect_or_drop("valid_amount", "amount > 0 AND amount < 100000")
@dlt.expect_or_drop("valid_currency", "currency IN ('USD', 'EUR', 'GBP', 'JPY')")
@dlt.expect("valid_merchant", "merchant_id IS NOT NULL")
def transactions_silver():
    """
    Parse and validate transaction data with fraud detection
    """
    return (
        dlt.read_stream("transactions_bronze")
        .select(
            F.get_json_object("transaction_value", "$.transaction_id").cast("string").alias("transaction_id"),
            F.get_json_object("transaction_value", "$.customer_id").cast("string").alias("customer_id"),
            F.get_json_object("transaction_value", "$.merchant_id").cast("string").alias("merchant_id"),
            F.get_json_object("transaction_value", "$.amount").cast("decimal(12,2)").alias("amount"),
            F.get_json_object("transaction_value", "$.currency").cast("string").alias("currency"),
            F.get_json_object("transaction_value", "$.payment_method").cast("string").alias("payment_method"),
            F.get_json_object("transaction_value", "$.timestamp").cast("timestamp").alias("transaction_timestamp"),
            F.get_json_object("transaction_value", "$.card_last_four").cast("string").alias("card_last_four"),
            F.get_json_object("transaction_value", "$.merchant_category").cast("string").alias("merchant_category"),
            F.get_json_object("transaction_value", "$.location").cast("string").alias("location"),
            "kafka_timestamp",
            "ingestion_timestamp"
        )
        .withColumn("processing_date", F.to_date("transaction_timestamp"))
        .withColumn("processing_hour", F.hour("transaction_timestamp"))
        .withColumn("is_weekend", F.dayofweek("transaction_timestamp").isin([1, 7]))
        .withColumn("amount_usd", 
                   F.when(F.col("currency") == "EUR", F.col("amount") * 1.1)
                   .when(F.col("currency") == "GBP", F.col("amount") * 1.25)
                   .when(F.col("currency") == "JPY", F.col("amount") * 0.0067)
                   .otherwise(F.col("amount")))
        # Simple fraud scoring based on amount and timing
        .withColumn("fraud_score",
                   F.when(F.col("amount") > 5000, 0.8)
                   .when((F.col("amount") > 1000) & F.col("is_weekend"), 0.6)
                   .when(F.hour("transaction_timestamp").between(0, 5), 0.4)
                   .otherwise(0.1))
        .withColumn("is_high_risk", F.col("fraud_score") > 0.7)
    )

@dlt.table(
    comment="Processed IoT sensor readings with anomaly detection",
    table_properties={
        "quality": "silver"
    }
)
@dlt.expect_or_drop("valid_sensor_id", "sensor_id IS NOT NULL")
@dlt.expect_or_drop("valid_reading_timestamp", "reading_timestamp IS NOT NULL")
@dlt.expect("valid_temperature", "temperature BETWEEN -50 AND 100")
@dlt.expect("valid_humidity", "humidity BETWEEN 0 AND 100")
def iot_sensors_silver():
    """
    Process IoT sensor data with anomaly detection
    """
    return (
        dlt.read_stream("iot_sensors_bronze")
        .select(
            F.get_json_object("sensor_value", "$.sensor_id").cast("string").alias("sensor_id"),
            F.get_json_object("sensor_value", "$.device_type").cast("string").alias("device_type"),
            F.get_json_object("sensor_value", "$.location").cast("string").alias("location"),
            F.get_json_object("sensor_value", "$.timestamp").cast("timestamp").alias("reading_timestamp"),
            F.get_json_object("sensor_value", "$.temperature").cast("double").alias("temperature"),
            F.get_json_object("sensor_value", "$.humidity").cast("double").alias("humidity"),
            F.get_json_object("sensor_value", "$.pressure").cast("double").alias("pressure"),
            F.get_json_object("sensor_value", "$.battery_level").cast("double").alias("battery_level"),
            "kafka_timestamp",
            "ingestion_timestamp"
        )
        .withColumn("processing_date", F.to_date("reading_timestamp"))
        .withColumn("processing_hour", F.hour("reading_timestamp"))
        # Calculate rolling averages for anomaly detection
        .withColumn("temp_anomaly", 
                   F.when(F.abs(F.col("temperature") - 22.0) > 15, True).otherwise(False))
        .withColumn("humidity_anomaly",
                   F.when((F.col("humidity") < 20) | (F.col("humidity") > 80), True).otherwise(False))
        .withColumn("battery_critical", F.col("battery_level") < 20)
        .withColumn("sensor_status",
                   F.when(F.col("battery_critical"), "BATTERY_LOW")
                   .when(F.col("temp_anomaly") | F.col("humidity_anomaly"), "ANOMALY_DETECTED")
                   .otherwise("NORMAL"))
    )

# =====================================================
# GOLD LAYER - Business-Ready Aggregations
# =====================================================

@dlt.table(
    comment="Real-time customer engagement metrics",
    table_properties={
        "quality": "gold",
        "delta.autoOptimize.optimizeWrite": "true"
    }
)
def customer_engagement_metrics():
    """
    Calculate real-time customer engagement KPIs
    """
    return (
        dlt.read_stream("user_events_silver")
        .withWatermark("event_timestamp", "30 minutes")
        .groupBy(
            F.window("event_timestamp", "10 minutes", "5 minutes"),
            "user_id"
        )
        .agg(
            F.count("*").alias("total_events"),
            F.countDistinct("session_id").alias("sessions"),
            F.countDistinct("page_url").alias("unique_pages"),
            F.sum("session_duration").alias("total_session_time"),
            F.avg("session_duration").alias("avg_session_duration"),
            F.count(F.when(F.col("event_type") == "purchase", 1)).alias("purchases"),
            F.count(F.when(F.col("is_mobile"), 1)).alias("mobile_events"),
            F.first("device_type").alias("primary_device")
        )
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            "user_id",
            "total_events",
            "sessions",
            "unique_pages",
            "total_session_time",
            "avg_session_duration",
            "purchases",
            "mobile_events",
            "primary_device",
            (F.col("mobile_events") / F.col("total_events") * 100).alias("mobile_usage_pct"),
            F.when(F.col("purchases") > 0, "Buyer").otherwise("Browser").alias("user_type"),
            F.current_timestamp().alias("calculated_at")
        )
    )

@dlt.table(
    comment="Real-time fraud detection alerts",
    table_properties={
        "quality": "gold"
    }
)
def fraud_detection_alerts():
    """
    Generate real-time fraud alerts based on transaction patterns
    """
    return (
        dlt.read_stream("transactions_silver")
        .withWatermark("transaction_timestamp", "10 minutes")
        .groupBy(
            F.window("transaction_timestamp", "5 minutes"),
            "customer_id"
        )
        .agg(
            F.count("*").alias("transaction_count"),
            F.sum("amount_usd").alias("total_amount"),
            F.max("amount_usd").alias("max_amount"),
            F.avg("fraud_score").alias("avg_fraud_score"),
            F.countDistinct("merchant_id").alias("unique_merchants"),
            F.countDistinct("location").alias("unique_locations"),
            F.sum(F.when(F.col("is_high_risk"), 1).otherwise(0)).alias("high_risk_count")
        )
        .filter(
            (F.col("transaction_count") > 5) |  # High frequency
            (F.col("total_amount") > 10000) |   # High amount
            (F.col("unique_locations") > 3) |   # Multiple locations
            (F.col("avg_fraud_score") > 0.6)    # High fraud score
        )
        .select(
            F.col("window.start").alias("alert_window_start"),
            F.col("window.end").alias("alert_window_end"),
            "customer_id",
            "transaction_count",
            "total_amount",
            "max_amount",
            "avg_fraud_score",
            "unique_merchants",
            "unique_locations",
            "high_risk_count",
            F.when(F.col("transaction_count") > 10, "VELOCITY_ALERT")
            .when(F.col("total_amount") > 20000, "AMOUNT_ALERT")
            .when(F.col("unique_locations") > 5, "LOCATION_ALERT")
            .when(F.col("avg_fraud_score") > 0.8, "FRAUD_SCORE_ALERT")
            .otherwise("GENERAL_ALERT").alias("alert_type"),
            F.current_timestamp().alias("alert_generated_at")
        )
    )

@dlt.table(
    comment="Real-time operational metrics from IoT sensors",
    table_properties={
        "quality": "gold"
    }
)
def operational_metrics():
    """
    Calculate operational KPIs from IoT sensor data
    """
    return (
        dlt.read_stream("iot_sensors_silver")
        .withWatermark("reading_timestamp", "15 minutes")
        .groupBy(
            F.window("reading_timestamp", "5 minutes"),
            "location",
            "device_type"
        )
        .agg(
            F.count("*").alias("total_readings"),
            F.avg("temperature").alias("avg_temperature"),
            F.min("temperature").alias("min_temperature"),
            F.max("temperature").alias("max_temperature"),
            F.avg("humidity").alias("avg_humidity"),
            F.avg("pressure").alias("avg_pressure"),
            F.avg("battery_level").alias("avg_battery_level"),
            F.count(F.when(F.col("sensor_status") == "NORMAL", 1)).alias("normal_readings"),
            F.count(F.when(F.col("sensor_status") == "ANOMALY_DETECTED", 1)).alias("anomaly_readings"),
            F.count(F.when(F.col("sensor_status") == "BATTERY_LOW", 1)).alias("battery_low_readings"),
            F.countDistinct("sensor_id").alias("active_sensors")
        )
        .select(
            F.col("window.start").alias("metric_window_start"),
            F.col("window.end").alias("metric_window_end"),
            "location",
            "device_type",
            "total_readings",
            "avg_temperature",
            "min_temperature",
            "max_temperature",
            "avg_humidity",
            "avg_pressure",
            "avg_battery_level",
            "normal_readings",
            "anomaly_readings", 
            "battery_low_readings",
            "active_sensors",
            (F.col("normal_readings") / F.col("total_readings") * 100).alias("health_score_pct"),
            (F.col("anomaly_readings") / F.col("total_readings") * 100).alias("anomaly_rate_pct"),
            F.when(F.col("anomaly_rate_pct") > 20, "CRITICAL")
            .when(F.col("anomaly_rate_pct") > 10, "WARNING")
            .otherwise("NORMAL").alias("operational_status"),
            F.current_timestamp().alias("calculated_at")
        )
    )

@dlt.table(
    comment="Hourly business KPIs across all data sources",
    table_properties={
        "quality": "gold"
    }
)
def hourly_business_kpis():
    """
    Comprehensive business KPIs combining all data sources
    """
    # Get user engagement data
    user_metrics = dlt.read_stream("customer_engagement_metrics").alias("um")
    
    # Get transaction data
    transaction_metrics = (
        dlt.read_stream("transactions_silver")
        .withWatermark("transaction_timestamp", "1 hour")
        .groupBy(F.window("transaction_timestamp", "1 hour"))
        .agg(
            F.count("*").alias("total_transactions"),
            F.sum("amount_usd").alias("total_revenue"),
            F.countDistinct("customer_id").alias("active_customers"),
            F.avg("amount_usd").alias("avg_transaction_value"),
            F.count(F.when(F.col("is_high_risk"), 1)).alias("high_risk_transactions")
        )
        .alias("tm")
    )
    
    # Get operational data
    operational_data = (
        dlt.read_stream("operational_metrics")
        .groupBy("metric_window_start")
        .agg(
            F.avg("health_score_pct").alias("avg_system_health"),
            F.sum("anomaly_readings").alias("total_anomalies"),
            F.count("location").alias("monitored_locations")
        )
        .alias("od")
    )
    
    # Combine all metrics
    return (
        transaction_metrics
        .join(
            operational_data,
            F.col("tm.window.start") == F.col("od.metric_window_start"),
            "left"
        )
        .select(
            F.col("tm.window.start").alias("hour_start"),
            F.col("tm.window.end").alias("hour_end"),
            "total_transactions",
            "total_revenue", 
            "active_customers",
            "avg_transaction_value",
            "high_risk_transactions",
            F.coalesce("avg_system_health", F.lit(100)).alias("system_health_score"),
            F.coalesce("total_anomalies", F.lit(0)).alias("operational_anomalies"),
            F.coalesce("monitored_locations", F.lit(0)).alias("monitored_locations"),
            (F.col("total_revenue") / F.col("active_customers")).alias("revenue_per_customer"),
            (F.col("high_risk_transactions") / F.col("total_transactions") * 100).alias("fraud_rate_pct"),
            F.current_timestamp().alias("kpi_calculated_at")
        )
    )