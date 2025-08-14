#!/usr/bin/env python3
"""
Daily Insurance Data Transformation Job

This Spark job processes daily insurance data:
1. Reads data from staging area
2. Applies business logic transformations
3. Performs data aggregations
4. Writes results to Delta Lake
5. Updates dimensional models
"""

import sys
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta import *
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_spark_session():
    """Create Spark session with Delta Lake support"""
    return SparkSession.builder \
        .appName("Insurance Daily Transformation") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .getOrCreate()

def read_postgres_table(spark, table_name):
    """Read table from PostgreSQL"""
    return spark.read \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://postgres:5432/insurance_db") \
        .option("dbtable", table_name) \
        .option("user", "insurance_user") \
        .option("password", "insurance_pass") \
        .option("driver", "org.postgresql.Driver") \
        .load()

def write_to_delta(df, path, mode="overwrite", partition_cols=None):
    """Write DataFrame to Delta Lake"""
    writer = df.write \
        .format("delta") \
        .mode(mode)
    
    if partition_cols:
        writer = writer.partitionBy(partition_cols)
    
    writer.save(path)

def transform_policy_data(spark, execution_date):
    """Transform policy data with business logic"""
    logger.info("Transforming policy data...")
    
    # Read source data
    policies = read_postgres_table(spark, "raw_data.policies")
    customers = read_postgres_table(spark, "raw_data.customers")
    agents = read_postgres_table(spark, "raw_data.agents")
    
    # Filter for recent data (last 30 days)
    cutoff_date = datetime.strptime(execution_date, '%Y-%m-%d') - timedelta(days=30)
    
    policies_recent = policies.filter(col("updated_at") >= lit(cutoff_date))
    
    # Join with dimensional data
    policy_enriched = policies_recent.alias("p") \
        .join(customers.alias("c"), col("p.customer_id") == col("c.customer_id"), "left") \
        .join(agents.alias("a"), col("p.agent_id") == col("a.agent_id"), "left") \
        .select(
            col("p.*"),
            col("c.first_name").alias("customer_first_name"),
            col("c.last_name").alias("customer_last_name"),
            col("c.email").alias("customer_email"),
            col("c.state_code").alias("customer_state"),
            col("c.customer_type"),
            col("c.risk_score").alias("customer_risk_score"),
            col("a.first_name").alias("agent_first_name"),
            col("a.last_name").alias("agent_last_name"),
            col("a.territory").alias("agent_territory"),
            col("a.commission_rate")
        )
    
    # Add derived columns
    policy_transformed = policy_enriched \
        .withColumn("policy_age_days", 
                   datediff(current_date(), col("effective_date"))) \
        .withColumn("annual_premium", 
                   col("premium_amount")) \
        .withColumn("monthly_premium", 
                   col("premium_amount") / 12) \
        .withColumn("coverage_ratio", 
                   col("coverage_amount") / col("premium_amount")) \
        .withColumn("is_active", 
                   when(col("policy_status") == "active", 1).otherwise(0)) \
        .withColumn("risk_category",
                   when(col("customer_risk_score") <= 3, "Low")
                   .when(col("customer_risk_score") <= 6, "Medium")
                   .otherwise("High")) \
        .withColumn("premium_tier",
                   when(col("premium_amount") <= 1000, "Basic")
                   .when(col("premium_amount") <= 3000, "Standard")
                   .otherwise("Premium")) \
        .withColumn("processing_date", lit(execution_date)) \
        .withColumn("last_updated", current_timestamp())
    
    return policy_transformed

def transform_claims_data(spark, execution_date):
    """Transform claims data with business logic"""
    logger.info("Transforming claims data...")
    
    # Read source data
    claims = read_postgres_table(spark, "raw_data.claims")
    policies = read_postgres_table(spark, "raw_data.policies")
    
    # Filter for recent data
    cutoff_date = datetime.strptime(execution_date, '%Y-%m-%d') - timedelta(days=30)
    claims_recent = claims.filter(col("updated_at") >= lit(cutoff_date))
    
    # Join with policy data
    claims_enriched = claims_recent.alias("c") \
        .join(policies.alias("p"), col("c.policy_id") == col("p.policy_id"), "left") \
        .select(
            col("c.*"),
            col("p.policy_type"),
            col("p.premium_amount"),
            col("p.coverage_amount"),
            col("p.customer_id")
        )
    
    # Add derived columns
    claims_transformed = claims_enriched \
        .withColumn("claim_age_days",
                   datediff(current_date(), col("reported_date"))) \
        .withColumn("report_delay_days",
                   datediff(col("reported_date"), col("incident_date"))) \
        .withColumn("claim_ratio",
                   when(col("coverage_amount") > 0, 
                        col("claim_amount") / col("coverage_amount"))
                   .otherwise(0)) \
        .withColumn("settlement_ratio",
                   when(col("claim_amount") > 0,
                        coalesce(col("settlement_amount"), lit(0)) / col("claim_amount"))
                   .otherwise(0)) \
        .withColumn("is_settled",
                   when(col("settlement_amount").isNotNull(), 1).otherwise(0)) \
        .withColumn("claim_severity",
                   when(col("claim_amount") <= 5000, "Minor")
                   .when(col("claim_amount") <= 25000, "Moderate") 
                   .when(col("claim_amount") <= 100000, "Major")
                   .otherwise("Catastrophic")) \
        .withColumn("processing_date", lit(execution_date)) \
        .withColumn("last_updated", current_timestamp())
    
    return claims_transformed

