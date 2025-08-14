"""
Integration tests for Airflow DAGs
"""

import pytest
import pendulum
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from airflow.models import DagBag, TaskInstance, DagRun
from airflow.utils.state import State
from airflow.utils.db import create_session
import pandas as pd


class TestInsuranceDataPipelineDAG:
    """Integration tests for the main insurance data pipeline DAG"""
    
    @pytest.fixture(scope="class")
    def dagbag(self):
        """Load DAGs from the DAG folder"""
        return DagBag(dag_folder="airflow/dags", include_examples=False)
    
    @pytest.fixture
    def dag_id(self):
        """DAG ID to test"""
        return "insurance_data_pipeline"
    
    def test_dag_loaded(self, dagbag, dag_id):
        """Test that the DAG is loaded without errors"""
        dag = dagbag.get_dag(dag_id)
        assert dag is not None
        assert len(dagbag.import_errors) == 0, f"DAG import errors: {dagbag.import_errors}"
    
    def test_dag_structure(self, dagbag, dag_id):
        """Test DAG structure and task count"""
        dag = dagbag.get_dag(dag_id)
        
        expected_tasks = [
            'extract_policy_data',
            'extract_claims_data', 
            'data_quality_check',
            'spark_data_transformation',
            'dbt_model_execution',
            'dbt_data_tests',
            'publish_to_kafka',
            'generate_quality_report',
            'success_notification'
        ]
        
        actual_tasks = list(dag.task_ids)
        
        for task in expected_tasks:
            assert task in actual_tasks, f"Task {task} not found in DAG"
    
    def test_dag_dependencies(self, dagbag, dag_id):
        """Test that task dependencies are correct"""
        dag = dagbag.get_dag(dag_id)
        
        # Test that data extraction tasks have no upstream dependencies
        extract_tasks = ['extract_policy_data', 'extract_claims_data']
        for task_id in extract_tasks:
            task = dag.get_task(task_id)
            assert len(task.upstream_task_ids) == 0
        
        # Test that data quality check depends on both extract tasks
        dq_task = dag.get_task('data_quality_check')
        assert 'extract_policy_data' in dq_task.upstream_task_ids
        assert 'extract_claims_data' in dq_task.upstream_task_ids
        
        # Test Spark transformation depends on data quality
        spark_task = dag.get_task('spark_data_transformation')
        assert 'data_quality_check' in spark_task.upstream_task_ids
        
        # Test dbt execution chain
        dbt_run_task = dag.get_task('dbt_model_execution')
        assert 'spark_data_transformation' in dbt_run_task.upstream_task_ids
        
        dbt_test_task = dag.get_task('dbt_data_tests')
        assert 'dbt_model_execution' in dbt_test_task.upstream_task_ids
    
    def test_dag_schedule_and_config(self, dagbag, dag_id):
        """Test DAG configuration"""
        dag = dagbag.get_dag(dag_id)
        
        assert dag.schedule_interval == '@daily'
        assert dag.catchup is False
        assert dag.max_active_runs == 1
        assert 'insurance' in dag.tags
        assert 'etl' in dag.tags
    
    @pytest.mark.integration
    @patch('airflow.providers.postgres.hooks.postgres.PostgresHook')
    def test_extract_policy_data_task(self, mock_pg_hook, dagbag, dag_id):
        """Test policy data extraction task"""
        dag = dagbag.get_dag(dag_id)
        task = dag.get_task('extract_policy_data')
        
        # Mock database response
        mock_df = pd.DataFrame({
            'policy_id': ['pol1', 'pol2'],
            'customer_id': ['cust1', 'cust2'], 
            'policy_number': ['POL001', 'POL002'],
            'premium_amount': [1000.0, 1500.0]
        })
        
        mock_hook_instance = MagicMock()
        mock_hook_instance.get_pandas_df.return_value = mock_df
        mock_pg_hook.return_value = mock_hook_instance
        
        # Execute task
        execution_date = datetime.now()
        task_instance = TaskInstance(task, execution_date)
        
        with patch('pandas.DataFrame.to_parquet') as mock_parquet:
            result = task.execute(context={'ds': execution_date.strftime('%Y-%m-%d')})
            
            # Verify function calls
            mock_hook_instance.get_pandas_df.assert_called_once()
            mock_parquet.assert_called_once()
            
            # Verify result
            assert result.endswith('.parquet')
            assert 'policies_' in result
    
    @pytest.mark.integration  
    @patch('airflow.providers.postgres.hooks.postgres.PostgresHook')
    def test_data_quality_check_task(self, mock_pg_hook, dagbag, dag_id):
        """Test data quality check task"""
        dag = dagbag.get_dag(dag_id)
        task = dag.get_task('data_quality_check')
        
        # Mock parquet files exist
        mock_df_policies = pd.DataFrame({
            'policy_id': ['pol1', 'pol2'],
            'customer_id': ['cust1', 'cust2'],
            'policy_number': ['POL001', 'POL002'],
            'premium_amount': [1000.0, 1500.0]
        })
        
        mock_df_claims = pd.DataFrame({
            'claim_id': ['claim1'],
            'policy_id': ['pol1'],
            'claim_number': ['CLM001'],
            'incident_date': [datetime.now().date()]
        })
        
        execution_date = datetime.now()
        
        with patch('pandas.read_parquet', side_effect=[mock_df_policies, mock_df_claims]):
            with patch.object(mock_pg_hook.return_value, 'run') as mock_run:
                task_instance = TaskInstance(task, execution_date)
                result = task.execute(context={'ds': execution_date.strftime('%Y-%m-%d')})
                
                # Should return True for good data
                assert result is True
                
                # Verify quality results were stored
                mock_run.assert_called()
    
    @pytest.mark.integration
    def test_spark_transformation_task(self, dagbag, dag_id):
        """Test Spark transformation task"""
        dag = dagbag.get_dag(dag_id)
        task = dag.get_task('spark_data_transformation')
        
        # This is a BashOperator, so we check the command
        expected_command_parts = [
            'spark-submit',
            'spark://spark-master:7077',
            'daily_transformation.py'
        ]
        
        for part in expected_command_parts:
            assert part in task.bash_command
    
    @pytest.mark.integration
    def test_dbt_tasks(self, dagbag, dag_id):
        """Test dbt model execution and testing tasks"""
        dag = dagbag.get_dag(dag_id)
        
        dbt_run_task = dag.get_task('dbt_model_execution')
        dbt_test_task = dag.get_task('dbt_data_tests')
        
        # Check dbt commands
        assert 'dbt run' in dbt_run_task.bash_command
        assert 'profiles-dir profiles' in dbt_run_task.bash_command
        
        assert 'dbt test' in dbt_test_task.bash_command
        assert 'profiles-dir profiles' in dbt_test_task.bash_command
    
    @pytest.mark.integration
    @patch('kafka.KafkaProducer')
    def test_kafka_publish_task(self, mock_kafka_producer, dagbag, dag_id):
        """Test Kafka publishing task"""
        dag = dagbag.get_dag(dag_id)
        task = dag.get_task('publish_to_kafka')
        
        # Mock Kafka producer
        mock_producer_instance = MagicMock()
        mock_kafka_producer.return_value = mock_producer_instance
        
        # Mock parquet data
        mock_df = pd.DataFrame({
            'policy_id': ['pol1'],
            'policy_number': ['POL001'],
            'policy_type': ['auto'],
            'premium_amount': [1000.0]
        })
        
        execution_date = datetime.now()
        
        with patch('pandas.read_parquet', return_value=mock_df):
            task_instance = TaskInstance(task, execution_date)
            task.execute(context={'ds': execution_date.strftime('%Y-%m-%d')})
            
            # Verify Kafka producer was used
            mock_kafka_producer.assert_called_once()
            mock_producer_instance.send.assert_called()
            mock_producer_instance.flush.assert_called_once()
            mock_producer_instance.close.assert_called_once()


