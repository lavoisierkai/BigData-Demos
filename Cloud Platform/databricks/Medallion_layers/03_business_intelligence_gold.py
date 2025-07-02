# Databricks notebook source
# MAGIC %md
# MAGIC # Business Intelligence & Gold Layer
# MAGIC 
# MAGIC This notebook demonstrates gold layer creation for business intelligence:
# MAGIC - Customer analytics and segmentation
# MAGIC - Product performance metrics
# MAGIC - Revenue and financial KPIs
# MAGIC - Operational dashboards
# MAGIC - Real-time business metrics
# MAGIC 
# MAGIC **Architecture**: Silver Layer → Gold Layer (Business-Ready Analytics)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
from delta.tables import *
from datetime import datetime, timedelta
import numpy as np

# Configuration
DATABASE_NAME = "demo_lakehouse"
SILVER_PATH = "/tmp/demo/silver"
GOLD_PATH = "/tmp/demo/gold"

# Use existing database
spark.sql(f"USE {DATABASE_NAME}")

print(f"Processing Silver → Gold layer transformation")
print(f"Gold layer path: {GOLD_PATH}")

# Load Silver layer tables
silver_transactions = spark.table(f"{DATABASE_NAME}.silver_ecommerce_transactions")
silver_customers = spark.table(f"{DATABASE_NAME}.silver_customer_demographics")
silver_iot = spark.table(f"{DATABASE_NAME}.silver_iot_sensor_data")

print("📊 Silver Layer Data Loaded")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Customer Analytics & Segmentation

# COMMAND ----------

def create_customer_analytics():
    """
    Create comprehensive customer analytics for business intelligence
    """
    
    # Customer transaction aggregations
    customer_metrics = silver_transactions \
        .groupBy("customer_id") \
        .agg(
            count("transaction_id").alias("total_transactions"),
            sum("total_value").alias("total_spent"),
            avg("total_value").alias("avg_transaction_value"),
            max("transaction_date").alias("last_transaction_date"),
            min("transaction_date").alias("first_transaction_date"),
            countDistinct("product_category_standardized").alias("unique_categories"),
            countDistinct("product_id").alias("unique_products"),
            sum(when(col("is_weekend"), col("total_value")).otherwise(0)).alias("weekend_spending"),
            sum(when(~col("is_weekend"), col("total_value")).otherwise(0)).alias("weekday_spending"),
            collect_set("product_category_standardized").alias("preferred_categories"),
            first("customer_location_clean").alias("location"),
            first("payment_method_category").alias("preferred_payment_method")
        )
    
    # Calculate customer lifetime metrics
    customer_metrics_enhanced = customer_metrics \
        .withColumn("customer_lifetime_days",
                   datediff(col("last_transaction_date"), col("first_transaction_date"))) \
        .withColumn("avg_days_between_purchases",
                   col("customer_lifetime_days") / greatest(col("total_transactions") - 1, lit(1))) \
        .withColumn("weekend_preference",
                   col("weekend_spending") / (col("weekend_spending") + col("weekday_spending"))) \
        .withColumn("recency_days",
                   datediff(current_date(), col("last_transaction_date")))
    
    # Join with customer demographics
    customer_complete = customer_metrics_enhanced \
        .join(silver_customers.select("customer_id", "age", "age_group", "customer_tier", 
                                    "loyalty_tier", "data_completeness_score"),
              "customer_id", "left")
    
    # Customer segmentation using RFM analysis
    # Calculate percentiles for RFM scoring
    recency_percentiles = customer_complete.approxQuantile("recency_days", [0.2, 0.4, 0.6, 0.8], 0.01)
    frequency_percentiles = customer_complete.approxQuantile("total_transactions", [0.2, 0.4, 0.6, 0.8], 0.01)
    monetary_percentiles = customer_complete.approxQuantile("total_spent", [0.2, 0.4, 0.6, 0.8], 0.01)
    
    # Apply RFM scoring (5 = best, 1 = worst)
    customer_rfm = customer_complete \
        .withColumn("recency_score",
                   when(col("recency_days") <= recency_percentiles[0], 5)
                   .when(col("recency_days") <= recency_percentiles[1], 4)
                   .when(col("recency_days") <= recency_percentiles[2], 3)
                   .when(col("recency_days") <= recency_percentiles[3], 2)
                   .otherwise(1)) \
        .withColumn("frequency_score",
                   when(col("total_transactions") >= frequency_percentiles[3], 5)
                   .when(col("total_transactions") >= frequency_percentiles[2], 4)
                   .when(col("total_transactions") >= frequency_percentiles[1], 3)
                   .when(col("total_transactions") >= frequency_percentiles[0], 2)
                   .otherwise(1)) \
        .withColumn("monetary_score",
                   when(col("total_spent") >= monetary_percentiles[3], 5)
                   .when(col("total_spent") >= monetary_percentiles[2], 4)
                   .when(col("total_spent") >= monetary_percentiles[1], 3)
                   .when(col("total_spent") >= monetary_percentiles[0], 2)
                   .otherwise(1))
    
    # Create RFM segment
    customer_segmented = customer_rfm \
        .withColumn("rfm_score", col("recency_score") + col("frequency_score") + col("monetary_score")) \
        .withColumn("customer_segment",
                   when(col("rfm_score") >= 13, "Champions")
                   .when(col("rfm_score") >= 11, "Loyal Customers")
                   .when(col("rfm_score") >= 9, "Potential Loyalists")
                   .when(col("rfm_score") >= 7, "New Customers")
                   .when(col("rfm_score") >= 5, "Promising")
                   .when(col("rfm_score") >= 3, "Customers Needing Attention")
                   .otherwise("At Risk")) \
        .withColumn("clv_estimate",
                   col("avg_transaction_value") * col("total_transactions") * 
                   (365 / greatest(col("customer_lifetime_days"), lit(1)))) \
        .withColumn("churn_risk_score",
                   when(col("recency_days") > 90, 0.8)
                   .when(col("recency_days") > 60, 0.6) 
                   .when(col("recency_days") > 30, 0.4)
                   .when(col("recency_days") > 14, 0.2)
                   .otherwise(0.1)) \
        .withColumn("analysis_date", current_date()) \
        .withColumn("gold_layer_version", lit("v1.0"))
    
    return customer_segmented

