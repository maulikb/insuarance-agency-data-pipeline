# Insurance Data Platform - Step-by-Step Setup Guide

This comprehensive guide walks you through setting up and running the Insurance Data Platform from scratch. Follow these steps carefully to ensure a successful deployment.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Initial Setup](#initial-setup)
5. [Data Generation](#data-generation)
6. [Service Verification](#service-verification)
7. [First Data Pipeline Run](#first-data-pipeline-run)
8. [Troubleshooting](#troubleshooting)
9. [Next Steps](#next-steps)

## 🔧 Prerequisites

### Required Software

**1. Install Docker Desktop**
- Download from: https://www.docker.com/products/docker-desktop
- **Windows**: Docker Desktop for Windows
- **macOS**: Docker Desktop for Mac
- **Linux**: Docker Engine + Docker Compose

**2. Install Git**
- Download from: https://git-scm.com/downloads
- Verify installation: `git --version`

**3. Install Make (if not already installed)**
- **macOS**: `xcode-select --install`
- **Windows**: Install via Chocolatey `choco install make` or use WSL
- **Linux**: `sudo apt-get install make` (Ubuntu/Debian) or `sudo yum install make` (CentOS/RHEL)

**4. Python 3.11+ (Optional for development)**
- Download from: https://www.python.org/downloads/
- Verify: `python3 --version`

## 💻 System Requirements

### Minimum Requirements
- **RAM**: 8GB (16GB recommended)
- **Disk Space**: 10GB free space
- **CPU**: 4 cores recommended
- **OS**: Windows 10+, macOS 10.14+, or modern Linux distribution

### Docker Resource Allocation
Configure Docker Desktop with adequate resources:

1. Open Docker Desktop Settings
2. Go to **Resources** → **Advanced**
3. Set the following:
   - **CPUs**: 4 (or half of your available cores)
   - **Memory**: 6GB minimum (8GB recommended)
   - **Swap**: 2GB
   - **Disk Image Size**: 60GB

## 🚀 Installation Steps

### Step 1: Clone the Repository

```bash
# Clone the project
git clone https://github.com/maulikb/insuarance-agency-data-pipeline.git

# Navigate to project directory
cd insuarance-agency-data-pipeline

# Switch to developer branch
git checkout developer
```

### Step 2: Verify Docker Installation

```bash
# Check Docker version
docker --version
# Expected output: Docker version 20.x.x or higher

# Check Docker Compose version
docker-compose --version
# Expected output: docker-compose version 1.29.x or higher

# Test Docker is running
docker run hello-world
# Should download and run successfully
```

### Step 3: Review Project Structure

```bash
# List project contents
ls -la

# Key directories you should see:
# - api/              # FastAPI application
# - dbt/              # Data transformations
# - docker/           # Docker configurations
# - scripts/          # Utility scripts
# - docker-compose.yml # Main orchestration file
# - Makefile          # Convenience commands
```

## ⚙️ Initial Setup

### Step 4: Start the Platform

```bash
# Method 1: Using Make (recommended)
make up

# Method 2: Using Docker Compose directly
docker-compose up -d
```

**What this does:**
- Downloads required Docker images (first run takes 5-15 minutes)
- Starts PostgreSQL database
- Starts Kafka and Zookeeper
- Starts Redis cache
- Starts Spark cluster
- Starts monitoring services (Prometheus, Grafana)
- Starts Jupyter Lab
- Starts MinIO object storage
- Starts the API service

### Step 5: Monitor Service Startup

```bash
# Check service status
docker-compose ps

# Watch logs for all services
make logs

# Watch logs for specific service
docker-compose logs -f postgres
docker-compose logs -f kafka
```

**Expected Status**: All services should show "Up" status. If any service shows "Exit" or "Restarting", check the troubleshooting section.

### Step 6: Wait for Services to be Ready

Services start in stages. Wait for these key indicators:

```bash
# Check PostgreSQL is ready (should return database list)
docker exec insurance-postgres pg_isready -U insurance_user

# Check Kafka is ready (should return empty topic list initially)
docker exec insurance-kafka kafka-topics --bootstrap-server localhost:9092 --list
```

## 🗄️ Data Generation

### Step 7: Initialize Database Schema

The database schemas should be created automatically, but you can verify:

```bash
# Check if schemas exist
docker exec insurance-postgres psql -U insurance_user -d insurance_db -c "\dn"

# Expected output should show: raw_data, staging, marts, audit, monitoring schemas
```

If schemas don't exist, run:
```bash
# Create schemas manually
docker exec insurance-postgres psql -U insurance_user -d insurance_db -f /docker-entrypoint-initdb.d/01-create-databases.sql
docker exec insurance-postgres psql -U insurance_user -d insurance_db -f /docker-entrypoint-initdb.d/02-insurance-schema.sql
```

### Step 8: Create Kafka Topics

```bash
# Create all required Kafka topics
make create-kafka-topics

# Verify topics were created
docker exec insurance-kafka kafka-topics --bootstrap-server localhost:9092 --list
```

**Expected Topics:**
- policy-events
- claim-events  
- payment-events
- customer-events
- underwriting-decisions
- agent-activities
- data-quality-alerts
- audit-logs
- (Plus corresponding DLQ topics)

### Step 9: Generate Sample Data

```bash
# Generate and load sample insurance data
make generate-data

# This will:
# 1. Generate 10,000 customers
# 2. Generate 25,000 policies  
# 3. Generate 5,000 claims
# 4. Generate agents and payments
# 5. Load all data into PostgreSQL
```

**Monitor Progress:**
```bash
# Watch data generation logs
docker-compose logs -f api

# Check data was loaded
docker exec insurance-postgres psql -U insurance_user -d insurance_db -c "SELECT COUNT(*) FROM raw_data.customers;"
```

## ✅ Service Verification

### Step 10: Access Web Interfaces

Open these URLs in your browser to verify services are running:

| Service | URL | Credentials | Status Check |
|---------|-----|-------------|--------------|
| **Jupyter Lab** | http://localhost:8888 | No password | Should show Jupyter interface |
| **Grafana** | http://localhost:3000 | admin/admin | Should show login page |
| **Kafka UI** | http://localhost:8082 | None | Should show Kafka topics |
| **API Docs** | http://localhost:8000/docs | None | Should show FastAPI docs |
| **Prometheus** | http://localhost:9090 | None | Should show Prometheus UI |
| **MinIO** | http://localhost:9001 | minio/minio123 | Should show MinIO console |

### Step 11: Test Database Connectivity

```bash
# Connect to database and run sample queries
docker exec -it insurance-postgres psql -U insurance_user -d insurance_db

# Once connected, run these SQL commands:
```

```sql
-- Check data counts
SELECT 'customers' as table_name, COUNT(*) as count FROM raw_data.customers
UNION ALL
SELECT 'policies', COUNT(*) FROM raw_data.policies  
UNION ALL
SELECT 'claims', COUNT(*) FROM raw_data.claims;

-- Sample customer data
SELECT customer_id, first_name, last_name, email, customer_type 
FROM raw_data.customers 
LIMIT 5;

-- Exit postgres
\q
```

### Step 12: Test API Endpoints

```bash
# Test API health check
curl http://localhost:8000/health

# Test customers endpoint
curl http://localhost:8000/customers?limit=5

# Test policies endpoint  
curl http://localhost:8000/policies?limit=5
```

## 🔄 First Data Pipeline Run

### Step 13: Run DBT Transformations

```bash
# Run all DBT models
make run-dbt

# Or manually:
docker-compose exec api dbt run --project-dir /app/dbt --profiles-dir /app/dbt/profiles
```

### Step 14: Run Data Quality Checks

```bash
# Execute data quality validation
make data-quality

# Or manually:
docker-compose exec api python /app/scripts/data_quality_checks.py
```

### Step 15: Check Monitoring

1. **Open Grafana** (http://localhost:3000)
   - Login: admin/admin
   - Skip password change for now
   - Look for pre-configured dashboards

2. **Check Prometheus** (http://localhost:9090)
   - Go to Status → Targets
   - All targets should be "UP"

3. **View Kafka Messages** (http://localhost:8082)
   - Browse topics to see any generated events

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue 1: Services Won't Start

**Symptoms:** `docker-compose ps` shows services as "Exited"

**Solutions:**
```bash
# Check Docker resources
docker system df

# Increase Docker memory allocation to 8GB+
# Restart Docker Desktop

# Clean up Docker
docker system prune -a
make clean
make up
```

#### Issue 2: Database Connection Refused

**Symptoms:** Cannot connect to PostgreSQL

**Solutions:**
```bash
# Check if PostgreSQL is running
docker-compose logs postgres

# Wait 30 seconds and try again
sleep 30
docker exec insurance-postgres pg_isready -U insurance_user

# If still failing, restart database
docker-compose restart postgres
```

#### Issue 3: Kafka Topics Not Created

**Symptoms:** Empty topic list or connection errors

**Solutions:**
```bash
# Check Kafka logs
docker-compose logs kafka

# Restart Kafka services
docker-compose restart kafka zookeeper
sleep 30

# Recreate topics
make create-kafka-topics
```

#### Issue 4: Port Conflicts

**Symptoms:** "Port already in use" errors

**Solutions:**
```bash
# Check what's using ports
lsof -i :8000  # API port
lsof -i :5432  # PostgreSQL port  
lsof -i :9092  # Kafka port

# Stop conflicting services or change ports in docker-compose.yml
```

#### Issue 5: Out of Disk Space

**Symptoms:** "No space left on device" errors

**Solutions:**
```bash
# Check Docker disk usage
docker system df

# Clean up unused data
docker system prune -a --volumes

# Remove old containers and images
docker container prune
docker image prune -a
```

#### Issue 6: Memory Issues

**Symptoms:** Services randomly stopping/restarting

**Solutions:**
1. Increase Docker Desktop memory allocation to 8GB+
2. Close other memory-intensive applications
3. Restart Docker Desktop
4. Consider running fewer services initially

## 🎯 Next Steps

Once everything is running successfully:

### Explore the Platform

1. **Data Exploration**
   - Open Jupyter Lab (http://localhost:8888)
   - Create notebooks to explore the insurance data
   - Run sample analysis queries

2. **API Development** 
   - Browse API documentation (http://localhost:8000/docs)
   - Test different endpoints
   - Build custom queries

3. **Data Visualization**
   - Create Grafana dashboards
   - Monitor data quality metrics
   - Set up alerts

4. **Stream Processing**
   - Produce test messages to Kafka topics
   - Monitor message flow in Kafka UI
   - Build real-time processing logic

### Development Workflow

```bash
# Daily development commands
make up          # Start platform
make logs        # Monitor services
make generate-data  # Refresh sample data
make run-dbt     # Run transformations
make down        # Stop platform
```

### Performance Tuning

1. **Database Optimization**
   - Add indexes for frequently queried columns
   - Optimize query performance
   - Configure connection pooling

2. **Kafka Configuration**
   - Adjust partition counts based on throughput
   - Configure retention policies
   - Optimize batch sizes

3. **Resource Allocation**
   - Monitor CPU and memory usage
   - Scale services based on load
   - Optimize Docker resource allocation

### Production Preparation

When ready for production:

1. **Security Hardening**
   - Change all default passwords
   - Set up proper authentication
   - Configure SSL/TLS certificates
   - Implement network security

2. **High Availability**
   - Set up database replication
   - Configure Kafka clusters
   - Implement load balancing
   - Plan disaster recovery

3. **Monitoring & Alerting**
   - Set up comprehensive monitoring
   - Configure alert notifications
   - Implement log aggregation
   - Plan capacity management

## 📞 Getting Help

If you encounter issues not covered here:

1. **Check the logs**: `make logs` or `docker-compose logs [service-name]`
2. **Review the main README.md** for additional documentation
3. **Search existing GitHub issues**: Look for similar problems
4. **Create a new issue**: Include error messages and system info
5. **Join community discussions**: Share experiences and get help

## 🎉 Success Checklist

Mark these items as complete:

- [ ] All Docker services running (`docker-compose ps` shows all "Up")
- [ ] Database schemas created (5 schemas visible)
- [ ] Sample data loaded (10,000+ customers)
- [ ] Kafka topics created (12+ topics)
- [ ] All web interfaces accessible
- [ ] API endpoints responding
- [ ] DBT transformations complete
- [ ] Data quality checks passing
- [ ] Grafana dashboards visible
- [ ] No error messages in logs

**Congratulations!** 🎊 Your Insurance Data Platform is now running successfully!

---

**Time to Complete**: 30-60 minutes (depending on internet speed and hardware)
**Difficulty Level**: Intermediate
**Prerequisites Met**: All required software installed and configured