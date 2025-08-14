"""
Unit tests for the sample data generator
"""

import pytest
import pandas as pd
from datetime import datetime, date
from unittest.mock import Mock, patch
import uuid

# Import the module to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from generate_sample_data import InsuranceDataGenerator, CONFIG


class TestInsuranceDataGenerator:
    """Test class for InsuranceDataGenerator"""
    
    @pytest.fixture
    def generator(self):
        """Create a generator instance for testing"""
        return InsuranceDataGenerator()
    
    def test_generator_initialization(self, generator):
        """Test that generator initializes correctly"""
        assert generator.customers == []
        assert generator.agents == []
        assert generator.policies == []
        assert generator.claims == []
        assert generator.payments == []
        assert generator.underwriting_decisions == []
        assert generator.policy_documents == []
    
    def test_generate_customers_count(self, generator):
        """Test that correct number of customers are generated"""
        customers = generator.generate_customers(10)
        assert len(customers) == 10
        assert len(generator.customers) == 10
    
    def test_generate_customers_structure(self, generator):
        """Test that customers have correct structure"""
        customers = generator.generate_customers(1)
        customer = customers[0]
        
        # Check required fields
        required_fields = [
            'customer_id', 'first_name', 'last_name', 'email',
            'customer_type', 'risk_score', 'created_at', 'source_system'
        ]
        
        for field in required_fields:
            assert field in customer
            assert customer[field] is not None
        
        # Check data types
        assert isinstance(customer['customer_id'], str)
        assert isinstance(customer['risk_score'], float)
        assert isinstance(customer['created_at'], datetime)
        assert customer['source_system'] == 'CRM'
    
    def test_generate_customers_data_validity(self, generator):
        """Test that customer data is valid"""
        customers = generator.generate_customers(100)
        
        for customer in customers:
            # Check email format
            assert '@' in customer['email']
            
            # Check risk score range
            assert 1.0 <= customer['risk_score'] <= 10.0
            
            # Check customer type
            assert customer['customer_type'] in ['individual', 'business']
            
            # Check UUID format
            uuid.UUID(customer['customer_id'])  # Will raise exception if invalid
    
    def test_generate_agents_count(self, generator):
        """Test that correct number of agents are generated"""
        agents = generator.generate_agents(5)
        assert len(agents) == 5
        assert len(generator.agents) == 5
    
    def test_generate_agents_structure(self, generator):
        """Test that agents have correct structure"""
        agents = generator.generate_agents(1)
        agent = agents[0]
        
        required_fields = [
            'agent_id', 'employee_id', 'first_name', 'last_name',
            'email', 'license_number', 'territory', 'commission_rate',
            'status', 'source_system'
        ]
        
        for field in required_fields:
            assert field in agent
            assert agent[field] is not None
        
        # Check data types and values
        assert isinstance(agent['commission_rate'], float)
        assert 0.02 <= agent['commission_rate'] <= 0.15
        assert agent['status'] in ['active', 'inactive']
        assert agent['source_system'] == 'AGENT_PORTAL'
    
    def test_generate_policies(self, generator):
        """Test policy generation"""
        # First generate customers and agents
        generator.generate_customers(10)
        generator.generate_agents(5)
        
        policies = generator.generate_policies()
        
        # Check that policies were generated
        assert len(policies) > 0
        assert len(generator.policies) > 0
        
        # Check policy structure
        policy = policies[0]
        required_fields = [
            'policy_id', 'customer_id', 'policy_number', 'policy_type',
            'policy_status', 'effective_date', 'expiration_date',
            'premium_amount', 'coverage_amount', 'agent_id'
        ]
        
        for field in required_fields:
            assert field in policy
            assert policy[field] is not None
        
        # Check business logic
        assert policy['effective_date'] <= policy['expiration_date']
        assert policy['premium_amount'] > 0
        assert policy['coverage_amount'] > 0
        assert policy['policy_type'] in ['auto', 'home', 'life', 'health']
    
    def test_generate_claims(self, generator):
        """Test claims generation"""
        # Setup dependencies
        generator.generate_customers(10)
        generator.generate_agents(5)
        generator.generate_policies()
        
        claims = generator.generate_claims()
        
        if len(claims) > 0:  # Claims are probabilistic
            claim = claims[0]
            
            required_fields = [
                'claim_id', 'policy_id', 'claim_number', 'claim_type',
                'claim_status', 'incident_date', 'reported_date', 'claim_amount'
            ]
            
            for field in required_fields:
                assert field in claim
                assert claim[field] is not None
            
            # Check business logic
            assert claim['incident_date'] <= claim['reported_date']
            assert claim['claim_amount'] > 0
    
    def test_generate_payments(self, generator):
        """Test payments generation"""
        # Setup dependencies
        generator.generate_customers(5)
        generator.generate_agents(3)
        generator.generate_policies()
        
        payments = generator.generate_payments()
        
        if len(payments) > 0:
            payment = payments[0]
            
            required_fields = [
                'payment_id', 'policy_id', 'payment_method', 'payment_amount',
                'payment_date', 'payment_status'
            ]
            
            for field in required_fields:
                assert field in payment
                assert payment[field] is not None
            
            # Check data validity
            assert payment['payment_amount'] > 0
            assert payment['payment_method'] in ['credit_card', 'bank_transfer', 'check']
            assert payment['payment_status'] in ['completed', 'pending', 'failed']
    
    @patch('pandas.DataFrame.to_csv')
    @patch('os.makedirs')
    def test_save_to_csv(self, mock_makedirs, mock_to_csv, generator):
        """Test CSV export functionality"""
        # Generate some test data
        generator.generate_customers(2)
        generator.generate_agents(1)
        
        generator.save_to_csv()
        
        # Check that directory creation was attempted
        mock_makedirs.assert_called_once_with('data/sample', exist_ok=True)
        
        # Check that to_csv was called for each dataset
        assert mock_to_csv.call_count >= 2  # At least customers and agents
    
    @patch('psycopg2.connect')
    def test_load_to_database_connection(self, mock_connect, generator):
        """Test database connection setup"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Generate minimal test data
        generator.generate_customers(1)
        generator.generate_agents(1)
        
        generator.load_to_database()
        
        # Check that connection was established
        mock_connect.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    def test_generate_all_data_integration(self, generator):
        """Test complete data generation workflow"""
        generator.generate_all_data()
        
        # Check that all data types were generated
        assert len(generator.customers) == CONFIG['customers']
        assert len(generator.agents) == CONFIG['agents']
        assert len(generator.policies) > 0
        
        # Check relationships
        customer_ids = {c['customer_id'] for c in generator.customers}
        agent_ids = {a['agent_id'] for a in generator.agents}
        
        for policy in generator.policies:
            assert policy['customer_id'] in customer_ids
            assert policy['agent_id'] in agent_ids
        
        # Check claims reference valid policies
        policy_ids = {p['policy_id'] for p in generator.policies}
        for claim in generator.claims:
            assert claim['policy_id'] in policy_ids
    
    def test_data_quality_constraints(self, generator):
        """Test data quality constraints"""
        generator.generate_customers(50)
        generator.generate_agents(10)
        generator.generate_policies()
        
        # Check email uniqueness
        emails = [c['email'] for c in generator.customers]
        assert len(emails) == len(set(emails)), "Duplicate emails found"
        
        # Check policy number uniqueness
        policy_numbers = [p['policy_number'] for p in generator.policies]
        assert len(policy_numbers) == len(set(policy_numbers)), "Duplicate policy numbers found"
        
        # Check agent employee ID uniqueness
        employee_ids = [a['employee_id'] for a in generator.agents]
        assert len(employee_ids) == len(set(employee_ids)), "Duplicate employee IDs found"
    
    def test_configuration_respect(self, generator):
        """Test that generator respects configuration parameters"""
        # Test with different customer count
        test_customer_count = 25
        customers = generator.generate_customers(test_customer_count)
        assert len(customers) == test_customer_count
        
        # Test that policies per customer is within configured range
        generator.generate_agents(5)
        generator.generate_policies()
        
        customer_policy_counts = {}
        for policy in generator.policies:
            customer_id = policy['customer_id']
            customer_policy_counts[customer_id] = customer_policy_counts.get(customer_id, 0) + 1
        
        for count in customer_policy_counts.values():
            min_policies, max_policies = CONFIG['policies_per_customer']
            assert min_policies <= count <= max_policies
    
    def test_date_consistency(self, generator):
        """Test date consistency across related records"""
        generator.generate_customers(10)
        generator.generate_agents(5)
        generator.generate_policies()
        generator.generate_claims()
        
        for claim in generator.claims:
            # Find related policy
            policy = next(p for p in generator.policies if p['policy_id'] == claim['policy_id'])
            
            # Claim incident should be within policy period (with some tolerance for edge cases)
            assert claim['incident_date'] >= policy['effective_date'] - pd.Timedelta(days=30)
            
            # Report delay should be reasonable (within 1 year)
            report_delay = (claim['reported_date'] - claim['incident_date']).days
            assert 0 <= report_delay <= 365