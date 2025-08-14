-- Insurance Data Schema
-- This script creates the core insurance tables for our data platform

\c insurance_db;

-- Raw Data Schema Tables (Source System Replicas)
-- ==============================================

-- Customers table (from CRM system)
CREATE TABLE IF NOT EXISTS raw_data.customers (
    customer_id UUID PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    ssn VARCHAR(11),
    address_line_1 VARCHAR(255),
    address_line_2 VARCHAR(255),
    city VARCHAR(100),
    state_code VARCHAR(2),
    zip_code VARCHAR(10),
    country VARCHAR(3) DEFAULT 'USA',
    customer_type VARCHAR(20), -- 'individual', 'business'
    risk_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_system VARCHAR(50) DEFAULT 'CRM'
);

-- Policies table (from Policy Management System)
CREATE TABLE IF NOT EXISTS raw_data.policies (
    policy_id UUID PRIMARY KEY,
    customer_id UUID NOT NULL,
    policy_number VARCHAR(50) UNIQUE NOT NULL,
    policy_type VARCHAR(50) NOT NULL, -- 'auto', 'home', 'life', 'health'
    product_name VARCHAR(100),
    policy_status VARCHAR(20) NOT NULL, -- 'active', 'inactive', 'cancelled', 'expired'
    effective_date DATE NOT NULL,
    expiration_date DATE NOT NULL,
    premium_amount DECIMAL(12,2) NOT NULL,
    coverage_amount DECIMAL(12,2),
    deductible_amount DECIMAL(12,2),
    agent_id UUID,
    underwriter_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_system VARCHAR(50) DEFAULT 'PMS',
    FOREIGN KEY (customer_id) REFERENCES raw_data.customers(customer_id)
);

-- Claims table (from Claims Management System)
CREATE TABLE IF NOT EXISTS raw_data.claims (
    claim_id UUID PRIMARY KEY,
    policy_id UUID NOT NULL,
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    claim_type VARCHAR(50) NOT NULL, -- 'auto_accident', 'property_damage', 'theft', etc.
    claim_status VARCHAR(20) NOT NULL, -- 'open', 'investigating', 'approved', 'denied', 'closed'
    incident_date DATE NOT NULL,
    reported_date DATE NOT NULL,
    claim_amount DECIMAL(12,2),
    settlement_amount DECIMAL(12,2),
    adjuster_id UUID,
    description TEXT,
    incident_location VARCHAR(255),
    police_report_number VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_system VARCHAR(50) DEFAULT 'CMS',
    FOREIGN KEY (policy_id) REFERENCES raw_data.policies(policy_id)
);

-- Agents table (from Agent Portal)
CREATE TABLE IF NOT EXISTS raw_data.agents (
    agent_id UUID PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    license_number VARCHAR(50) UNIQUE,
    license_state VARCHAR(2),
    territory VARCHAR(50),
    hire_date DATE,
    commission_rate DECIMAL(5,4),
    manager_id UUID,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'terminated'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_system VARCHAR(50) DEFAULT 'AGENT_PORTAL'
);

