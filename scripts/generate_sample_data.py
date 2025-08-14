#!/usr/bin/env python3
"""
Generate sample insurance data for testing and development.
This script creates realistic insurance data including customers, policies, claims, etc.
"""

import uuid
import random
import pandas as pd
from datetime import datetime, timedelta, date
from faker import Faker
import psycopg2
import json
import logging
from typing import Dict, List, Any
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker('en_US')
Faker.seed(42)  # For reproducible data
random.seed(42)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'insurance_db',
    'user': 'insurance_user',
    'password': 'insurance_pass'
}

# Configuration for data generation
CONFIG = {
    'customers': 10000,
    'agents': 500,
    'policies_per_customer': (1, 3),  # min, max policies per customer
    'claims_probability': 0.15,  # 15% of policies will have claims
    'payments_per_policy': (12, 24),  # monthly payments for 1-2 years
    'start_date': datetime(2020, 1, 1),
    'end_date': datetime(2024, 12, 31)
}

class InsuranceDataGenerator:
    def __init__(self):
        self.customers = []
        self.agents = []
        self.policies = []
        self.claims = []
        self.payments = []
        self.underwriting_decisions = []
        self.policy_documents = []
        
    def generate_customers(self, count: int) -> List[Dict[str, Any]]:
        """Generate customer data"""
        logger.info(f"Generating {count} customers...")
        customers = []
        
        for _ in range(count):
            customer_type = random.choice(['individual', 'business'])
            customer = {
                'customer_id': str(uuid.uuid4()),
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'email': fake.unique.email(),
                'phone': fake.numerify('###-###-####'),
                'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=80),
                'ssn': fake.ssn(),
                'address_line_1': fake.street_address(),
                'address_line_2': fake.secondary_address() if random.random() < 0.3 else None,
                'city': fake.city(),
                'state_code': fake.state_abbr(),
                'zip_code': fake.zipcode(),
                'country': 'USA',
                'customer_type': customer_type,
                'risk_score': round(random.uniform(1.0, 10.0), 2),
                'created_at': fake.date_time_between(
                    start_date=CONFIG['start_date'], 
                    end_date=CONFIG['end_date']
                ),
                'source_system': 'CRM'
            }
            customers.append(customer)
        
        self.customers = customers
        return customers
    
    def generate_agents(self, count: int) -> List[Dict[str, Any]]:
        """Generate agent data"""
        logger.info(f"Generating {count} agents...")
        agents = []
        territories = ['North', 'South', 'East', 'West', 'Central', 'Northeast', 'Southeast', 'Northwest', 'Southwest']
        
        for _ in range(count):
            hire_date = fake.date_between(start_date='-10y', end_date='-1y')
            agent = {
                'agent_id': str(uuid.uuid4()),
                'employee_id': f"EMP{fake.unique.random_int(min=10000, max=99999)}",
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'email': fake.unique.email(),
                'phone': fake.numerify('###-###-####'),
                'license_number': f"LIC{fake.unique.random_int(min=100000, max=999999)}",
                'license_state': fake.state_abbr(),
                'territory': random.choice(territories),
                'hire_date': hire_date,
                'commission_rate': round(random.uniform(0.02, 0.15), 4),
                'manager_id': None,  # We'll assign some managers later
                'status': random.choices(['active', 'inactive'], weights=[0.9, 0.1])[0],
                'created_at': hire_date,
                'source_system': 'AGENT_PORTAL'
            }
            agents.append(agent)
        
        # Assign some agents as managers to others
        manager_count = count // 10  # 10% are managers
        managers = random.sample(agents, manager_count)
        
        for agent in agents:
            if agent not in managers and random.random() < 0.8:  # 80% have managers
                agent['manager_id'] = random.choice(managers)['agent_id']
        
        self.agents = agents
        return agents
    
    def generate_policies(self) -> List[Dict[str, Any]]:
        """Generate policy data"""
        logger.info("Generating policies...")
        policies = []
        policy_types = {
            'auto': {'min_premium': 800, 'max_premium': 3000, 'min_coverage': 25000, 'max_coverage': 500000},
            'home': {'min_premium': 1200, 'max_premium': 5000, 'min_coverage': 100000, 'max_coverage': 1000000},
            'life': {'min_premium': 300, 'max_premium': 2000, 'min_coverage': 50000, 'max_coverage': 2000000},
            'health': {'min_premium': 2400, 'max_premium': 8000, 'min_coverage': 10000, 'max_coverage': 100000}
        }
        
        policy_counter = 1
        
        for customer in self.customers:
            # Each customer gets 1-3 policies
            num_policies = random.randint(*CONFIG['policies_per_customer'])
            customer_policies = random.sample(list(policy_types.keys()), 
                                            min(num_policies, len(policy_types)))
            
            for policy_type in customer_policies:
                type_config = policy_types[policy_type]
                effective_date = fake.date_between(
                    start_date=customer['created_at'].date(),
                    end_date=datetime.now().date()
                )
                
                policy = {
                    'policy_id': str(uuid.uuid4()),
                    'customer_id': customer['customer_id'],
                    'policy_number': f"POL{policy_counter:08d}",
                    'policy_type': policy_type,
                    'product_name': f"{policy_type.title()} Protection Plan",
                    'policy_status': random.choices(
                        ['active', 'inactive', 'cancelled', 'expired'],
                        weights=[0.7, 0.1, 0.1, 0.1]
                    )[0],
                    'effective_date': effective_date,
                    'expiration_date': effective_date + timedelta(days=365),
                    'premium_amount': round(random.uniform(
                        type_config['min_premium'], 
                        type_config['max_premium']
                    ), 2),
                    'coverage_amount': round(random.uniform(
                        type_config['min_coverage'], 
                        type_config['max_coverage']
                    ), 2),
                    'deductible_amount': round(random.uniform(500, 5000), 2),
                    'agent_id': random.choice(self.agents)['agent_id'],
                    'underwriter_id': str(uuid.uuid4()),  # Mock underwriter
                    'created_at': effective_date,
                    'source_system': 'PMS'
                }
                policies.append(policy)
                policy_counter += 1
        
        self.policies = policies
        return policies
    
    def generate_claims(self) -> List[Dict[str, Any]]:
        """Generate claims data"""
        logger.info("Generating claims...")
        claims = []
        claim_types = {
            'auto': ['auto_accident', 'theft', 'vandalism', 'collision', 'comprehensive'],
            'home': ['property_damage', 'theft', 'fire', 'water_damage', 'storm_damage'],
            'life': ['death_benefit', 'disability'],
            'health': ['medical_expense', 'prescription', 'emergency_care', 'specialist_visit']
        }
        
        claim_counter = 1
        
        # Only generate claims for a percentage of policies
        policies_with_claims = random.sample(
            self.policies, 
            int(len(self.policies) * CONFIG['claims_probability'])
        )
        
        for policy in policies_with_claims:
            # Some policies might have multiple claims
            num_claims = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
            
            for _ in range(num_claims):
                incident_date = fake.date_between(
                    start_date=policy['effective_date'],
                    end_date=min(policy['expiration_date'], datetime.now().date())
                )
                reported_date = incident_date + timedelta(days=random.randint(0, 30))
                
                claim_amount = round(random.uniform(1000, min(policy['coverage_amount'] * 0.8, 50000)), 2)
                
                claim = {
                    'claim_id': str(uuid.uuid4()),
                    'policy_id': policy['policy_id'],
                    'claim_number': f"CLM{claim_counter:08d}",
                    'claim_type': random.choice(claim_types[policy['policy_type']]),
                    'claim_status': random.choices(
                        ['open', 'investigating', 'approved', 'denied', 'closed'],
                        weights=[0.1, 0.2, 0.4, 0.1, 0.2]
                    )[0],
                    'incident_date': incident_date,
                    'reported_date': reported_date,
                    'claim_amount': claim_amount,
                    'settlement_amount': round(claim_amount * random.uniform(0.7, 1.0), 2) if random.random() > 0.2 else None,
                    'adjuster_id': str(uuid.uuid4()),  # Mock adjuster
                    'description': fake.text(max_nb_chars=200),
                    'incident_location': f"{fake.city()}, {fake.state_abbr()}",
                    'police_report_number': f"PR{fake.random_int(min=100000, max=999999)}" if random.random() > 0.6 else None,
                    'created_at': reported_date,
                    'source_system': 'CMS'
                }
                claims.append(claim)
                claim_counter += 1
        
        self.claims = claims
        return claims
    
    def generate_payments(self) -> List[Dict[str, Any]]:
        """Generate payment data"""
        logger.info("Generating payments...")
        payments = []
        payment_methods = ['credit_card', 'bank_transfer', 'check']
        
        for policy in self.policies:
            if policy['policy_status'] in ['active', 'expired']:
                # Generate monthly payments
                num_payments = random.randint(*CONFIG['payments_per_policy'])
                monthly_premium = policy['premium_amount'] / 12
                
                start_date = policy['effective_date']
                
                for month in range(num_payments):
                    payment_date = start_date + timedelta(days=30 * month)
                    if payment_date > datetime.now().date():
                        break
                    
                    payment = {
                        'payment_id': str(uuid.uuid4()),
                        'policy_id': policy['policy_id'],
                        'payment_method': random.choice(payment_methods),
                        'payment_amount': round(monthly_premium + random.uniform(-50, 50), 2),
                        'payment_date': payment_date,
                        'payment_status': random.choices(
                            ['completed', 'pending', 'failed'],
                            weights=[0.9, 0.05, 0.05]
                        )[0],
                        'transaction_id': f"TXN{uuid.uuid4().hex[:12].upper()}",
                        'billing_period_start': payment_date - timedelta(days=30),
                        'billing_period_end': payment_date,
                        'created_at': payment_date,
                        'source_system': 'BILLING'
                    }
                    payments.append(payment)
        
        self.payments = payments
        return payments
    
    def generate_underwriting_decisions(self) -> List[Dict[str, Any]]:
        """Generate underwriting decisions"""
        logger.info("Generating underwriting decisions...")
        decisions = []
        
        for policy in self.policies:
            # Not all policies have detailed underwriting records
            if random.random() < 0.7:  # 70% have underwriting records
                risk_factors = {
                    'credit_score': random.randint(300, 850),
                    'claims_history': random.randint(0, 5),
                    'location_risk': random.choice(['low', 'medium', 'high']),
                    'age_factor': random.uniform(0.8, 1.5)
                }
                
                score_details = {
                    'base_score': random.randint(60, 95),
                    'adjustments': {
                        'credit': random.uniform(-10, 10),
                        'claims': random.uniform(-15, 5),
                        'location': random.uniform(-5, 5)
                    }
                }
                
                decision = {
                    'decision_id': str(uuid.uuid4()),
                    'policy_id': policy['policy_id'],
                    'underwriter_id': policy['underwriter_id'],
                    'decision_type': random.choices(
                        ['approval', 'rejection', 'modification'],
                        weights=[0.8, 0.1, 0.1]
                    )[0],
                    'risk_factors': json.dumps(risk_factors),
                    'score_details': json.dumps(score_details),
                    'decision_reason': fake.sentence(),
                    'decision_date': policy['effective_date'],
                    'premium_adjustment': round(random.uniform(-200, 200), 2),
                    'created_at': policy['effective_date'],
                    'source_system': 'UNDERWRITING'
                }
                decisions.append(decision)
        
        self.underwriting_decisions = decisions
        return decisions
    
    def generate_policy_documents(self) -> List[Dict[str, Any]]:
        """Generate policy documents"""
        logger.info("Generating policy documents...")
        documents = []
        document_types = ['policy', 'certificate', 'endorsement']
        
        for policy in self.policies:
            # Each policy gets 1-3 documents
            num_docs = random.randint(1, 3)
            
            for i in range(num_docs):
                doc_type = random.choice(document_types)
                document = {
                    'document_id': str(uuid.uuid4()),
                    'policy_id': policy['policy_id'],
                    'document_type': doc_type,
                    'document_name': f"{policy['policy_number']}_{doc_type}_{i+1}.pdf",
                    'document_path': f"/documents/{policy['policy_type']}/{policy['policy_number']}/{doc_type}_{i+1}.pdf",
                    'document_size_bytes': random.randint(50000, 500000),
                    'upload_date': policy['effective_date'] + timedelta(days=random.randint(0, 30)),
                    'created_at': policy['effective_date'] + timedelta(days=random.randint(0, 30)),
                    'source_system': 'DMS'
                }
                documents.append(document)
        
        self.policy_documents = documents
        return documents
    
    def save_to_csv(self):
        """Save all generated data to CSV files"""
        logger.info("Saving data to CSV files...")
        
        # Ensure data directory exists
        os.makedirs('data/sample', exist_ok=True)
        
        # Convert to DataFrames and save
        datasets = {
            'customers': self.customers,
            'agents': self.agents,
            'policies': self.policies,
            'claims': self.claims,
            'payments': self.payments,
            'underwriting_decisions': self.underwriting_decisions,
            'policy_documents': self.policy_documents
        }
        
        for name, data in datasets.items():
            if data:
                df = pd.DataFrame(data)
                df.to_csv(f'data/sample/{name}.csv', index=False)
                logger.info(f"Saved {len(data)} records to data/sample/{name}.csv")
    
    def load_to_database(self):
        """Load generated data to PostgreSQL database"""
        logger.info("Loading data to database...")
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # Load customers
            logger.info("Loading customers...")
            for customer in self.customers:
                cur.execute("""
                    INSERT INTO raw_data.customers (
                        customer_id, first_name, last_name, email, phone, date_of_birth,
                        ssn, address_line_1, address_line_2, city, state_code, zip_code,
                        country, customer_type, risk_score, created_at, updated_at, source_system
                    ) VALUES (
                        %(customer_id)s, %(first_name)s, %(last_name)s, %(email)s, %(phone)s, 
                        %(date_of_birth)s, %(ssn)s, %(address_line_1)s, %(address_line_2)s, 
                        %(city)s, %(state_code)s, %(zip_code)s, %(country)s, %(customer_type)s,
                        %(risk_score)s, %(created_at)s, %(created_at)s, %(source_system)s
                    ) ON CONFLICT (customer_id) DO NOTHING
                """, customer)
            
            # Load agents
            logger.info("Loading agents...")
            for agent in self.agents:
                cur.execute("""
                    INSERT INTO raw_data.agents (
                        agent_id, employee_id, first_name, last_name, email, phone,
                        license_number, license_state, territory, hire_date, commission_rate,
                        manager_id, status, created_at, updated_at, source_system
                    ) VALUES (
                        %(agent_id)s, %(employee_id)s, %(first_name)s, %(last_name)s, %(email)s,
                        %(phone)s, %(license_number)s, %(license_state)s, %(territory)s, 
                        %(hire_date)s, %(commission_rate)s, %(manager_id)s, %(status)s,
                        %(created_at)s, %(created_at)s, %(source_system)s
                    ) ON CONFLICT (agent_id) DO NOTHING
                """, agent)
            
            # Load policies
            logger.info("Loading policies...")
            for policy in self.policies:
                cur.execute("""
                    INSERT INTO raw_data.policies (
                        policy_id, customer_id, policy_number, policy_type, product_name,
                        policy_status, effective_date, expiration_date, premium_amount,
                        coverage_amount, deductible_amount, agent_id, underwriter_id,
                        created_at, updated_at, source_system
                    ) VALUES (
                        %(policy_id)s, %(customer_id)s, %(policy_number)s, %(policy_type)s,
                        %(product_name)s, %(policy_status)s, %(effective_date)s, %(expiration_date)s,
                        %(premium_amount)s, %(coverage_amount)s, %(deductible_amount)s,
                        %(agent_id)s, %(underwriter_id)s, %(created_at)s, %(created_at)s, %(source_system)s
                    ) ON CONFLICT (policy_id) DO NOTHING
                """, policy)
            
            # Load claims
            logger.info("Loading claims...")
            for claim in self.claims:
                cur.execute("""
                    INSERT INTO raw_data.claims (
                        claim_id, policy_id, claim_number, claim_type, claim_status,
                        incident_date, reported_date, claim_amount, settlement_amount,
                        adjuster_id, description, incident_location, police_report_number,
                        created_at, updated_at, source_system
                    ) VALUES (
                        %(claim_id)s, %(policy_id)s, %(claim_number)s, %(claim_type)s, %(claim_status)s,
                        %(incident_date)s, %(reported_date)s, %(claim_amount)s, %(settlement_amount)s,
                        %(adjuster_id)s, %(description)s, %(incident_location)s, %(police_report_number)s,
                        %(created_at)s, %(created_at)s, %(source_system)s
                    ) ON CONFLICT (claim_id) DO NOTHING
                """, claim)
            
            # Load payments
            logger.info("Loading payments...")
            for payment in self.payments:
                cur.execute("""
                    INSERT INTO raw_data.payments (
                        payment_id, policy_id, payment_method, payment_amount, payment_date,
                        payment_status, transaction_id, billing_period_start, billing_period_end,
                        created_at, updated_at, source_system
                    ) VALUES (
                        %(payment_id)s, %(policy_id)s, %(payment_method)s, %(payment_amount)s,
                        %(payment_date)s, %(payment_status)s, %(transaction_id)s,
                        %(billing_period_start)s, %(billing_period_end)s, %(created_at)s,
                        %(created_at)s, %(source_system)s
                    ) ON CONFLICT (payment_id) DO NOTHING
                """, payment)
            
            # Load underwriting decisions
            logger.info("Loading underwriting decisions...")
            for decision in self.underwriting_decisions:
                cur.execute("""
                    INSERT INTO raw_data.underwriting_decisions (
                        decision_id, policy_id, underwriter_id, decision_type, risk_factors,
                        score_details, decision_reason, decision_date, premium_adjustment,
                        created_at, source_system
                    ) VALUES (
                        %(decision_id)s, %(policy_id)s, %(underwriter_id)s, %(decision_type)s,
                        %(risk_factors)s::jsonb, %(score_details)s::jsonb, %(decision_reason)s,
                        %(decision_date)s, %(premium_adjustment)s, %(created_at)s, %(source_system)s
                    ) ON CONFLICT (decision_id) DO NOTHING
                """, decision)
            
            # Load policy documents
            logger.info("Loading policy documents...")
            for doc in self.policy_documents:
                cur.execute("""
                    INSERT INTO raw_data.policy_documents (
                        document_id, policy_id, document_type, document_name, document_path,
                        document_size_bytes, upload_date, created_at, source_system
                    ) VALUES (
                        %(document_id)s, %(policy_id)s, %(document_type)s, %(document_name)s,
                        %(document_path)s, %(document_size_bytes)s, %(upload_date)s,
                        %(created_at)s, %(source_system)s
                    ) ON CONFLICT (document_id) DO NOTHING
                """, doc)
            
            conn.commit()
            logger.info("Successfully loaded all data to database!")
            
        except Exception as e:
            logger.error(f"Error loading data to database: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
    def generate_all_data(self):
        """Generate all types of data"""
        logger.info("Starting data generation...")
        
        # Generate in order (due to foreign key dependencies)
        self.generate_customers(CONFIG['customers'])
        self.generate_agents(CONFIG['agents'])
        self.generate_policies()
        self.generate_claims()
        self.generate_payments()
        self.generate_underwriting_decisions()
        self.generate_policy_documents()
        
        logger.info("Data generation completed!")
        
        # Print summary
        print("\n" + "="*50)
        print("DATA GENERATION SUMMARY")
        print("="*50)
        print(f"Customers: {len(self.customers):,}")
        print(f"Agents: {len(self.agents):,}")
        print(f"Policies: {len(self.policies):,}")
        print(f"Claims: {len(self.claims):,}")
        print(f"Payments: {len(self.payments):,}")
        print(f"Underwriting Decisions: {len(self.underwriting_decisions):,}")
        print(f"Policy Documents: {len(self.policy_documents):,}")
        print("="*50)

def main():
    """Main function"""
    generator = InsuranceDataGenerator()
    
    # Generate all data
    generator.generate_all_data()
    
    # Save to CSV files
    generator.save_to_csv()
    
    # Load to database
    try:
        generator.load_to_database()
    except Exception as e:
        logger.error(f"Could not load to database: {e}")
        logger.info("Data saved to CSV files in data/sample/ directory")

if __name__ == "__main__":
    main()