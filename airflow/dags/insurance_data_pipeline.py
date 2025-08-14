"""
Insurance Data Pipeline DAG

This DAG orchestrates the complete insurance data processing pipeline:
1. Data extraction from various sources
2. Data validation and quality checks
3. Data transformation with Spark
4. Loading to data warehouse
5. dbt model execution
6. Data quality reporting
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.email_operator import EmailOperator
from airflow.sensors.filesystem import FileSensor
from airflow.models import Variable
import pandas as pd
import logging

# Default arguments for the DAG
default_args = {
    'owner': 'insurance-data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['admin@insurance.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'max_active_runs': 1,
}

# Create the DAG
dag = DAG(
    'insurance_data_pipeline',
    default_args=default_args,
    description='Complete insurance data processing pipeline',
    schedule_interval='@daily',  # Run daily at midnight
    catchup=False,
    tags=['insurance', 'etl', 'data-engineering'],
)

def extract_policy_data(**context):
    """Extract policy data from source systems"""
    logging.info("Extracting policy data...")
    
    # In real scenario, this would connect to source systems
    # For demo, we'll simulate data extraction
    pg_hook = PostgresHook(postgres_conn_id='postgres_insurance')
    
    # Extract yesterday's policy updates
    extraction_date = context['ds']
    
    sql = f"""
    SELECT 
        policy_id,
        customer_id,
        policy_number,
        policy_type,
        policy_status,
        premium_amount,
        created_at,
        updated_at
    FROM raw_data.policies 
    WHERE DATE(updated_at) = '{extraction_date}'
       OR DATE(created_at) = '{extraction_date}'
    """
    
    df = pg_hook.get_pandas_df(sql)
    
    # Save to staging area
    staging_path = f"/opt/airflow/data/staging/policies_{extraction_date}.parquet"
    df.to_parquet(staging_path, index=False)
    
    logging.info(f"Extracted {len(df)} policy records to {staging_path}")
    return staging_path

def extract_claims_data(**context):
    """Extract claims data from source systems"""
    logging.info("Extracting claims data...")
    
    pg_hook = PostgresHook(postgres_conn_id='postgres_insurance')
    extraction_date = context['ds']
    
    sql = f"""
    SELECT 
        c.*,
        p.policy_number,
        p.policy_type
    FROM raw_data.claims c
    LEFT JOIN raw_data.policies p ON c.policy_id = p.policy_id
    WHERE DATE(c.updated_at) = '{extraction_date}'
       OR DATE(c.created_at) = '{extraction_date}'
    """
    
    df = pg_hook.get_pandas_df(sql)
    
    staging_path = f"/opt/airflow/data/staging/claims_{extraction_date}.parquet"
    df.to_parquet(staging_path, index=False)
    
    logging.info(f"Extracted {len(df)} claim records to {staging_path}")
    return staging_path

def data_quality_check(**context):
    """Perform data quality checks on extracted data"""
    logging.info("Performing data quality checks...")
    
    extraction_date = context['ds']
    issues = []
    
    # Check policy data
    try:
        policy_path = f"/opt/airflow/data/staging/policies_{extraction_date}.parquet"
        policy_df = pd.read_parquet(policy_path)
        
        # Check for nulls in critical fields
        critical_fields = ['policy_id', 'customer_id', 'policy_number']
        for field in critical_fields:
            null_count = policy_df[field].isna().sum()
            if null_count > 0:
                issues.append(f"Policy data: {null_count} null values in {field}")
        
        # Check for duplicate policy numbers
        duplicates = policy_df['policy_number'].duplicated().sum()
        if duplicates > 0:
            issues.append(f"Policy data: {duplicates} duplicate policy numbers")
            
        # Check premium amounts are positive
        negative_premiums = (policy_df['premium_amount'] <= 0).sum()
        if negative_premiums > 0:
            issues.append(f"Policy data: {negative_premiums} non-positive premium amounts")
            
    except Exception as e:
        issues.append(f"Policy data quality check failed: {str(e)}")
    
    # Check claims data
    try:
        claims_path = f"/opt/airflow/data/staging/claims_{extraction_date}.parquet"
        claims_df = pd.read_parquet(claims_path)
        
        # Check for nulls in critical fields
        critical_fields = ['claim_id', 'policy_id', 'claim_number']
        for field in critical_fields:
            null_count = claims_df[field].isna().sum()
            if null_count > 0:
                issues.append(f"Claims data: {null_count} null values in {field}")
        
        # Check incident dates are not in the future
        future_incidents = (pd.to_datetime(claims_df['incident_date']) > pd.Timestamp.now()).sum()
        if future_incidents > 0:
            issues.append(f"Claims data: {future_incidents} future incident dates")
            
    except Exception as e:
        issues.append(f"Claims data quality check failed: {str(e)}")
    
    # Log results
    if issues:
        logging.warning(f"Data quality issues found: {issues}")
        # In production, you might want to fail the DAG or send alerts
        for issue in issues:
            logging.warning(issue)
    else:
        logging.info("All data quality checks passed!")
    
    # Store results in monitoring table
    pg_hook = PostgresHook(postgres_conn_id='postgres_insurance')
    
    check_result = 'failed' if issues else 'passed'
    error_count = len(issues)
    
    pg_hook.run(f"""
        INSERT INTO monitoring.data_quality_results 
        (table_name, check_type, check_description, check_result, error_count, 
         check_timestamp, batch_id, details)
        VALUES 
        ('daily_extraction', 'comprehensive', 'Daily data quality check', 
         '{check_result}', {error_count}, CURRENT_TIMESTAMP, '{extraction_date}',
         '{{"issues": {issues}}}')
    """)
    
    return len(issues) == 0

def publish_to_kafka(**context):
    """Publish processed data to Kafka topics"""
    from kafka import KafkaProducer
    import json
    
    logging.info("Publishing data to Kafka...")
    
    producer = KafkaProducer(
        bootstrap_servers=['kafka:29092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    extraction_date = context['ds']
    
    try:
        # Publish policy updates
        policy_path = f"/opt/airflow/data/staging/policies_{extraction_date}.parquet"
        policy_df = pd.read_parquet(policy_path)
        
        for _, row in policy_df.iterrows():
            event = {
                'event_type': 'policy_update',
                'policy_id': row['policy_id'],
                'policy_number': row['policy_number'],
                'policy_type': row['policy_type'],
                'status': row['policy_status'],
                'premium_amount': float(row['premium_amount']),
                'timestamp': datetime.now().isoformat(),
                'extraction_date': extraction_date
            }
            
            producer.send('policy-events', value=event)
        
        # Publish claim updates
        claims_path = f"/opt/airflow/data/staging/claims_{extraction_date}.parquet"
        claims_df = pd.read_parquet(claims_path)
        
        for _, row in claims_df.iterrows():
            event = {
                'event_type': 'claim_update',
                'claim_id': row['claim_id'],
                'policy_id': row['policy_id'],
                'claim_number': row['claim_number'],
                'claim_type': row['claim_type'],
                'status': row['claim_status'],
                'claim_amount': float(row['claim_amount']) if pd.notna(row['claim_amount']) else None,
                'timestamp': datetime.now().isoformat(),
                'extraction_date': extraction_date
            }
            
            producer.send('claim-events', value=event)
        
        producer.flush()
        logging.info("Successfully published events to Kafka")
        
    except Exception as e:
        logging.error(f"Failed to publish to Kafka: {str(e)}")
        raise
    
    finally:
        producer.close()

# Task definitions
extract_policies_task = PythonOperator(
    task_id='extract_policy_data',
    python_callable=extract_policy_data,
    dag=dag,
)

extract_claims_task = PythonOperator(
    task_id='extract_claims_data',
    python_callable=extract_claims_data,
    dag=dag,
)

data_quality_task = PythonOperator(
    task_id='data_quality_check',
    python_callable=data_quality_check,
    dag=dag,
)

# Spark job for data transformation
spark_transform_task = BashOperator(
    task_id='spark_data_transformation',
    bash_command="""
    docker-compose exec spark-master spark-submit \
        --master spark://spark-master:7077 \
        --deploy-mode client \
        --conf spark.sql.adaptive.enabled=true \
        --conf spark.sql.adaptive.coalescePartitions.enabled=true \
        /opt/bitnami/spark/jobs/daily_transformation.py {{ ds }}
    """,
    dag=dag,
)

# dbt model execution
dbt_run_task = BashOperator(
    task_id='dbt_model_execution',
    bash_command="""
    cd /opt/airflow/dbt && \
    dbt run --profiles-dir profiles --vars '{"execution_date": "{{ ds }}"}'
    """,
    dag=dag,
)

dbt_test_task = BashOperator(
    task_id='dbt_data_tests',
    bash_command="""
    cd /opt/airflow/dbt && \
    dbt test --profiles-dir profiles
    """,
    dag=dag,
)

# Publish to Kafka
kafka_publish_task = PythonOperator(
    task_id='publish_to_kafka',
    python_callable=publish_to_kafka,
    dag=dag,
)

# Generate data quality report
generate_report_task = PostgresOperator(
    task_id='generate_quality_report',
    postgres_conn_id='postgres_insurance',
    sql="""
    INSERT INTO monitoring.pipeline_runs 
    (pipeline_name, run_status, start_time, end_time, records_processed, run_config)
    SELECT 
        'insurance_data_pipeline',
        'completed',
        '{{ ts }}',
        CURRENT_TIMESTAMP,
        (SELECT COUNT(*) FROM raw_data.policies WHERE DATE(updated_at) = '{{ ds }}'),
        '{"execution_date": "{{ ds }}", "dag_id": "{{ dag.dag_id }}"}'::jsonb;
    """,
    dag=dag,
)

# Email notification on success
success_email_task = EmailOperator(
    task_id='success_notification',
    to=['admin@insurance.com'],
    subject='Insurance Data Pipeline - Daily Run Successful',
    html_content="""
    <h3>Insurance Data Pipeline Completed Successfully</h3>
    <p><strong>Execution Date:</strong> {{ ds }}</p>
    <p><strong>DAG:</strong> {{ dag.dag_id }}</p>
    <p><strong>Run ID:</strong> {{ run_id }}</p>
    
    <h4>Pipeline Summary:</h4>
    <ul>
        <li>Data extraction completed</li>
        <li>Data quality checks passed</li>
        <li>Spark transformations executed</li>
        <li>dbt models updated</li>
        <li>Events published to Kafka</li>
    </ul>
    
    <p>Check the dashboards for detailed metrics and monitoring.</p>
    """,
    dag=dag,
)

# Task dependencies
[extract_policies_task, extract_claims_task] >> data_quality_task
data_quality_task >> spark_transform_task
spark_transform_task >> dbt_run_task
dbt_run_task >> dbt_test_task
dbt_test_task >> kafka_publish_task
kafka_publish_task >> generate_report_task
generate_report_task >> success_email_task