# Create customer analytics
customer_analytics = create_customer_analytics()

print("👥 Customer Segmentation Results:")
customer_analytics.groupBy("customer_segment") \
    .agg(count("*").alias("customer_count"),
         avg("total_spent").alias("avg_total_spent"),
         avg("churn_risk_score").alias("avg_churn_risk")) \
    .orderBy(desc("avg_total_spent")) \
    .show()

# Write to Gold layer
customer_analytics.write \
    .format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .save(f"{GOLD_PATH}/customer_analytics")

# Create table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.gold_customer_analytics
    USING DELTA
    LOCATION '{GOLD_PATH}/customer_analytics'
""")

print("✅ Customer analytics table created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Product Performance & Category Analysis

# COMMAND ----------

def create_product_analytics():
    """
    Create product performance analytics
    """
    
    # Product-level metrics
    product_metrics = silver_transactions \
        .groupBy("product_id", "product_name_clean", "product_category_standardized") \
        .agg(
            count("transaction_id").alias("total_sales"),
            sum("quantity").alias("total_quantity_sold"),
            sum("total_value").alias("total_revenue"),
            avg("amount").alias("avg_unit_price"),
            countDistinct("customer_id").alias("unique_customers"),
            max("transaction_date").alias("last_sold_date"),
            min("transaction_date").alias("first_sold_date"),
            stddev("amount").alias("price_volatility")
        )
    
    # Category-level aggregations
    category_metrics = silver_transactions \
        .groupBy("product_category_standardized") \
        .agg(
            count("transaction_id").alias("category_transactions"),
            sum("total_value").alias("category_revenue"),
            countDistinct("product_id").alias("unique_products_in_category"),
            countDistinct("customer_id").alias("unique_customers_in_category"),
            avg("total_value").alias("avg_transaction_value_category")
        )
    
    # Join product metrics with category metrics for insights
    product_enhanced = product_metrics \
        .join(category_metrics, "product_category_standardized", "left") \
        .withColumn("product_market_share",
                   col("total_revenue") / col("category_revenue")) \
        .withColumn("customer_penetration",
                   col("unique_customers") / col("unique_customers_in_category")) \
        .withColumn("sales_performance_score",
                   (col("total_sales") * 0.3 + 
                    col("total_revenue") * 0.4 + 
                    col("unique_customers") * 0.3) / 100) \
        .withColumn("days_in_catalog",
                   datediff(col("last_sold_date"), col("first_sold_date"))) \
        .withColumn("sales_velocity",
                   col("total_sales") / greatest(col("days_in_catalog"), lit(1))) \
        .withColumn("product_status",
                   when(col("last_sold_date") >= date_sub(current_date(), 30), "Active")
                   .when(col("last_sold_date") >= date_sub(current_date(), 90), "Slow Moving")
                   .otherwise("Dormant")) \
        .withColumn("price_tier",
                   when(col("avg_unit_price") >= 300, "Premium")
                   .when(col("avg_unit_price") >= 150, "Mid-range")
                   .otherwise("Budget")) \
        .withColumn("analysis_date", current_date()) \
        .withColumn("gold_layer_version", lit("v1.0"))
    
    return product_enhanced

# Create product analytics
product_analytics = create_product_analytics()

print("📦 Product Performance by Category:")
product_analytics.groupBy("product_category_standardized", "price_tier") \
    .agg(count("*").alias("product_count"),
         sum("total_revenue").alias("category_revenue"),
         avg("product_market_share").alias("avg_market_share")) \
    .orderBy("product_category_standardized", "price_tier") \
    .show()

# Write to Gold layer
product_analytics.write \
    .format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .save(f"{GOLD_PATH}/product_analytics")

# Create table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.gold_product_analytics
    USING DELTA
    LOCATION '{GOLD_PATH}/product_analytics'
""")