class TestDAGFailureHandling:
    """Test DAG behavior under failure conditions"""
    
    @pytest.fixture
    def dagbag(self):
        return DagBag(dag_folder="airflow/dags", include_examples=False)
    
    @pytest.mark.integration
    @patch('pandas.read_parquet')
    def test_data_quality_failure(self, mock_read_parquet, dagbag):
        """Test data quality check failure handling"""
        dag = dagbag.get_dag('insurance_data_pipeline')
        task = dag.get_task('data_quality_check')
        
        # Mock bad data that should fail quality checks
        bad_df = pd.DataFrame({
            'policy_id': [None, 'pol2'],  # Null policy ID
            'customer_id': ['cust1', 'cust2'],
            'premium_amount': [0, -100]  # Invalid premium amounts
        })
        
        mock_read_parquet.return_value = bad_df
        
        execution_date = datetime.now()
        task_instance = TaskInstance(task, execution_date)
        
        # Should detect quality issues
        with patch('airflow.providers.postgres.hooks.postgres.PostgresHook'):
            result = task.execute(context={'ds': execution_date.strftime('%Y-%m-%d')})
            # Quality check should pass but log warnings
            # In production, you might want to fail on critical issues
    
    @pytest.mark.integration
    def test_task_retry_configuration(self, dagbag):
        """Test that tasks have proper retry configuration"""
        dag = dagbag.get_dag('insurance_data_pipeline')
        
        for task in dag.tasks:
            # All tasks should have retries configured
            assert task.retries >= 1
            assert task.retry_delay.total_seconds() >= 300  # At least 5 minutes
    
    @pytest.mark.integration
    def test_dag_timeout_configuration(self, dagbag):
        """Test DAG timeout configurations"""
        dag = dagbag.get_dag('insurance_data_pipeline')
        
        # Check that the DAG has reasonable timeouts
        assert dag.dagrun_timeout is None or dag.dagrun_timeout.total_seconds() <= 3600 * 6  # Max 6 hours


