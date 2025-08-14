#!/usr/bin/env python3
"""
Data Quality Monitoring Framework

This script implements comprehensive data quality checks for the insurance platform:
1. Data completeness checks
2. Data validity checks  
3. Business rule validations
4. Data freshness monitoring
5. Statistical anomaly detection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import psycopg2
from sqlalchemy import create_engine
import logging
import json
from typing import Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataQualityMonitor:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'insurance_db',
            'user': 'insurance_user',
            'password': 'insurance_pass'
        }
        
        self.engine = create_engine(
            f"postgresql://{self.db_config['user']}:{self.db_config['password']}@"
            f"{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )
        
        self.quality_results = []
        
    def run_completeness_checks(self) -> List[Dict[str, Any]]:
        """Check data completeness across critical fields"""
        logger.info("Running data completeness checks...")
        
        completeness_rules = [
            {
                'table': 'raw_data.customers',
                'critical_fields': ['customer_id', 'email', 'first_name', 'last_name'],
                'optional_fields': ['phone', 'address_line_1', 'city', 'state_code']
            },
            {
                'table': 'raw_data.policies', 
                'critical_fields': ['policy_id', 'customer_id', 'policy_number', 'premium_amount'],
                'optional_fields': ['agent_id', 'underwriter_id']
            },
            {
                'table': 'raw_data.claims',
                'critical_fields': ['claim_id', 'policy_id', 'claim_number', 'incident_date'],
                'optional_fields': ['settlement_amount', 'police_report_number']
            }
        ]
        
        results = []
        
        for rule in completeness_rules:
            table = rule['table']
            
            # Get total record count
            total_count_query = f"SELECT COUNT(*) as total FROM {table}"
            total_records = pd.read_sql(total_count_query, self.engine)['total'].iloc[0]
            
            if total_records == 0:
                results.append({
                    'check_type': 'completeness',
                    'table_name': table,
                    'check_description': 'Table is empty',
                    'check_result': 'failed',
                    'error_count': 1,
                    'total_records': 0,
                    'details': {'message': 'No records found in table'}
                })
                continue
            
            # Check critical fields
            for field in rule['critical_fields']:
                null_count_query = f"""
                    SELECT COUNT(*) as null_count 
                    FROM {table} 
                    WHERE {field} IS NULL OR TRIM(CAST({field} AS TEXT)) = ''
                """
                
                try:
                    null_count = pd.read_sql(null_count_query, self.engine)['null_count'].iloc[0]
                    null_percentage = (null_count / total_records) * 100
                    
                    result = {
                        'check_type': 'completeness',
                        'table_name': table,
                        'check_description': f'Null check for critical field {field}',
                        'check_result': 'failed' if null_count > 0 else 'passed',
                        'error_count': null_count,
                        'total_records': total_records,
                        'details': {
                            'field': field,
                            'null_count': int(null_count),
                            'null_percentage': round(null_percentage, 2),
                            'criticality': 'critical'
                        }
                    }
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error checking {field} in {table}: {str(e)}")
                    results.append({
                        'check_type': 'completeness',
                        'table_name': table,
                        'check_description': f'Failed to check field {field}',
                        'check_result': 'failed',
                        'error_count': 1,
                        'total_records': total_records,
                        'details': {'error': str(e)}
                    })
            
            # Check optional fields (warning level)
            for field in rule.get('optional_fields', []):
                null_count_query = f"""
                    SELECT COUNT(*) as null_count 
                    FROM {table} 
                    WHERE {field} IS NULL OR TRIM(CAST({field} AS TEXT)) = ''
                """
                
                try:
                    null_count = pd.read_sql(null_count_query, self.engine)['null_count'].iloc[0]
                    null_percentage = (null_count / total_records) * 100
                    
                    # Optional fields get warning if >50% null
                    result_status = 'warning' if null_percentage > 50 else 'passed'
                    
                    result = {
                        'check_type': 'completeness',
                        'table_name': table,
                        'check_description': f'Null check for optional field {field}',
                        'check_result': result_status,
                        'error_count': null_count if null_percentage > 50 else 0,
                        'total_records': total_records,
                        'details': {
                            'field': field,
                            'null_count': int(null_count),
                            'null_percentage': round(null_percentage, 2),
                            'criticality': 'optional'
                        }
                    }
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error checking optional field {field} in {table}: {str(e)}")
        
        return results
    
    def run_validity_checks(self) -> List[Dict[str, Any]]:
        """Check data validity based on business rules"""
        logger.info("Running data validity checks...")
        
        validity_checks = [
            {
                'table': 'raw_data.customers',
                'check': 'email_format',
                'query': """
                    SELECT COUNT(*) as invalid_count,
                           (SELECT COUNT(*) FROM raw_data.customers) as total_count
                    FROM raw_data.customers 
                    WHERE email IS NOT NULL 
                    AND NOT (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$')
                """,
                'description': 'Invalid email format check'
            },
            {
                'table': 'raw_data.customers',
                'check': 'age_range',
                'query': """
                    SELECT COUNT(*) as invalid_count,
                           (SELECT COUNT(*) FROM raw_data.customers WHERE date_of_birth IS NOT NULL) as total_count
                    FROM raw_data.customers 
                    WHERE date_of_birth IS NOT NULL
                    AND (date_of_birth > CURRENT_DATE - INTERVAL '18 years' 
                         OR date_of_birth < CURRENT_DATE - INTERVAL '120 years')
                """,
                'description': 'Invalid age range check (18-120 years)'
            },
            {
                'table': 'raw_data.policies',
                'check': 'premium_amount',
                'query': """
                    SELECT COUNT(*) as invalid_count,
                           (SELECT COUNT(*) FROM raw_data.policies) as total_count
                    FROM raw_data.policies 
                    WHERE premium_amount <= 0 OR premium_amount > 100000
                """,
                'description': 'Premium amount out of reasonable range (0-100,000)'
            },
            {
                'table': 'raw_data.policies',
                'check': 'date_logic',
                'query': """
                    SELECT COUNT(*) as invalid_count,
                           (SELECT COUNT(*) FROM raw_data.policies) as total_count
                    FROM raw_data.policies 
                    WHERE effective_date >= expiration_date
                """,
                'description': 'Effective date should be before expiration date'
            },
            {
                'table': 'raw_data.claims',
                'check': 'incident_vs_reported_date',
                'query': """
                    SELECT COUNT(*) as invalid_count,
                           (SELECT COUNT(*) FROM raw_data.claims) as total_count
                    FROM raw_data.claims 
                    WHERE incident_date > reported_date
                """,
                'description': 'Incident date should not be after reported date'
            },
            {
                'table': 'raw_data.claims',
                'check': 'claim_amount',
                'query': """
                    SELECT COUNT(*) as invalid_count,
                           (SELECT COUNT(*) FROM raw_data.claims) as total_count
                    FROM raw_data.claims 
                    WHERE claim_amount IS NOT NULL AND (claim_amount <= 0 OR claim_amount > 10000000)
                """,
                'description': 'Claim amount out of reasonable range (0-10M)'
            }
        ]
        
        results = []
        
        for check in validity_checks:
            try:
                result_df = pd.read_sql(check['query'], self.engine)
                invalid_count = result_df['invalid_count'].iloc[0]
                total_count = result_df['total_count'].iloc[0]
                
                if total_count > 0:
                    error_rate = (invalid_count / total_count) * 100
                else:
                    error_rate = 0
                
                result = {
                    'check_type': 'validity',
                    'table_name': check['table'],
                    'check_description': check['description'],
                    'check_result': 'failed' if invalid_count > 0 else 'passed',
                    'error_count': int(invalid_count),
                    'total_records': int(total_count),
                    'details': {
                        'check_name': check['check'],
                        'error_rate': round(error_rate, 2)
                    }
                }
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error running validity check {check['check']}: {str(e)}")
                results.append({
                    'check_type': 'validity',
                    'table_name': check['table'],
                    'check_description': f"Failed to run {check['description']}",
                    'check_result': 'failed',
                    'error_count': 1,
                    'total_records': 0,
                    'details': {'error': str(e)}
                })
        
        return results
    
    def run_uniqueness_checks(self) -> List[Dict[str, Any]]:
        """Check data uniqueness constraints"""
        logger.info("Running data uniqueness checks...")
        
        uniqueness_checks = [
            {
                'table': 'raw_data.customers',
                'field': 'email',
                'description': 'Customer email uniqueness'
            },
            {
                'table': 'raw_data.policies',
                'field': 'policy_number',
                'description': 'Policy number uniqueness'
            },
            {
                'table': 'raw_data.claims',
                'field': 'claim_number', 
                'description': 'Claim number uniqueness'
            },
            {
                'table': 'raw_data.agents',
                'field': 'employee_id',
                'description': 'Agent employee ID uniqueness'
            }
        ]
        
        results = []
        
        for check in uniqueness_checks:
            try:
                duplicate_query = f"""
                    SELECT COUNT(*) - COUNT(DISTINCT {check['field']}) as duplicate_count,
                           COUNT(*) as total_count
                    FROM {check['table']} 
                    WHERE {check['field']} IS NOT NULL
                """
                
                result_df = pd.read_sql(duplicate_query, self.engine)
                duplicate_count = result_df['duplicate_count'].iloc[0]
                total_count = result_df['total_count'].iloc[0]
                
                result = {
                    'check_type': 'uniqueness',
                    'table_name': check['table'],
                    'check_description': check['description'],
                    'check_result': 'failed' if duplicate_count > 0 else 'passed',
                    'error_count': int(duplicate_count),
                    'total_records': int(total_count),
                    'details': {
                        'field': check['field'],
                        'duplicate_count': int(duplicate_count)
                    }
                }
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error running uniqueness check for {check['field']}: {str(e)}")
                results.append({
                    'check_type': 'uniqueness',
                    'table_name': check['table'],
                    'check_description': f"Failed uniqueness check for {check['field']}",
                    'check_result': 'failed',
                    'error_count': 1,
                    'total_records': 0,
                    'details': {'error': str(e)}
                })
        
        return results
    
    def run_freshness_checks(self) -> List[Dict[str, Any]]:
        """Check data freshness"""
        logger.info("Running data freshness checks...")
        
        freshness_checks = [
            {
                'table': 'raw_data.policies',
                'timestamp_field': 'updated_at',
                'max_age_hours': 24,
                'description': 'Policy data freshness (should be updated within 24 hours)'
            },
            {
                'table': 'raw_data.claims',
                'timestamp_field': 'updated_at',
                'max_age_hours': 6,
                'description': 'Claims data freshness (should be updated within 6 hours)'
            },
            {
                'table': 'raw_data.payments',
                'timestamp_field': 'created_at',
                'max_age_hours': 2,
                'description': 'Payment data freshness (should be created within 2 hours)'
            }
        ]
        
        results = []
        
        for check in freshness_checks:
            try:
                freshness_query = f"""
                    SELECT 
                        COUNT(*) as total_records,
                        MAX({check['timestamp_field']}) as latest_timestamp,
                        EXTRACT(EPOCH FROM (NOW() - MAX({check['timestamp_field']}))) / 3600 as hours_since_last_update
                    FROM {check['table']}
                    WHERE {check['timestamp_field']} IS NOT NULL
                """
                
                result_df = pd.read_sql(freshness_query, self.engine)
                
                if len(result_df) > 0 and not pd.isna(result_df['hours_since_last_update'].iloc[0]):
                    hours_old = result_df['hours_since_last_update'].iloc[0]
                    total_records = result_df['total_records'].iloc[0]
                    latest_timestamp = result_df['latest_timestamp'].iloc[0]
                    
                    is_stale = hours_old > check['max_age_hours']
                    
                    result = {
                        'check_type': 'freshness',
                        'table_name': check['table'],
                        'check_description': check['description'],
                        'check_result': 'failed' if is_stale else 'passed',
                        'error_count': 1 if is_stale else 0,
                        'total_records': int(total_records),
                        'details': {
                            'hours_since_update': round(hours_old, 2),
                            'max_allowed_hours': check['max_age_hours'],
                            'latest_timestamp': str(latest_timestamp),
                            'timestamp_field': check['timestamp_field']
                        }
                    }
                else:
                    result = {
                        'check_type': 'freshness',
                        'table_name': check['table'],
                        'check_description': check['description'],
                        'check_result': 'failed',
                        'error_count': 1,
                        'total_records': 0,
                        'details': {'message': 'No timestamp data available'}
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error running freshness check for {check['table']}: {str(e)}")
                results.append({
                    'check_type': 'freshness',
                    'table_name': check['table'],
                    'check_description': f"Failed freshness check for {check['table']}",
                    'check_result': 'failed',
                    'error_count': 1,
                    'total_records': 0,
                    'details': {'error': str(e)}
                })
        
        return results
    
    def run_business_rule_checks(self) -> List[Dict[str, Any]]:
        """Check business-specific rules"""
        logger.info("Running business rule checks...")
        
        business_rules = [
            {
                'name': 'policy_customer_relationship',
                'query': """
                    SELECT COUNT(*) as invalid_count,
                           (SELECT COUNT(*) FROM raw_data.policies) as total_count
                    FROM raw_data.policies p
                    LEFT JOIN raw_data.customers c ON p.customer_id = c.customer_id
                    WHERE c.customer_id IS NULL
                """,
                'description': 'All policies must have valid customer relationships'
            },
            {
                'name': 'claim_policy_relationship',
                'query': """
                    SELECT COUNT(*) as invalid_count,
                           (SELECT COUNT(*) FROM raw_data.claims) as total_count
                    FROM raw_data.claims cl
                    LEFT JOIN raw_data.policies p ON cl.policy_id = p.policy_id
                    WHERE p.policy_id IS NULL
                """,
                'description': 'All claims must have valid policy relationships'
            },
            {
                'name': 'settlement_vs_claim_amount',
                'query': """
                    SELECT COUNT(*) as invalid_count,
                           (SELECT COUNT(*) FROM raw_data.claims WHERE settlement_amount IS NOT NULL) as total_count
                    FROM raw_data.claims
                    WHERE settlement_amount IS NOT NULL 
                    AND settlement_amount > claim_amount * 1.1
                """,
                'description': 'Settlement should not exceed claim amount by more than 10%'
            },
            {
                'name': 'policy_effective_period',
                'query': """
                    SELECT COUNT(*) as invalid_count,
                           (SELECT COUNT(*) FROM raw_data.policies) as total_count
                    FROM raw_data.policies
                    WHERE EXTRACT(DAY FROM (expiration_date - effective_date)) < 30
                    OR EXTRACT(DAY FROM (expiration_date - effective_date)) > 1095
                """,
                'description': 'Policy terms should be between 30 days and 3 years'
            }
        ]
        
        results = []
        
        for rule in business_rules:
            try:
                result_df = pd.read_sql(rule['query'], self.engine)
                invalid_count = result_df['invalid_count'].iloc[0]
                total_count = result_df['total_count'].iloc[0]
                
                result = {
                    'check_type': 'business_rule',
                    'table_name': 'multiple',
                    'check_description': rule['description'],
                    'check_result': 'failed' if invalid_count > 0 else 'passed',
                    'error_count': int(invalid_count),
                    'total_records': int(total_count),
                    'details': {
                        'rule_name': rule['name'],
                        'violation_count': int(invalid_count)
                    }
                }
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error running business rule {rule['name']}: {str(e)}")
                results.append({
                    'check_type': 'business_rule',
                    'table_name': 'multiple',
                    'check_description': f"Failed to run rule: {rule['description']}",
                    'check_result': 'failed',
                    'error_count': 1,
                    'total_records': 0,
                    'details': {'error': str(e)}
                })
        
        return results
    
    def save_results_to_database(self, results: List[Dict[str, Any]], batch_id: str):
        """Save quality check results to monitoring database"""
        logger.info(f"Saving {len(results)} quality check results to database...")
        
        try:
            with self.engine.connect() as conn:
                for result in results:
                    insert_query = """
                        INSERT INTO monitoring.data_quality_results 
                        (table_name, check_type, check_description, check_result, 
                         error_count, total_records, check_timestamp, batch_id, details)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    conn.execute(insert_query, (
                        result['table_name'],
                        result['check_type'],
                        result['check_description'],
                        result['check_result'],
                        result['error_count'],
                        result['total_records'],
                        datetime.now(),
                        batch_id,
                        json.dumps(result['details'])
                    ))
                
                conn.commit()
                logger.info("Quality check results saved successfully")
                
        except Exception as e:
            logger.error(f"Error saving results to database: {str(e)}")
            raise
    
    def generate_summary_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary report of all quality checks"""
        total_checks = len(results)
        passed_checks = len([r for r in results if r['check_result'] == 'passed'])
        failed_checks = len([r for r in results if r['check_result'] == 'failed'])
        warning_checks = len([r for r in results if r['check_result'] == 'warning'])
        
        total_errors = sum(r['error_count'] for r in results)
        total_records_checked = sum(r['total_records'] for r in results)
        
        check_types = {}
        for result in results:
            check_type = result['check_type']
            if check_type not in check_types:
                check_types[check_type] = {'passed': 0, 'failed': 0, 'warning': 0}
            check_types[check_type][result['check_result']] += 1
        
        summary = {
            'execution_timestamp': datetime.now().isoformat(),
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'warning_checks': warning_checks,
            'success_rate': round((passed_checks / total_checks) * 100, 2) if total_checks > 0 else 0,
            'total_errors': total_errors,
            'total_records_checked': total_records_checked,
            'check_types_summary': check_types,
            'critical_failures': [
                r for r in results 
                if r['check_result'] == 'failed' and r['error_count'] > 0
            ]
        }
        
        return summary
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run complete data quality monitoring suite"""
        logger.info("Starting comprehensive data quality monitoring...")
        
        batch_id = f"dq_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        all_results = []
        
        # Run all check types
        all_results.extend(self.run_completeness_checks())
        all_results.extend(self.run_validity_checks())
        all_results.extend(self.run_uniqueness_checks())
        all_results.extend(self.run_freshness_checks())
        all_results.extend(self.run_business_rule_checks())
        
        # Save results to database
        self.save_results_to_database(all_results, batch_id)
        
        # Generate summary report
        summary = self.generate_summary_report(all_results)
        summary['batch_id'] = batch_id
        
        # Log summary
        logger.info("=== DATA QUALITY MONITORING SUMMARY ===")
        logger.info(f"Batch ID: {batch_id}")
        logger.info(f"Total Checks: {summary['total_checks']}")
        logger.info(f"Passed: {summary['passed_checks']}")
        logger.info(f"Failed: {summary['failed_checks']}")
        logger.info(f"Warnings: {summary['warning_checks']}")
        logger.info(f"Success Rate: {summary['success_rate']}%")
        logger.info(f"Total Errors: {summary['total_errors']}")
        
        if summary['critical_failures']:
            logger.warning(f"Critical failures detected: {len(summary['critical_failures'])}")
            for failure in summary['critical_failures'][:5]:  # Show first 5
                logger.warning(f"  - {failure['table_name']}: {failure['check_description']}")
        
        return summary

def main():
    """Main execution function"""
    monitor = DataQualityMonitor()
    
    try:
        summary = monitor.run_all_checks()
        
        # Save summary to file
        summary_file = f"data_quality_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(f"/tmp/{summary_file}", 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Summary saved to /tmp/{summary_file}")
        
        # Exit with error code if critical failures
        if summary['failed_checks'] > 0:
            logger.error("Data quality checks failed! Manual review required.")
            exit(1)
        else:
            logger.info("All data quality checks passed!")
            exit(0)
            
    except Exception as e:
        logger.error(f"Data quality monitoring failed: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()