print("✅ Product analytics table created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Financial KPIs & Revenue Analytics

# COMMAND ----------

def create_financial_kpis():
    """
    Create financial KPIs and revenue analytics
    """
    
    # Daily revenue metrics
    daily_revenue = silver_transactions \
        .groupBy("transaction_date") \
        .agg(
            count("transaction_id").alias("daily_transactions"),
            sum("total_value").alias("daily_revenue"),
            avg("total_value").alias("avg_transaction_value"),
            countDistinct("customer_id").alias("daily_active_customers"),
            countDistinct("product_id").alias("daily_products_sold"),
            sum("quantity").alias("daily_items_sold")
        ) \
        .withColumn("revenue_per_customer", col("daily_revenue") / col("daily_active_customers")) \
        .withColumn("items_per_transaction", col("daily_items_sold") / col("daily_transactions"))
    
    # Add rolling metrics
    window_7d = Window.orderBy("transaction_date").rowsBetween(-6, 0)
    window_30d = Window.orderBy("transaction_date").rowsBetween(-29, 0)
    
    daily_with_rolling = daily_revenue \
        .withColumn("revenue_7d_avg", avg("daily_revenue").over(window_7d)) \
        .withColumn("revenue_30d_avg", avg("daily_revenue").over(window_30d)) \
        .withColumn("transactions_7d_avg", avg("daily_transactions").over(window_7d)) \
        .withColumn("customers_7d_avg", avg("daily_active_customers").over(window_7d)) \
        .withColumn("revenue_growth_7d",
                   (col("daily_revenue") - col("revenue_7d_avg")) / col("revenue_7d_avg") * 100) \
        .withColumn("customer_growth_7d",
                   (col("daily_active_customers") - col("customers_7d_avg")) / col("customers_7d_avg") * 100)
    
    # Monthly aggregations
    monthly_kpis = silver_transactions \
        .withColumn("year_month", date_format(col("transaction_date"), "yyyy-MM")) \
        .groupBy("year_month") \
        .agg(
            sum("total_value").alias("monthly_revenue"),
            count("transaction_id").alias("monthly_transactions"),
            countDistinct("customer_id").alias("monthly_active_customers"),
            countDistinct("product_id").alias("monthly_products_sold"),
            avg("total_value").alias("monthly_avg_transaction"),
            sum("quantity").alias("monthly_items_sold")
        ) \
        .withColumn("revenue_per_customer", col("monthly_revenue") / col("monthly_active_customers")) \
        .withColumn("transactions_per_customer", col("monthly_transactions") / col("monthly_active_customers"))
    
    # Add month-over-month growth
    window_month = Window.orderBy("year_month")
    
    monthly_with_growth = monthly_kpis \
        .withColumn("prev_month_revenue", lag("monthly_revenue").over(window_month)) \
        .withColumn("revenue_mom_growth",
                   (col("monthly_revenue") - col("prev_month_revenue")) / col("prev_month_revenue") * 100) \
        .withColumn("prev_month_customers", lag("monthly_active_customers").over(window_month)) \
        .withColumn("customer_mom_growth",
                   (col("monthly_active_customers") - col("prev_month_customers")) / col("prev_month_customers") * 100) \
        .withColumn("analysis_date", current_date()) \
        .withColumn("gold_layer_version", lit("v1.0"))
    
    return daily_with_rolling, monthly_with_growth

# Create financial KPIs
daily_kpis, monthly_kpis = create_financial_kpis()

print("💰 Monthly Revenue Performance:")
monthly_kpis.select("year_month", "monthly_revenue", "monthly_active_customers", 
                   "revenue_mom_growth", "customer_mom_growth") \
    .orderBy("year_month") \
    .show()

# Write to Gold layer
daily_kpis.write \
    .format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .save(f"{GOLD_PATH}/daily_financial_kpis")

monthly_kpis.write \
    .format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .save(f"{GOLD_PATH}/monthly_financial_kpis")

# Create tables
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.gold_daily_financial_kpis
    USING DELTA
    LOCATION '{GOLD_PATH}/daily_financial_kpis'
""")

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.gold_monthly_financial_kpis
    USING DELTA
    LOCATION '{GOLD_PATH}/monthly_financial_kpis'
""")

