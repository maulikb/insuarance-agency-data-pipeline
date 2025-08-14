#!/bin/bash

# Insurance Data Platform Setup Script
set -e

echo "🚀 Setting up Insurance Data Engineering Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install it and try again."
    exit 1
fi

print_status "Docker is running ✓"

# Create necessary directories
print_status "Creating directories..."
mkdir -p data/{raw,processed,sample,backup}
mkdir -p logs/{airflow,spark,kafka}
mkdir -p airflow/logs
mkdir -p notebooks/exploratory
mkdir -p dbt/profiles

# Set permissions for Airflow
print_status "Setting up Airflow permissions..."
echo -e "AIRFLOW_UID=$(id -u)" > .env
echo -e "AIRFLOW_GID=0" >> .env
echo -e "_AIRFLOW_WWW_USER_USERNAME=admin" >> .env
echo -e "_AIRFLOW_WWW_USER_PASSWORD=admin123" >> .env

# Create dbt profiles
print_status "Setting up dbt profiles..."
cat > dbt/profiles/profiles.yml << EOF
insurance_dbt:
  outputs:
    dev:
      type: postgres
      host: localhost
      user: insurance_user
      password: insurance_pass
      port: 5432
      dbname: insurance_db
      schema: staging
      threads: 4
      keepalives_idle: 0
      search_path: "staging,marts,raw_data"
    
    prod:
      type: postgres
      host: localhost
      user: insurance_user
      password: insurance_pass
      port: 5432
      dbname: insurance_db
      schema: marts
      threads: 4
      keepalives_idle: 0
      search_path: "marts,staging,raw_data"
  
  target: dev
EOF

# Create Prometheus configuration
print_status "Setting up monitoring configuration..."
mkdir -p docker/prometheus
cat > docker/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'airflow'
    static_configs:
      - targets: ['airflow-webserver:8080']
    metrics_path: '/admin/metrics/'

  - job_name: 'spark'
    static_configs:
      - targets: ['spark-master:8080']
    metrics_path: '/metrics/master/prometheus/'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka:9092']
EOF

# Create Grafana provisioning
print_status "Setting up Grafana dashboards..."
mkdir -p docker/grafana/provisioning/{dashboards,datasources}

cat > docker/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

cat > docker/grafana/provisioning/dashboards/dashboard.yml << EOF
apiVersion: 1

providers:
  - name: 'insurance-platform'
    orgId: 1
    folder: ''
    folderUid: ''
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

# Make scripts executable
print_status "Making scripts executable..."
find scripts/ -name "*.sh" -exec chmod +x {} \;
find scripts/ -name "*.py" -exec chmod +x {} \;

# Create .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
    print_status "Creating .gitignore..."
    cat > .gitignore << EOF
# Environment
.env
*.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Jupyter Notebook
.ipynb_checkpoints

# Data files
data/raw/*
data/processed/*
data/backup/*
*.csv
*.parquet
*.json
!data/sample/.gitkeep

# Logs
logs/
*.log
airflow/logs/

# Docker volumes
postgres_data/
redis_data/
minio_data/
kafka_data/
grafana_data/
prometheus_data/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Terraform
infrastructure/terraform/*.tfstate
infrastructure/terraform/*.tfstate.*
infrastructure/terraform/.terraform/
infrastructure/terraform/*.tfvars

# Temporary files
tmp/
temp/
EOF
fi

# Create empty files to maintain directory structure
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch data/sample/.gitkeep
touch logs/.gitkeep

print_status "Setup completed successfully! ✓"
echo ""
echo "Next steps:"
echo "1. Run 'make up' to start all services"
echo "2. Run 'make setup-databases' to initialize databases"
echo "3. Run 'make generate-sample-data' to create sample data"
echo "4. Run 'make monitor' to see all dashboard URLs"
echo ""
echo "Happy data engineering! 🎉"