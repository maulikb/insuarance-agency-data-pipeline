"""
Test DAG for Insurance Data Platform
Simple DAG to verify Airflow is working correctly
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator

# Default arguments
default_args = {
    'owner': 'insurance-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'test_insurance_platform',
    default_args=default_args,
    description='Test DAG for Insurance Data Platform',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['test', 'insurance'],
)

def test_function():
    """Simple test function"""
    print("✅ Insurance Data Platform is working!")
    return "Success"

def test_data_connection():
    """Test data connection"""
    print("🔗 Testing data connections...")
    return "Connections OK"

# Define tasks
test_task = PythonOperator(
    task_id='test_platform',
    python_callable=test_function,
    dag=dag,
)

connection_test = PythonOperator(
    task_id='test_connections',
    python_callable=test_data_connection,
    dag=dag,
)

bash_test = BashOperator(
    task_id='bash_test',
    bash_command='echo "Bash operator working!" && date',
    dag=dag,
)

# Set task dependencies
test_task >> connection_test >> bash_test 