print("✅ Financial KPI tables created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Operational Analytics from IoT Data

# COMMAND ----------

def create_operational_analytics():
    """
    Create operational analytics from IoT sensor data
    """
    
    # Hourly operational metrics
    hourly_operations = silver_iot \
        .withColumn("date_hour", date_format(col("timestamp"), "yyyy-MM-dd HH")) \
        .groupBy("date_hour", "location") \
        .agg(
            count("*").alias("total_readings"),
            avg("temperature").alias("avg_temperature"),
            min("temperature").alias("min_temperature"),
            max("temperature").alias("max_temperature"),
            avg("humidity").alias("avg_humidity"),
            avg("pressure").alias("avg_pressure"),
            avg("battery_level").alias("avg_battery_level"),
            sum(when(col("sensor_status") == "NORMAL", 1).otherwise(0)).alias("normal_readings"),
            sum(when(col("sensor_status").contains("ANOMALY"), 1).otherwise(0)).alias("anomaly_readings"),
            sum(when(col("battery_critical"), 1).otherwise(0)).alias("critical_battery_readings"),
            countDistinct("sensor_id").alias("active_sensors")
        )
    
    # Calculate operational efficiency metrics
    operational_efficiency = hourly_operations \
        .withColumn("normal_reading_percentage", 
                   col("normal_readings") / col("total_readings") * 100) \
        .withColumn("anomaly_rate", 
                   col("anomaly_readings") / col("total_readings") * 100) \
        .withColumn("critical_battery_rate",
                   col("critical_battery_readings") / col("total_readings") * 100) \
        .withColumn("operational_health_score",
                   greatest(lit(0), 
                           100 - col("anomaly_rate") * 2 - col("critical_battery_rate") * 3)) \
        .withColumn("temperature_range", col("max_temperature") - col("min_temperature")) \
        .withColumn("environment_status",
                   when((col("avg_temperature").between(20, 26)) & 
                        (col("avg_humidity").between(40, 60)), "Optimal")
                   .when((col("avg_temperature") < 18) | (col("avg_temperature") > 28), "Temperature Alert")
                   .when((col("avg_humidity") < 30) | (col("avg_humidity") > 70), "Humidity Alert")
                   .otherwise("Acceptable"))
    
    # Daily operational summary
    daily_operations = silver_iot \
        .groupBy("reading_date", "location") \
        .agg(
            count("*").alias("daily_readings"),
            countDistinct("sensor_id").alias("sensors_reporting"),
            avg("data_quality_score").alias("avg_data_quality"),
            sum(when(col("sensor_status") == "NORMAL", 1).otherwise(0)).alias("normal_readings_daily"),
            sum(when(col("battery_critical"), 1).otherwise(0)).alias("critical_battery_daily"),
            avg("temperature").alias("daily_avg_temperature"),
            stddev("temperature").alias("daily_temp_volatility")
        ) \
        .withColumn("sensor_uptime_percentage",
                   col("sensors_reporting") / lit(4) * 100)  # Assuming 4 sensors per location \
        .withColumn("daily_operational_score",
                   (col("avg_data_quality") * 40 + 
                    col("sensor_uptime_percentage") * 30 + 
                    (100 - col("critical_battery_daily") / col("daily_readings") * 100) * 30)) \
        .withColumn("analysis_date", current_date()) \
        .withColumn("gold_layer_version", lit("v1.0"))
    
    return operational_efficiency, daily_operations

# Create operational analytics
hourly_ops, daily_ops = create_operational_analytics()

print("🏭 Operational Performance by Location:")
daily_ops.groupBy("location") \
    .agg(avg("daily_operational_score").alias("avg_operational_score"),
         avg("sensor_uptime_percentage").alias("avg_uptime"),
         avg("daily_avg_temperature").alias("avg_temperature")) \
    .orderBy(desc("avg_operational_score")) \
    .show()

# Write to Gold layer
hourly_ops.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("location") \
    .option("mergeSchema", "true") \
    .save(f"{GOLD_PATH}/hourly_operational_analytics")

daily_ops.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("location") \
    .option("mergeSchema", "true") \
    .save(f"{GOLD_PATH}/daily_operational_analytics")

# Create tables
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.gold_hourly_operational_analytics
    USING DELTA
    LOCATION '{GOLD_PATH}/hourly_operational_analytics'
""")

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.gold_daily_operational_analytics
    USING DELTA
    LOCATION '{GOLD_PATH}/daily_operational_analytics'
""")