def create_aggregations(spark, policies_df, claims_df, execution_date):
    """Create daily aggregations"""
    logger.info("Creating daily aggregations...")
    
    # Daily policy metrics
    daily_policy_metrics = policies_df \
        .filter(date_format(col("created_at"), "yyyy-MM-dd") == execution_date) \
        .groupBy("policy_type", "agent_territory", "processing_date") \
        .agg(
            count("policy_id").alias("new_policies"),
            sum("premium_amount").alias("total_premium"),
            avg("premium_amount").alias("avg_premium"),
            sum("coverage_amount").alias("total_coverage"),
            countDistinct("customer_id").alias("unique_customers"),
            sum(col("is_active")).alias("active_policies")
        ) \
        .withColumn("avg_coverage_ratio", col("total_coverage") / col("total_premium")) \
        .withColumn("created_at", current_timestamp())
    
    # Daily claims metrics
    daily_claims_metrics = claims_df \
        .filter(date_format(col("reported_date"), "yyyy-MM-dd") == execution_date) \
        .groupBy("policy_type", "claim_type", "processing_date") \
        .agg(
            count("claim_id").alias("new_claims"),
            sum("claim_amount").alias("total_claim_amount"),
            sum("settlement_amount").alias("total_settlement_amount"),
            avg("claim_amount").alias("avg_claim_amount"),
            avg("report_delay_days").alias("avg_report_delay"),
            sum(col("is_settled")).alias("settled_claims"),
            countDistinct("policy_id").alias("affected_policies")
        ) \
        .withColumn("settlement_rate", 
                   when(col("new_claims") > 0, col("settled_claims") / col("new_claims"))
                   .otherwise(0)) \
        .withColumn("created_at", current_timestamp())
    
    return daily_policy_metrics, daily_claims_metrics

def calculate_kpis(spark, policies_df, claims_df, execution_date):
    """Calculate business KPIs"""
    logger.info("Calculating business KPIs...")
    
    # Policy KPIs
    policy_kpis = policies_df \
        .agg(
            count("policy_id").alias("total_policies"),
            sum("is_active").alias("active_policies"),
            sum("premium_amount").alias("total_premium_portfolio"),
            avg("premium_amount").alias("avg_policy_premium"),
            countDistinct("customer_id").alias("total_customers"),
            countDistinct("agent_id").alias("active_agents")
        ) \
        .withColumn("kpi_date", lit(execution_date)) \
        .withColumn("kpi_type", lit("policy_metrics"))
    
    # Claims KPIs  
    claims_kpis = claims_df \
        .agg(
            count("claim_id").alias("total_claims"),
            sum("is_settled").alias("settled_claims"),
            sum("claim_amount").alias("total_claims_amount"),
            sum("settlement_amount").alias("total_settlements_amount"),
            avg("claim_age_days").alias("avg_claim_age_days"),
            avg("report_delay_days").alias("avg_report_delay_days")
        ) \
        .withColumn("settlement_rate", col("settled_claims") / col("total_claims")) \
        .withColumn("kpi_date", lit(execution_date)) \
        .withColumn("kpi_type", lit("claims_metrics"))
    
    return policy_kpis, claims_kpis

def main():
    """Main transformation job"""
    if len(sys.argv) < 2:
        logger.error("Please provide execution date as argument (YYYY-MM-DD)")
        sys.exit(1)
    
    execution_date = sys.argv[1]
    logger.info(f"Starting daily transformation for {execution_date}")
    
    # Create Spark session
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        # Transform core data
        policies_transformed = transform_policy_data(spark, execution_date)
        claims_transformed = transform_claims_data(spark, execution_date)
        
        # Write transformed data to Delta Lake
        logger.info("Writing policy data to Delta Lake...")
        write_to_delta(
            policies_transformed,
            "/opt/bitnami/spark/data/delta/policies_enriched",
            mode="append",
            partition_cols=["processing_date", "policy_type"]
        )
        
        logger.info("Writing claims data to Delta Lake...")
        write_to_delta(
            claims_transformed,
            "/opt/bitnami/spark/data/delta/claims_enriched", 
            mode="append",
            partition_cols=["processing_date", "policy_type"]
        )
        
        # Create aggregations
        daily_policy_metrics, daily_claims_metrics = create_aggregations(
            spark, policies_transformed, claims_transformed, execution_date
        )
        
        logger.info("Writing daily policy metrics...")
        write_to_delta(
            daily_policy_metrics,
            "/opt/bitnami/spark/data/delta/daily_policy_metrics",
            mode="append",
            partition_cols=["processing_date"]
        )
        
        logger.info("Writing daily claims metrics...")  
        write_to_delta(
            daily_claims_metrics,
            "/opt/bitnami/spark/data/delta/daily_claims_metrics",
            mode="append", 
            partition_cols=["processing_date"]
        )
        
        # Calculate and save KPIs
        policy_kpis, claims_kpis = calculate_kpis(
            spark, policies_transformed, claims_transformed, execution_date
        )
        
        logger.info("Writing business KPIs...")
        write_to_delta(
            policy_kpis,
            "/opt/bitnami/spark/data/delta/business_kpis",
            mode="append",
            partition_cols=["kpi_date"]
        )
        
        write_to_delta(
            claims_kpis, 
            "/opt/bitnami/spark/data/delta/business_kpis",
            mode="append",
            partition_cols=["kpi_date"]
        )
        
        # Print summary statistics
        logger.info("=== TRANSFORMATION SUMMARY ===")
        logger.info(f"Policies processed: {policies_transformed.count()}")
        logger.info(f"Claims processed: {claims_transformed.count()}")
        logger.info(f"Policy metrics records: {daily_policy_metrics.count()}")
        logger.info(f"Claims metrics records: {daily_claims_metrics.count()}")
        
        logger.info("Daily transformation completed successfully!")
        
    except Exception as e:
        logger.error(f"Transformation job failed: {str(e)}")
        raise
        
    finally:
        spark.stop()

if __name__ == "__main__":
    main()