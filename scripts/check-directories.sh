#!/bin/bash

# Check and create missing directories for Docker volumes

echo "🔍 Checking and creating required directories..."

# Create airflow directories
mkdir -p airflow/dags
mkdir -p airflow/logs
mkdir -p airflow/plugins
mkdir -p airflow/config

# Create data directories
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/staging

# Create spark directories
mkdir -p spark/jobs
mkdir -p spark/batch
mkdir -p spark/streaming

# Create notebook directories
mkdir -p notebooks

# Create test directories
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/e2e

# Create logs directory
mkdir -p logs

# Set proper permissions
chmod 755 airflow/
chmod 755 data/
chmod 755 spark/
chmod 755 notebooks/
chmod 755 tests/
chmod 755 logs/

echo "✅ All required directories created and permissions set!"
echo ""
echo "📁 Directory structure:"
echo "├── airflow/"
echo "│   ├── dags/"
echo "│   ├── logs/"
echo "│   ├── plugins/"
echo "│   └── config/"
echo "├── data/"
echo "│   ├── raw/"
echo "│   ├── processed/"
echo "│   └── staging/"
echo "├── spark/"
echo "│   ├── jobs/"
echo "│   ├── batch/"
echo "│   └── streaming/"
echo "├── notebooks/"
echo "├── tests/"
echo "│   ├── unit/"
echo "│   ├── integration/"
echo "│   └── e2e/"
echo "└── logs/"
echo ""
echo "🚀 Ready to start Docker services!" 