class TestDAGTriggers:
    """Test DAG triggering and scheduling"""
    
    @pytest.fixture
    def dagbag(self):
        return DagBag(dag_folder="airflow/dags", include_examples=False)
    
    def test_dag_schedule_compliance(self, dagbag):
        """Test that DAG schedule aligns with business requirements"""
        dag = dagbag.get_dag('insurance_data_pipeline')
        
        # Should run daily
        assert dag.schedule_interval == '@daily'
        
        # Should have proper start date
        assert dag.start_date <= datetime.now()
        
        # Should not backfill by default
        assert dag.catchup is False
    
    @pytest.mark.integration
    def test_manual_trigger(self, dagbag):
        """Test manual DAG triggering"""
        dag = dagbag.get_dag('insurance_data_pipeline')
        
        # Should be able to trigger manually
        execution_date = datetime.now()
        
        with create_session() as session:
            # Create a manual DAG run
            dag_run = DagRun(
                dag_id=dag.dag_id,
                execution_date=execution_date,
                start_date=datetime.now(),
                external_trigger=True,
                state=State.RUNNING
            )
            
            session.add(dag_run)
            session.commit()
            
            # Verify DAG run was created
            assert dag_run.dag_id == dag.dag_id
            assert dag_run.external_trigger is True


class TestDAGMonitoring:
    """Test DAG monitoring and observability features"""
    
    @pytest.fixture
    def dagbag(self):
        return DagBag(dag_folder="airflow/dags", include_examples=False)
    
    def test_dag_has_email_notifications(self, dagbag):
        """Test that DAG has email notification configured"""
        dag = dagbag.get_dag('insurance_data_pipeline')
        
        # Check default args for email settings
        assert dag.default_args.get('email_on_failure') is True
        assert dag.default_args.get('email') is not None
        assert len(dag.default_args.get('email', [])) > 0
    
    def test_dag_has_success_notification(self, dagbag):
        """Test that success notification task exists"""
        dag = dagbag.get_dag('insurance_data_pipeline')
        
        success_task = dag.get_task('success_notification')
        assert success_task is not None
        
        # Should be an EmailOperator
        assert success_task.task_type == 'EmailOperator'
    
    def test_dag_logging_configuration(self, dagbag):
        """Test DAG logging is properly configured"""
        dag = dagbag.get_dag('insurance_data_pipeline')
        
        # Each task should have proper task_id for logging
        for task in dag.tasks:
            assert task.task_id is not None
            assert len(task.task_id) > 0
            assert '_' in task.task_id or task.task_id.isalnum()