-- Payments table (from Billing System)
CREATE TABLE IF NOT EXISTS raw_data.payments (
    payment_id UUID PRIMARY KEY,
    policy_id UUID NOT NULL,
    payment_method VARCHAR(20) NOT NULL, -- 'credit_card', 'bank_transfer', 'check'
    payment_amount DECIMAL(12,2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_status VARCHAR(20) NOT NULL, -- 'pending', 'completed', 'failed', 'refunded'
    transaction_id VARCHAR(100),
    billing_period_start DATE,
    billing_period_end DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_system VARCHAR(50) DEFAULT 'BILLING',
    FOREIGN KEY (policy_id) REFERENCES raw_data.policies(policy_id)
);

-- Underwriting data (from Underwriting System)
CREATE TABLE IF NOT EXISTS raw_data.underwriting_decisions (
    decision_id UUID PRIMARY KEY,
    policy_id UUID NOT NULL,
    underwriter_id UUID,
    decision_type VARCHAR(20) NOT NULL, -- 'approval', 'rejection', 'modification'
    risk_factors JSONB,
    score_details JSONB,
    decision_reason TEXT,
    decision_date DATE NOT NULL,
    premium_adjustment DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_system VARCHAR(50) DEFAULT 'UNDERWRITING',
    FOREIGN KEY (policy_id) REFERENCES raw_data.policies(policy_id)
);

-- Policy documents table (from Document Management)
CREATE TABLE IF NOT EXISTS raw_data.policy_documents (
    document_id UUID PRIMARY KEY,
    policy_id UUID NOT NULL,
    document_type VARCHAR(50) NOT NULL, -- 'policy', 'certificate', 'endorsement'
    document_name VARCHAR(255) NOT NULL,
    document_path VARCHAR(500),
    document_size_bytes BIGINT,
    upload_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_system VARCHAR(50) DEFAULT 'DMS',
    FOREIGN KEY (policy_id) REFERENCES raw_data.policies(policy_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_customers_email ON raw_data.customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON raw_data.customers(created_at);
CREATE INDEX IF NOT EXISTS idx_policies_customer_id ON raw_data.policies(customer_id);
CREATE INDEX IF NOT EXISTS idx_policies_policy_number ON raw_data.policies(policy_number);
CREATE INDEX IF NOT EXISTS idx_policies_policy_type ON raw_data.policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_policies_status ON raw_data.policies(policy_status);
CREATE INDEX IF NOT EXISTS idx_claims_policy_id ON raw_data.claims(policy_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON raw_data.claims(claim_status);
CREATE INDEX IF NOT EXISTS idx_claims_incident_date ON raw_data.claims(incident_date);
CREATE INDEX IF NOT EXISTS idx_payments_policy_id ON raw_data.payments(policy_id);
CREATE INDEX IF NOT EXISTS idx_payments_date ON raw_data.payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_agents_territory ON raw_data.agents(territory);
CREATE INDEX IF NOT EXISTS idx_underwriting_policy_id ON raw_data.underwriting_decisions(policy_id);

-- Audit Schema Tables (for change tracking)
-- ==========================================

-- Generic audit table for tracking all data changes
CREATE TABLE IF NOT EXISTS audit.data_lineage (
    lineage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_table VARCHAR(100) NOT NULL,
    source_id VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    change_reason VARCHAR(255),
    batch_id VARCHAR(100)
);

-- Data quality monitoring table
CREATE TABLE IF NOT EXISTS monitoring.data_quality_results (
    check_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL, -- 'null_check', 'uniqueness', 'range_check', etc.
    check_description TEXT,
    check_result VARCHAR(20) NOT NULL, -- 'passed', 'failed', 'warning'
    error_count INTEGER DEFAULT 0,
    total_records INTEGER DEFAULT 0,
    check_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(100),
    details JSONB
);

-- Pipeline execution monitoring
CREATE TABLE IF NOT EXISTS monitoring.pipeline_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name VARCHAR(100) NOT NULL,
    run_status VARCHAR(20) NOT NULL, -- 'running', 'completed', 'failed'
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    records_processed INTEGER,
    error_message TEXT,
    run_config JSONB
);

-- Create a view for active policies (commonly used)
CREATE OR REPLACE VIEW raw_data.active_policies AS
SELECT 
    p.*,
    c.first_name,
    c.last_name,
    c.email,
    a.first_name as agent_first_name,
    a.last_name as agent_last_name
FROM raw_data.policies p
LEFT JOIN raw_data.customers c ON p.customer_id = c.customer_id
LEFT JOIN raw_data.agents a ON p.agent_id = a.agent_id
WHERE p.policy_status = 'active'
AND p.expiration_date >= CURRENT_DATE;