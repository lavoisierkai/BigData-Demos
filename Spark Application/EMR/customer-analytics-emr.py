#!/usr/bin/env python3
"""
Sample Spark Application for EMR Deployment
Customer Analytics Pipeline for Retail Business Intelligence

This application demonstrates:
- Reading data from S3 with optimized configurations for EMR
- Advanced customer segmentation and RFM analysis
- Machine learning for customer lifetime value prediction
- Writing results to multiple formats (Delta Lake, Hive, S3)
- Integration with EMR-specific features
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler, StandardScaler, Bucketizer
from pyspark.ml.clustering import KMeans
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml import Pipeline
import sys
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_spark_session(app_name):
    """Create Spark session with EMR-optimized configurations"""
    return SparkSession.builder \
        .appName(app_name) \
        .enableHiveSupport() \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.sql.adaptive.skewJoin.enabled", "true") \
        .config("spark.sql.adaptive.localShuffleReader.enabled", "true") \
        .config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "256MB") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.hadoop.fs.s3.optimized.committer.enabled", "true") \
        .config("spark.hadoop.fs.s3.committer.name", "partitioned") \
        .config("spark.hadoop.fs.s3.committer.staging.conflict-mode", "append") \
        .config("spark.sql.parquet.compression.codec", "snappy") \
        .config("spark.sql.warehouse.dir", "s3://your-data-lake/warehouse/") \
        .getOrCreate()

def read_customer_data(spark, base_path):
    """Read customer transaction data from S3"""
    logger.info(f"Reading customer data from: {base_path}")
    
    # Customer transactions schema
    transactions_schema = StructType([
        StructField("transaction_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("product_id", StringType(), True),
        StructField("product_category", StringType(), True),
        StructField("product_subcategory", StringType(), True),
        StructField("quantity", IntegerType(), True),
        StructField("unit_price", DoubleType(), True),
        StructField("discount", DoubleType(), True),
        StructField("transaction_date", TimestampType(), True),
        StructField("payment_method", StringType(), True),
        StructField("channel", StringType(), True),
        StructField("store_location", StringType(), True),
        StructField("customer_age", IntegerType(), True),
        StructField("customer_gender", StringType(), True),
        StructField("customer_segment", StringType(), True)
    ])
    
    # Read transactions
    transactions_df = spark.read \
        .option("header", "true") \
        .schema(transactions_schema) \
        .csv(f"{base_path}/transactions/")
    
    # Customer demographics schema
    demographics_schema = StructType([
        StructField("customer_id", StringType(), True),
        StructField("first_name", StringType(), True),
        StructField("last_name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("address", StringType(), True),
        StructField("city", StringType(), True),
        StructField("state", StringType(), True),
        StructField("zipcode", StringType(), True),
        StructField("registration_date", TimestampType(), True),
        StructField("preferred_channel", StringType(), True),
        StructField("income_bracket", StringType(), True)
    ])
    
    # Read customer demographics
    customers_df = spark.read \
        .option("header", "true") \
        .schema(demographics_schema) \
        .csv(f"{base_path}/customers/")
    
    return transactions_df, customers_df

def calculate_customer_metrics(transactions_df):
    """Calculate comprehensive customer metrics including RFM analysis"""
    logger.info("Calculating customer metrics and RFM analysis")
    
    # Calculate transaction amounts
    transactions_with_amount = transactions_df.withColumn(
        "transaction_amount", 
        col("quantity") * col("unit_price") * (1 - col("discount"))
    )
    
    # Define analysis date (for recency calculation)
    analysis_date = datetime.now()
    
    # Calculate RFM metrics
    rfm_metrics = transactions_with_amount.groupBy("customer_id").agg(
        # Recency: Days since last purchase
        datediff(lit(analysis_date), max("transaction_date")).alias("recency"),
        
        # Frequency: Number of transactions
        count("transaction_id").alias("frequency"),
        
        # Monetary: Total amount spent
        sum("transaction_amount").alias("monetary"),
        
        # Additional metrics
        avg("transaction_amount").alias("avg_order_value"),
        countDistinct("product_category").alias("category_diversity"),
        countDistinct("product_id").alias("product_diversity"),
        max("transaction_date").alias("last_purchase_date"),
        min("transaction_date").alias("first_purchase_date"),
        countDistinct("store_location").alias("store_diversity"),
        countDistinct("channel").alias("channel_diversity")
    )
    
    # Calculate customer lifetime (days between first and last purchase)
    customer_metrics = rfm_metrics.withColumn(
        "customer_lifetime_days",
        datediff(col("last_purchase_date"), col("first_purchase_date"))
    ).withColumn(
        "purchase_frequency_per_month",
        when(col("customer_lifetime_days") > 0, 
             col("frequency") * 30.0 / col("customer_lifetime_days"))
        .otherwise(col("frequency"))
    )
    
    return customer_metrics

def perform_rfm_segmentation(customer_metrics):
    """Perform RFM segmentation using quintiles"""
    logger.info("Performing RFM segmentation")
    
    # Calculate quintiles for R, F, M
    recency_quintiles = customer_metrics.approxQuantile("recency", [0.2, 0.4, 0.6, 0.8], 0.05)
    frequency_quintiles = customer_metrics.approxQuantile("frequency", [0.2, 0.4, 0.6, 0.8], 0.05)
    monetary_quintiles = customer_metrics.approxQuantile("monetary", [0.2, 0.4, 0.6, 0.8], 0.05)
    
    # Create bucketizers (note: for recency, lower is better, so we reverse the scoring)
    recency_bucketizer = Bucketizer(
        splits=[-float('inf')] + recency_quintiles + [float('inf')],
        inputCol="recency", outputCol="recency_score_raw"
    )
    
    frequency_bucketizer = Bucketizer(
        splits=[-float('inf')] + frequency_quintiles + [float('inf')],
        inputCol="frequency", outputCol="frequency_score"
    )
    
    monetary_bucketizer = Bucketizer(
        splits=[-float('inf')] + monetary_quintiles + [float('inf')],
        inputCol="monetary", outputCol="monetary_score"
    )
    
    # Apply bucketizers
    rfm_with_scores = recency_bucketizer.transform(customer_metrics)
    rfm_with_scores = frequency_bucketizer.transform(rfm_with_scores)
    rfm_with_scores = monetary_bucketizer.transform(rfm_with_scores)
    
    # Reverse recency score (lower recency = higher score)
    rfm_with_scores = rfm_with_scores.withColumn(
        "recency_score", 
        5 - col("recency_score_raw")
    )
    
    # Calculate RFM score
    rfm_segmented = rfm_with_scores.withColumn(
        "rfm_score",
        col("recency_score") * 100 + col("frequency_score") * 10 + col("monetary_score")
    )
    
    # Define customer segments based on RFM scores
    rfm_segmented = rfm_segmented.withColumn(
        "customer_segment",
        when((col("recency_score") >= 4) & (col("frequency_score") >= 4) & (col("monetary_score") >= 4), "Champions")
        .when((col("recency_score") >= 3) & (col("frequency_score") >= 3) & (col("monetary_score") >= 3), "Loyal Customers")
        .when((col("recency_score") >= 4) & (col("frequency_score") <= 2), "New Customers")
        .when((col("recency_score") >= 3) & (col("frequency_score") <= 3) & (col("monetary_score") >= 3), "Potential Loyalists")
        .when((col("recency_score") <= 2) & (col("frequency_score") >= 3) & (col("monetary_score") >= 3), "At Risk")
        .when((col("recency_score") <= 2) & (col("frequency_score") <= 2) & (col("monetary_score") >= 4), "Cannot Lose Them")
        .when((col("recency_score") <= 1) & (col("frequency_score") <= 2), "Lost")
        .otherwise("Others")
    )
    
    return rfm_segmented

def build_clv_prediction_model(customer_metrics, transactions_df):
    """Build Customer Lifetime Value prediction model using Random Forest"""
    logger.info("Building Customer Lifetime Value prediction model")
    
    # Prepare features for CLV prediction
    feature_columns = [
        "frequency", "monetary", "avg_order_value", "category_diversity",
        "product_diversity", "customer_lifetime_days", "purchase_frequency_per_month",
        "store_diversity", "channel_diversity"
    ]
    
    # Create feature vector
    assembler = VectorAssembler(inputCols=feature_columns, outputCol="features")
    
    # Scale features
    scaler = StandardScaler(inputCol="features", outputCol="scaled_features")
    
    # Create target variable (projected CLV based on current metrics)
    # This is a simplified CLV calculation - in practice, you'd use more sophisticated methods
    clv_data = customer_metrics.withColumn(
        "projected_clv",
        col("monetary") * (col("purchase_frequency_per_month") * 12) * 2  # 2-year projection
    ).filter(col("customer_lifetime_days") > 30)  # Filter customers with enough history
    
    # Random Forest model
    rf = RandomForestRegressor(
        featuresCol="scaled_features",
        labelCol="projected_clv",
        numTrees=100,
        maxDepth=10,
        seed=42
    )
    
    # Create pipeline
    pipeline = Pipeline(stages=[assembler, scaler, rf])
    
    # Split data
    train_data, test_data = clv_data.randomSplit([0.8, 0.2], seed=42)
    
    # Train model
    model = pipeline.fit(train_data)
    
    # Make predictions
    predictions = model.transform(test_data)
    
    # Evaluate model
    evaluator = RegressionEvaluator(
        labelCol="projected_clv",
        predictionCol="prediction",
        metricName="rmse"
    )
    
    rmse = evaluator.evaluate(predictions)
    logger.info(f"CLV Model RMSE: {rmse}")
    
    # Apply model to all customers
    all_predictions = model.transform(clv_data)
    
    return all_predictions, model, rmse

def perform_customer_clustering(customer_metrics):
    """Perform customer clustering using K-Means"""
    logger.info("Performing customer clustering analysis")
    
    # Prepare features for clustering
    clustering_features = [
        "frequency", "monetary", "avg_order_value", "category_diversity",
        "customer_lifetime_days", "purchase_frequency_per_month"
    ]
    
    # Create feature vector
    assembler = VectorAssembler(inputCols=clustering_features, outputCol="features")
    
    # Scale features
    scaler = StandardScaler(inputCol="features", outputCol="scaled_features")
    
    # K-Means clustering
    kmeans = KMeans(featuresCol="scaled_features", k=6, seed=42)
    
    # Create pipeline
    pipeline = Pipeline(stages=[assembler, scaler, kmeans])
    
    # Fit model
    model = pipeline.fit(customer_metrics)
    
    # Make predictions
    clustered_customers = model.transform(customer_metrics)
    
    # Add cluster descriptions
    clustered_customers = clustered_customers.withColumn(
        "cluster_description",
        when(col("prediction") == 0, "High Value Frequent")
        .when(col("prediction") == 1, "Medium Value Regular")
        .when(col("prediction") == 2, "Low Value Occasional")
        .when(col("prediction") == 3, "High Value Infrequent")
        .when(col("prediction") == 4, "New Customers")
        .otherwise("Other Segment")
    )
    
    return clustered_customers

def analyze_customer_behavior(transactions_df, customers_df):
    """Perform detailed customer behavior analysis"""
    logger.info("Analyzing customer behavior patterns")
    
    # Join transactions with customer demographics
    enriched_transactions = transactions_df.join(customers_df, "customer_id", "left")
    
    # Calculate behavioral metrics
    behavior_analysis = enriched_transactions.groupBy("customer_id").agg(
        # Channel preferences
        mode(col("channel")).alias("preferred_channel"),
        countDistinct("channel").alias("channels_used"),
        
        # Payment preferences
        mode(col("payment_method")).alias("preferred_payment"),
        countDistinct("payment_method").alias("payment_methods_used"),
        
        # Shopping patterns
        avg(hour(col("transaction_date"))).alias("avg_shopping_hour"),
        mode(dayofweek(col("transaction_date"))).alias("preferred_shopping_day"),
        
        # Category preferences
        mode(col("product_category")).alias("favorite_category"),
        collect_list("product_category").alias("categories_purchased"),
        
        # Seasonal patterns
        mode(month(col("transaction_date"))).alias("most_active_month"),
        stddev(col("quantity") * col("unit_price")).alias("spending_volatility")
    )
    
    return behavior_analysis

def create_customer_dashboard_data(rfm_segmented, clv_predictions, clustered_customers, behavior_analysis):
    """Create comprehensive customer dashboard data"""
    logger.info("Creating customer dashboard data")
    
    # Combine all customer insights
    comprehensive_customer_view = rfm_segmented \
        .join(clv_predictions.select("customer_id", "prediction").withColumnRenamed("prediction", "predicted_clv"), "customer_id", "left") \
        .join(clustered_customers.select("customer_id", "prediction", "cluster_description").withColumnRenamed("prediction", "cluster_id"), "customer_id", "left") \
        .join(behavior_analysis, "customer_id", "left")
    
    # Calculate segment summaries
    segment_summary = comprehensive_customer_view.groupBy("customer_segment").agg(
        count("customer_id").alias("customer_count"),
        avg("monetary").alias("avg_revenue_per_customer"),
        sum("monetary").alias("total_segment_revenue"),
        avg("frequency").alias("avg_purchase_frequency"),
        avg("predicted_clv").alias("avg_predicted_clv"),
        min("recency").alias("min_recency"),
        max("recency").alias("max_recency")
    ).orderBy(desc("total_segment_revenue"))
    
    # Calculate cluster summaries
    cluster_summary = comprehensive_customer_view.groupBy("cluster_description").agg(
        count("customer_id").alias("cluster_size"),
        avg("monetary").alias("avg_cluster_revenue"),
        avg("frequency").alias("avg_cluster_frequency"),
        avg("predicted_clv").alias("avg_cluster_clv")
    ).orderBy(desc("avg_cluster_revenue"))
    
    return comprehensive_customer_view, segment_summary, cluster_summary

def write_results_to_hive(spark, df, table_name, database="customer_analytics"):
    """Write results to Hive table"""
    logger.info(f"Writing to Hive table: {database}.{table_name}")
    
    # Create database if not exists
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {database}")
    
    # Write to Hive table
    df.write \
        .mode("overwrite") \
        .option("path", f"s3://your-data-lake/warehouse/{database}/{table_name}/") \
        .saveAsTable(f"{database}.{table_name}")

def write_to_s3_partitioned(df, output_path, partition_cols=None):
    """Write DataFrame to S3 with partitioning"""
    logger.info(f"Writing partitioned data to: {output_path}")
    
    writer = df.write.mode("overwrite").parquet(output_path)
    
    if partition_cols:
        writer = writer.partitionBy(*partition_cols)
    
    writer.save()

def generate_insights_report(segment_summary, cluster_summary):
    """Generate business insights report"""
    logger.info("Generating business insights report")
    
    print("\n" + "="*80)
    print("CUSTOMER ANALYTICS INSIGHTS REPORT")
    print("="*80)
    
    print("\nTOP CUSTOMER SEGMENTS BY REVENUE:")
    print("-" * 50)
    segment_summary.show(10, truncate=False)
    
    print("\nCUSTOMER CLUSTERS ANALYSIS:")
    print("-" * 40)
    cluster_summary.show(10, truncate=False)
    
    # Additional insights
    total_customers = segment_summary.agg(sum("customer_count")).collect()[0][0]
    total_revenue = segment_summary.agg(sum("total_segment_revenue")).collect()[0][0]
    
    print(f"\nKEY METRICS:")
    print(f"Total Customers Analyzed: {total_customers:,}")
    print(f"Total Revenue: ${total_revenue:,.2f}")
    print(f"Average Revenue per Customer: ${total_revenue/total_customers:,.2f}")
    
    print("\n" + "="*80)

def main():
    """Main application logic"""
    if len(sys.argv) != 3:
        print("Usage: spark-submit customer-analytics-emr.py <input_path> <output_path>")
        print("Example: spark-submit customer-analytics-emr.py s3://bucket/input/ s3://bucket/output/")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Create Spark session
    spark = create_spark_session("EMR-Customer-Analytics")
    
    try:
        # Read data
        transactions_df, customers_df = read_customer_data(spark, input_path)
        
        # Cache frequently used DataFrames
        transactions_df.cache()
        customers_df.cache()
        
        logger.info(f"Loaded {transactions_df.count()} transactions and {customers_df.count()} customers")
        
        # Calculate customer metrics
        customer_metrics = calculate_customer_metrics(transactions_df)
        customer_metrics.cache()
        
        # Perform RFM segmentation
        rfm_segmented = perform_rfm_segmentation(customer_metrics)
        
        # Build CLV prediction model
        clv_predictions, clv_model, rmse = build_clv_prediction_model(customer_metrics, transactions_df)
        
        # Perform customer clustering
        clustered_customers = perform_customer_clustering(customer_metrics)
        
        # Analyze customer behavior
        behavior_analysis = analyze_customer_behavior(transactions_df, customers_df)
        
        # Create comprehensive dashboard data
        comprehensive_view, segment_summary, cluster_summary = create_customer_dashboard_data(
            rfm_segmented, clv_predictions, clustered_customers, behavior_analysis
        )
        
        # Write results to Hive tables
        write_results_to_hive(spark, comprehensive_view, "customer_comprehensive_view")
        write_results_to_hive(spark, segment_summary, "customer_segment_summary")
        write_results_to_hive(spark, cluster_summary, "customer_cluster_summary")
        write_results_to_hive(spark, rfm_segmented, "customer_rfm_analysis")
        
        # Write results to S3
        write_to_s3_partitioned(
            comprehensive_view, 
            f"{output_path}/customer_analysis/comprehensive_view",
            ["customer_segment"]
        )
        
        write_to_s3_partitioned(
            rfm_segmented,
            f"{output_path}/customer_analysis/rfm_segmentation",
            ["customer_segment"]
        )
        
        segment_summary.coalesce(1).write.mode("overwrite").parquet(f"{output_path}/customer_analysis/segment_summary")
        cluster_summary.coalesce(1).write.mode("overwrite").parquet(f"{output_path}/customer_analysis/cluster_summary")
        
        # Generate insights report
        generate_insights_report(segment_summary, cluster_summary)
        
        logger.info("Customer analytics pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Application failed with error: {str(e)}")
        raise e
    
    finally:
        spark.stop()

if __name__ == "__main__":
    main()