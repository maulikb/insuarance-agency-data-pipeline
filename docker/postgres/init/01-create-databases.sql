-- Create multiple databases for different components
CREATE DATABASE IF NOT EXISTS airflow_db;
CREATE DATABASE IF NOT EXISTS dbt_db;

-- Create schemas in the main insurance database
\c insurance_db;

-- Core insurance schemas
CREATE SCHEMA IF NOT EXISTS raw_data;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Operational schemas
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE insurance_db TO insurance_user;
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO insurance_user;
GRANT ALL PRIVILEGES ON DATABASE dbt_db TO insurance_user;

-- Grant schema permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw_data TO insurance_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO insurance_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA marts TO insurance_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO insurance_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO insurance_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO insurance_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA raw_data GRANT ALL ON TABLES TO insurance_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT ALL ON TABLES TO insurance_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts GRANT ALL ON TABLES TO insurance_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT ALL ON TABLES TO insurance_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON TABLES TO insurance_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA monitoring GRANT ALL ON TABLES TO insurance_user;