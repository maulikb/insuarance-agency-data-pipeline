#!/usr/bin/env python3
"""
Kafka Stream Processing Job

Real-time processing of insurance events from Kafka topics:
1. Policy events processing
2. Claims events processing  
3. Payment events processing
4. Data quality monitoring
5. Real-time aggregations
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta import *
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_spark_session():
    """Create Spark session with Kafka and Delta Lake support"""
    return SparkSession.builder \
        .appName("Insurance Kafka Stream Processor") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.streaming.checkpointLocation", "/opt/bitnami/spark/data/checkpoints") \
        .getOrCreate()

def define_schemas():
    """Define schemas for different event types"""
    
    policy_schema = StructType([
        StructField("event_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("policy_id", StringType(), True),
        StructField("policy_number", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("policy_type", StringType(), True),
        StructField("status", StringType(), True),
        StructField("premium_amount", DoubleType(), True),
        StructField("coverage_amount", DoubleType(), True),
        StructField("agent_id", StringType(), True),
        StructField("territory", StringType(), True),
        StructField("effective_date", StringType(), True),
        StructField("expiration_date", StringType(), True),
        StructField("extraction_date", StringType(), True),
        StructField("metadata", MapType(StringType(), StringType()), True)
    ])
    
    claim_schema = StructType([
        StructField("event_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("claim_id", StringType(), True),
        StructField("claim_number", StringType(), True),
        StructField("policy_id", StringType(), True),
        StructField("claim_type", StringType(), True),
        StructField("status", StringType(), True),
        StructField("claim_amount", DoubleType(), True),
        StructField("settlement_amount", DoubleType(), True),
        StructField("incident_date", StringType(), True),
        StructField("reported_date", StringType(), True),
        StructField("extraction_date", StringType(), True),
        StructField("metadata", MapType(StringType(), StringType()), True)
    ])
    
    payment_schema = StructType([
        StructField("event_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("payment_id", StringType(), True),
        StructField("policy_id", StringType(), True),
        StructField("transaction_id", StringType(), True),
        StructField("payment_method", StringType(), True),
        StructField("payment_amount", DoubleType(), True),
        StructField("payment_date", StringType(), True),
        StructField("payment_status", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("metadata", MapType(StringType(), StringType()), True)
    ])
    
    return {
        'policy': policy_schema,
        'claim': claim_schema, 
        'payment': payment_schema
    }

def read_kafka_stream(spark, topic, schema):
    """Read streaming data from Kafka topic"""
    return spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:29092") \
        .option("subscribe", topic) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load() \
        .select(
            col("key").cast("string"),
            col("value").cast("string"),
            col("timestamp"),
            col("partition"),
            col("offset")
        ) \
        .select(
            col("key"),
            from_json(col("value"), schema).alias("data"),
            col("timestamp").alias("kafka_timestamp"),
            col("partition"),
            col("offset")
        ) \
        .select("data.*", "kafka_timestamp", "partition", "offset")

def process_policy_events(spark, schemas):
    """Process policy events stream"""
    logger.info("Setting up policy events processing...")
    
    policy_stream = read_kafka_stream(spark, "policy-events", schemas['policy'])
    
    # Add processing timestamp and derived fields
    processed_policy_stream = policy_stream \
        .withColumn("processing_timestamp", current_timestamp()) \
        .withColumn("event_date", to_date(col("timestamp"))) \
        .withColumn("event_hour", hour(col("timestamp"))) \
        .withColumn("premium_tier", 
                   when(col("premium_amount") <= 1000, "Basic")
                   .when(col("premium_amount") <= 3000, "Standard")
                   .otherwise("Premium")) \
        .withColumn("is_high_value", col("premium_amount") > 5000)
    
    # Write to Delta Lake with partitioning
    policy_query = processed_policy_stream.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/opt/bitnami/spark/data/checkpoints/policy-events") \
        .partitionBy("event_date", "policy_type") \
        .start("/opt/bitnami/spark/data/delta/streaming/policy_events")
    
    return policy_query

def process_claim_events(spark, schemas):
    """Process claim events stream"""
    logger.info("Setting up claim events processing...")
    
    claim_stream = read_kafka_stream(spark, "claim-events", schemas['claim'])
    
    # Add processing timestamp and derived fields
    processed_claim_stream = claim_stream \
        .withColumn("processing_timestamp", current_timestamp()) \
        .withColumn("event_date", to_date(col("timestamp"))) \
        .withColumn("event_hour", hour(col("timestamp"))) \
        .withColumn("claim_severity",
                   when(col("claim_amount") <= 5000, "Minor")
                   .when(col("claim_amount") <= 25000, "Moderate") 
                   .when(col("claim_amount") <= 100000, "Major")
                   .otherwise("Catastrophic")) \
        .withColumn("is_high_value_claim", col("claim_amount") > 25000) \
        .withColumn("settlement_ratio", 
                   when(col("claim_amount") > 0, col("settlement_amount") / col("claim_amount"))
                   .otherwise(0))
    
    # Write to Delta Lake
    claim_query = processed_claim_stream.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/opt/bitnami/spark/data/checkpoints/claim-events") \
        .partitionBy("event_date", "claim_type") \
        .start("/opt/bitnami/spark/data/delta/streaming/claim_events")
    
    return claim_query

def process_payment_events(spark, schemas):
    """Process payment events stream"""
    logger.info("Setting up payment events processing...")
    
    payment_stream = read_kafka_stream(spark, "payment-events", schemas['payment'])
    
    # Add processing fields
    processed_payment_stream = payment_stream \
        .withColumn("processing_timestamp", current_timestamp()) \
        .withColumn("event_date", to_date(col("timestamp"))) \
        .withColumn("event_hour", hour(col("timestamp"))) \
        .withColumn("is_successful", col("payment_status") == "completed") \
        .withColumn("payment_tier",
                   when(col("payment_amount") <= 200, "Small")
                   .when(col("payment_amount") <= 1000, "Medium")
                   .otherwise("Large"))
    
    # Write to Delta Lake
    payment_query = processed_payment_stream.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/opt/bitnami/spark/data/checkpoints/payment-events") \
        .partitionBy("event_date", "payment_method") \
        .start("/opt/bitnami/spark/data/delta/streaming/payment_events")
    
    return payment_query

def create_real_time_aggregations(spark, schemas):
    """Create real-time aggregations using windowing"""
    logger.info("Setting up real-time aggregations...")
    
    # Policy events aggregation (5-minute windows)
    policy_stream = read_kafka_stream(spark, "policy-events", schemas['policy']) \
        .withColumn("event_timestamp", to_timestamp(col("timestamp")))
    
    policy_aggregates = policy_stream \
        .withWatermark("event_timestamp", "10 minutes") \
        .groupBy(
            window(col("event_timestamp"), "5 minutes"),
            col("policy_type"),
            col("event_type")
        ) \
        .agg(
            count("event_id").alias("event_count"),
            sum("premium_amount").alias("total_premium"),
            avg("premium_amount").alias("avg_premium"),
            countDistinct("policy_id").alias("unique_policies"),
            max("timestamp").alias("latest_event_time")
        ) \
        .withColumn("window_start", col("window.start")) \
        .withColumn("window_end", col("window.end")) \
        .drop("window")
    
    # Write aggregates to Delta
    policy_agg_query = policy_aggregates.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/opt/bitnami/spark/data/checkpoints/policy-aggregates") \
        .start("/opt/bitnami/spark/data/delta/streaming/policy_aggregates_5min")
    
    # Claims events aggregation
    claim_stream = read_kafka_stream(spark, "claim-events", schemas['claim']) \
        .withColumn("event_timestamp", to_timestamp(col("timestamp")))
    
    claim_aggregates = claim_stream \
        .withWatermark("event_timestamp", "10 minutes") \
        .groupBy(
            window(col("event_timestamp"), "5 minutes"),
            col("claim_type"),
            col("status")
        ) \
        .agg(
            count("event_id").alias("event_count"),
            sum("claim_amount").alias("total_claim_amount"),
            avg("claim_amount").alias("avg_claim_amount"),
            countDistinct("claim_id").alias("unique_claims"),
            sum(when(col("claim_amount") > 25000, 1).otherwise(0)).alias("high_value_claims")
        ) \
        .withColumn("window_start", col("window.start")) \
        .withColumn("window_end", col("window.end")) \
        .drop("window")
    
    claim_agg_query = claim_aggregates.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/opt/bitnami/spark/data/checkpoints/claim-aggregates") \
        .start("/opt/bitnami/spark/data/delta/streaming/claim_aggregates_5min")
    
    return policy_agg_query, claim_agg_query

def setup_alerts_and_monitoring(spark, schemas):
    """Set up real-time alerts for critical events"""
    logger.info("Setting up real-time alerts...")
    
    # High-value claim alerts
    claim_stream = read_kafka_stream(spark, "claim-events", schemas['claim'])
    
    high_value_claims = claim_stream \
        .filter(col("claim_amount") > 100000) \
        .withColumn("alert_type", lit("high_value_claim")) \
        .withColumn("alert_timestamp", current_timestamp()) \
        .withColumn("alert_message", 
                   concat(lit("High value claim detected: "), col("claim_number"), 
                         lit(" for amount $"), col("claim_amount")))
    
    # Write alerts to separate stream (could be sent to external alerting system)
    alert_query = high_value_claims \
        .select("alert_type", "alert_timestamp", "alert_message", "claim_id", "policy_id", "claim_amount") \
        .writeStream \
        .format("console") \
        .outputMode("append") \
        .option("truncate", False) \
        .start()
    
    return alert_query

def main():
    """Main streaming application"""
    logger.info("Starting Insurance Kafka Stream Processor...")
    
    # Create Spark session
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    
    # Define schemas
    schemas = define_schemas()
    
    try:
        # Start all streaming queries
        policy_query = process_policy_events(spark, schemas)
        claim_query = process_claim_events(spark, schemas)
        payment_query = process_payment_events(spark, schemas)
        
        # Start aggregations
        policy_agg_query, claim_agg_query = create_real_time_aggregations(spark, schemas)
        
        # Start alerts
        alert_query = setup_alerts_and_monitoring(spark, schemas)
        
        logger.info("All streaming queries started successfully!")
        
        # Print status every 30 seconds
        while True:
            import time
            time.sleep(30)
            
            queries = [policy_query, claim_query, payment_query, policy_agg_query, claim_agg_query, alert_query]
            active_queries = [q for q in queries if q.isActive]
            
            logger.info(f"Active streaming queries: {len(active_queries)}/{len(queries)}")
            
            for i, query in enumerate(active_queries):
                progress = query.lastProgress
                if progress:
                    logger.info(f"Query {i}: Processed {progress.get('inputRowsPerSecond', 0)} rows/sec")
            
            # Check if any query failed
            failed_queries = [q for q in queries if not q.isActive]
            if failed_queries:
                logger.error(f"Failed queries detected: {len(failed_queries)}")
                for q in failed_queries:
                    if q.exception():
                        logger.error(f"Query error: {q.exception()}")
                break
        
        # Wait for all queries to terminate
        for query in [policy_query, claim_query, payment_query, policy_agg_query, claim_agg_query, alert_query]:
            if query.isActive:
                query.awaitTermination()
                
    except KeyboardInterrupt:
        logger.info("Streaming application interrupted by user")
    except Exception as e:
        logger.error(f"Streaming application failed: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()