print("✅ Operational analytics tables created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Executive Dashboard Summary

# COMMAND ----------

def create_executive_summary():
    """
    Create executive summary dashboard data
    """
    
    # Key business metrics summary
    business_summary = spark.sql(f"""
        WITH revenue_metrics AS (
            SELECT 
                SUM(total_value) as total_revenue,
                COUNT(DISTINCT customer_id) as total_customers,
                COUNT(transaction_id) as total_transactions,
                AVG(total_value) as avg_order_value
            FROM {DATABASE_NAME}.silver_ecommerce_transactions
        ),
        customer_metrics AS (
            SELECT 
                customer_segment,
                COUNT(*) as segment_size,
                AVG(total_spent) as avg_segment_value,
                AVG(churn_risk_score) as avg_churn_risk
            FROM {DATABASE_NAME}.gold_customer_analytics
            GROUP BY customer_segment
        ),
        product_metrics AS (
            SELECT 
                product_category_standardized,
                SUM(total_revenue) as category_revenue,
                COUNT(*) as products_in_category
            FROM {DATABASE_NAME}.gold_product_analytics
            GROUP BY product_category_standardized
        ),
        operational_metrics AS (
            SELECT 
                AVG(daily_operational_score) as avg_operational_score,
                AVG(sensor_uptime_percentage) as avg_sensor_uptime
            FROM {DATABASE_NAME}.gold_daily_operational_analytics
        )
        SELECT 
            r.total_revenue,
            r.total_customers,
            r.total_transactions,
            r.avg_order_value,
            o.avg_operational_score,
            o.avg_sensor_uptime,
            CURRENT_DATE() as report_date
        FROM revenue_metrics r
        CROSS JOIN operational_metrics o
    """)
    
    # Top performing segments and categories
    top_segments = spark.sql(f"""
        SELECT 'Customer Segment' as metric_type, customer_segment as metric_name, 
               CAST(COUNT(*) AS STRING) as metric_value, 'count' as metric_unit
        FROM {DATABASE_NAME}.gold_customer_analytics
        GROUP BY customer_segment
        ORDER BY COUNT(*) DESC
        LIMIT 5
        
        UNION ALL
        
        SELECT 'Product Category' as metric_type, product_category_standardized as metric_name,
               CAST(ROUND(SUM(total_revenue), 2) AS STRING) as metric_value, 'revenue' as metric_unit
        FROM {DATABASE_NAME}.gold_product_analytics  
        GROUP BY product_category_standardized
        ORDER BY SUM(total_revenue) DESC
        LIMIT 5
    """)
    
    # Recent trends (last 7 days)
    recent_trends = spark.sql(f"""
        SELECT 
            transaction_date,
            daily_revenue,
            daily_transactions,
            daily_active_customers,
            ROUND(revenue_growth_7d, 2) as revenue_growth_7d
        FROM {DATABASE_NAME}.gold_daily_financial_kpis
        WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), 7)
        ORDER BY transaction_date DESC
    """)
    
    return business_summary, top_segments, recent_trends

# Create executive summary
exec_summary, top_metrics, trends = create_executive_summary()

print("📈 Executive Business Summary:")
display(exec_summary)

print("\n🏆 Top Performing Segments & Categories:")
display(top_metrics)

print("\n📊 Recent Trends (Last 7 Days):")
display(trends)

# Write executive summary to Gold layer
exec_summary.write \
    .format("delta") \
    .mode("overwrite") \
    .save(f"{GOLD_PATH}/executive_summary")

# Create table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE_NAME}.gold_executive_summary
    USING DELTA
    LOCATION '{GOLD_PATH}/executive_summary'
""")

print("✅ Executive summary table created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Real-time Business Alerts

# COMMAND ----------

def generate_business_alerts():
    """
    Generate business alerts based on Gold layer analytics
    """
    
    alerts = []
    
    # Revenue alerts
    recent_revenue = spark.sql(f"""
        SELECT daily_revenue, revenue_growth_7d 
        FROM {DATABASE_NAME}.gold_daily_financial_kpis
        ORDER BY transaction_date DESC
        LIMIT 1
    """).collect()[0]
    
    if recent_revenue['revenue_growth_7d'] < -10:
        alerts.append({
            'alert_type': 'Revenue Decline',
            'severity': 'High',
            'message': f'Revenue declined by {recent_revenue["revenue_growth_7d"]:.1f}% (7-day avg)',
            'metric_value': recent_revenue['revenue_growth_7d'],
            'threshold': -10
        })
    
    # Customer churn alerts
    high_churn_customers = spark.sql(f"""
        SELECT COUNT(*) as high_churn_count
        FROM {DATABASE_NAME}.gold_customer_analytics
        WHERE churn_risk_score > 0.7
    """).collect()[0]['high_churn_count']
    
    if high_churn_customers > 0:
        alerts.append({
            'alert_type': 'High Churn Risk',
            'severity': 'Medium',
            'message': f'{high_churn_customers} customers at high risk of churn',
            'metric_value': high_churn_customers,
            'threshold': 0
        })
    
    # Operational alerts
    low_operational_score = spark.sql(f"""
        SELECT location, daily_operational_score
        FROM {DATABASE_NAME}.gold_daily_operational_analytics
        WHERE reading_date = CURRENT_DATE() - 1 AND daily_operational_score < 80
    """).collect()
    
    for location_alert in low_operational_score:
        alerts.append({
            'alert_type': 'Operational Issue',
            'severity': 'Medium',
            'message': f'Low operational score at {location_alert["location"]}: {location_alert["daily_operational_score"]:.1f}%',
            'metric_value': location_alert['daily_operational_score'],
            'threshold': 80
        })
    
    # Convert alerts to DataFrame
    if alerts:
        alerts_df = spark.createDataFrame(alerts) \
            .withColumn("alert_timestamp", current_timestamp()) \
            .withColumn("alert_date", current_date())
        
        print("🚨 Active Business Alerts:")
        display(alerts_df)
        
        # Save alerts
        alerts_df.write \
            .format("delta") \
            .mode("append") \
            .save(f"{GOLD_PATH}/business_alerts")
    else:
        print("✅ No active alerts - all metrics within normal ranges")

generate_business_alerts()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Summary and Performance Metrics

# COMMAND ----------

print("🎯 Gold Layer Summary:")
print("=" * 50)

# Count records in all Gold tables
gold_summary = spark.sql(f"""
    SELECT 'Customer Analytics' as table_name, COUNT(*) as record_count
    FROM {DATABASE_NAME}.gold_customer_analytics
    
    UNION ALL
    
    SELECT 'Product Analytics' as table_name, COUNT(*) as record_count
    FROM {DATABASE_NAME}.gold_product_analytics
    
    UNION ALL
    
    SELECT 'Daily Financial KPIs' as table_name, COUNT(*) as record_count
    FROM {DATABASE_NAME}.gold_daily_financial_kpis
    
    UNION ALL
    
    SELECT 'Monthly Financial KPIs' as table_name, COUNT(*) as record_count
    FROM {DATABASE_NAME}.gold_monthly_financial_kpis
    
    UNION ALL
    
    SELECT 'Daily Operational Analytics' as table_name, COUNT(*) as record_count
    FROM {DATABASE_NAME}.gold_daily_operational_analytics
    
    UNION ALL
    
    SELECT 'Executive Summary' as table_name, COUNT(*) as record_count
    FROM {DATABASE_NAME}.gold_executive_summary
""")

display(gold_summary)

# Business insights summary
insights_summary = spark.sql(f"""
    SELECT 
        'Total Business Value' as metric,
        CONCAT('$', FORMAT_NUMBER(SUM(total_spent), 2)) as value
    FROM {DATABASE_NAME}.gold_customer_analytics
    
    UNION ALL
    
    SELECT 
        'Customer Segments' as metric,
        CAST(COUNT(DISTINCT customer_segment) AS STRING) as value
    FROM {DATABASE_NAME}.gold_customer_analytics
    
    UNION ALL
    
    SELECT 
        'Product Categories' as metric,
        CAST(COUNT(DISTINCT product_category_standardized) AS STRING) as value
    FROM {DATABASE_NAME}.gold_product_analytics
    
    UNION ALL
    
    SELECT 
        'Operational Locations' as metric,
        CAST(COUNT(DISTINCT location) AS STRING) as value
    FROM {DATABASE_NAME}.gold_daily_operational_analytics
""")

print("\n📊 Business Insights:")
display(insights_summary)

print("\n✅ Gold Layer Processing Complete!")
print("\nKey Features Demonstrated:")
print("• Customer segmentation using RFM analysis")
print("• Product performance and market share analysis")
print("• Financial KPIs with growth metrics")
print("• Operational analytics from IoT data")
print("• Executive dashboard summaries")
print("• Real-time business alerts")
print("• Multi-dimensional business intelligence")

print("\n🔄 Next Steps:")
print("• Set up automated dashboard refreshes")
print("• Implement machine learning models on Gold data")
print("• Create Databricks SQL dashboards")
print("• Set up scheduled alert notifications")
print("• Optimize query performance with Z-ORDER")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optional: Optimize Tables for Performance

# COMMAND ----------

# Optimize Gold tables for query performance
tables_to_optimize = [
    "gold_customer_analytics",
    "gold_product_analytics", 
    "gold_daily_financial_kpis",
    "gold_monthly_financial_kpis"
]

for table in tables_to_optimize:
    try:
        # Run OPTIMIZE with Z-ORDER for better query performance
        spark.sql(f"OPTIMIZE {DATABASE_NAME}.{table}")
        print(f"✅ Optimized {table}")
        
        # Add Z-ORDER for commonly filtered columns
        if "customer" in table:
            spark.sql(f"OPTIMIZE {DATABASE_NAME}.{table} ZORDER BY (customer_segment, churn_risk_score)")
        elif "product" in table:
            spark.sql(f"OPTIMIZE {DATABASE_NAME}.{table} ZORDER BY (product_category_standardized, product_status)")
        elif "financial" in table:
            spark.sql(f"OPTIMIZE {DATABASE_NAME}.{table} ZORDER BY (transaction_date)")
            
    except Exception as e:
        print(f"Could not optimize {table}: {e}")

print("\n🚀 Gold layer tables optimized for analytics workloads!")