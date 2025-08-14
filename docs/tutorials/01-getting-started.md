# Getting Started with the Insurance Data Platform

Welcome to the Insurance Data Engineering Platform! This tutorial will guide you through setting up and running your first data pipeline.

## 🎯 What You'll Learn

By the end of this tutorial, you'll have:
- A fully functional local data engineering environment
- Generated sample insurance data
- Executed your first ETL pipeline
- Created your first dbt models
- Set up monitoring dashboards

## 📋 Prerequisites

Before starting, ensure you have:
- **Docker Desktop** (4GB+ RAM allocated)
- **Git** for version control
- **Python 3.9+** for running scripts
- **Make** for running automation commands
- At least **8GB free disk space**

## 🚀 Quick Start (15 minutes)

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/insurance-data-platform.git
cd insurance-data-platform

# Run initial setup
make setup
```

This command:
- Creates necessary directories
- Sets up environment variables  
- Configures dbt profiles
- Makes scripts executable
- Creates monitoring configurations

### Step 2: Start the Platform

```bash
# Start all services (this may take 5-10 minutes first time)
make up

# Wait for services to be ready
make setup-databases
```

You'll see Docker pulling and starting these services:
- PostgreSQL (database)
- Redis (caching)
- Apache Kafka (streaming)
- Apache Airflow (orchestration)
- Apache Spark (processing)
- Jupyter (analysis)
- Grafana (monitoring)

### Step 3: Generate Sample Data

```bash
# Create realistic insurance data
make generate-sample-data
```

This creates:
- 10,000 customers
- 500 insurance agents
- 25,000+ policies across auto, home, life, health
- 3,750+ claims with settlement tracking
- 300,000+ payment records

### Step 4: Access the Dashboards

```bash
# View all dashboard URLs
make monitor
```

Key URLs:
- **Airflow**: http://localhost:8081 (admin/admin123)
- **Jupyter**: http://localhost:8888?token=insurance123  
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Kafka UI**: http://localhost:8080
- **Spark**: http://localhost:8090

## 🔍 Exploring Your Data

### Database Exploration

Connect to PostgreSQL:
```bash
make shell-postgres
```

Run some queries:
```sql
-- See your generated data
SELECT policy_type, COUNT(*), AVG(premium_amount) 
FROM raw_data.policies 
GROUP BY policy_type;

-- Check claims by severity  
SELECT claim_severity, COUNT(*), SUM(claim_amount)
FROM staging.stg_claims 
GROUP BY claim_severity;
```

### Jupyter Analysis

1. Open Jupyter: http://localhost:8888?token=insurance123
2. Navigate to `work/exploratory/`
3. Create a new notebook and try:

```python
import pandas as pd
import psycopg2

# Connect to database
conn = psycopg2.connect(
    host="postgres", 
    database="insurance_db",
    user="insurance_user", 
    password="insurance_pass"
)

# Load some data
df = pd.read_sql("""
    SELECT c.customer_type, c.risk_category, 
           COUNT(*) as policies,
           AVG(p.premium_amount) as avg_premium
    FROM raw_data.customers c
    JOIN raw_data.policies p ON c.customer_id = p.customer_id  
    WHERE p.policy_status = 'active'
    GROUP BY c.customer_type, c.risk_category
    ORDER BY avg_premium DESC
""", conn)

print(df)
```

## 🔄 Running Your First Pipeline

### 1. Trigger the Main Pipeline

In Airflow (http://localhost:8081):
1. Find the `insurance_data_pipeline` DAG
2. Toggle it ON
3. Click "Trigger DAG"

This pipeline:
- Extracts data from source systems
- Validates data quality
- Transforms data with Spark
- Runs dbt models
- Publishes events to Kafka

### 2. Monitor Pipeline Progress

Watch the DAG run in real-time:
- **Green**: Task completed successfully
- **Blue**: Task is running  
- **Red**: Task failed
- **Orange**: Task is queued

### 3. Check Results

After pipeline completion:

```bash
# Check dbt models were created
cd dbt && dbt run --profiles-dir profiles

# View transformed data
make shell-postgres
```

```sql
-- Check customer dimension
SELECT customer_value_segment, COUNT(*), AVG(total_active_premium)
FROM marts.dim_customers 
GROUP BY customer_value_segment;

-- Check daily metrics
SELECT metric_date, policy_type, new_policies_count, total_premium_amount
FROM marts.fact_daily_metrics 
ORDER BY metric_date DESC 
LIMIT 10;
```

## 📊 Understanding the Data Model

### Raw Layer (`raw_data` schema)
- **customers**: Customer demographics and contact info
- **policies**: Insurance policies with coverage details
- **claims**: Claims submissions and settlements  
- **agents**: Insurance agents and territories
- **payments**: Payment transactions and billing

### Staging Layer (`staging` schema)
- **stg_customers**: Cleaned customer data with derived fields
- **stg_policies**: Standardized policies with business logic
- **stg_claims**: Claims with severity classifications

### Marts Layer (`marts` schema)  
- **dim_customers**: Customer dimension with portfolio metrics
- **fact_daily_metrics**: Daily business metrics by policy type and geography

## 🛠️ Next Steps

Now that your environment is running, explore:

1. **[dbt Development](./02-dbt-development.md)** - Create new data models
2. **[Spark Jobs](./03-spark-processing.md)** - Build custom transformations  
3. **[Streaming Data](./04-kafka-streaming.md)** - Real-time data processing
4. **[Monitoring](./05-monitoring-alerting.md)** - Set up alerts and dashboards
5. **[Cloud Deployment](./06-aws-deployment.md)** - Deploy to AWS

## 🆘 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker resources
docker system df
docker system prune  # if needed

# Restart with fresh containers
make down && make up
```

**Database connection errors:**
```bash
# Wait for PostgreSQL to be ready
make setup-databases

# Check service health
docker-compose ps
```

**Memory issues:**
- Increase Docker Desktop memory to 6-8GB
- Reduce worker count in `docker-compose.yml`

### Getting Help

- Check the [FAQ](../faq.md)
- Review [Architecture Overview](../architecture/overview.md)  
- Join our Slack: #data-engineering
- Create GitHub issues for bugs

## 🎉 Success!

You now have a complete insurance data platform running locally! 

**What you've accomplished:**
✅ Set up enterprise-grade data infrastructure  
✅ Generated realistic insurance datasets  
✅ Executed end-to-end data pipelines  
✅ Created dimensional data models  
✅ Established monitoring and observability  

Ready to dive deeper? Continue with [dbt Development](./02-dbt-development.md) to start building custom analytics models.