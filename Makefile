.PHONY: help setup up down logs clean test lint format install-deps

# Default target
help: ## Show this help message
	@echo "Insurance Data Engineering Platform - Make Commands"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment Setup
setup: ## Initial project setup
	@echo "🚀 Setting up Insurance Data Platform..."
	@chmod +x scripts/*.sh
	@./scripts/setup.sh

install-deps: ## Install Python dependencies
	@echo "📦 Installing Python dependencies..."
	@pip install -r requirements.txt
	@pip install -r requirements-dev.txt

# Docker Operations
up: ## Start all services
	@echo "🐳 Starting all services..."
	@docker-compose up -d

down: ## Stop all services
	@echo "🛑 Stopping all services..."
	@docker-compose down

restart: down up ## Restart all services

logs: ## Show logs for all services
	@docker-compose logs -f

logs-service: ## Show logs for specific service (usage: make logs-service SERVICE=airflow-webserver)
	@docker-compose logs -f $(SERVICE)

# Database Operations
setup-databases: ## Initialize databases and schemas
	@echo "🗄️ Setting up databases..."
	@./scripts/setup-databases.sh

migrate-db: ## Run database migrations
	@echo "📊 Running database migrations..."
	@cd dbt && dbt run --profiles-dir profiles

seed-data: ## Load seed data
	@echo "🌱 Loading seed data..."
	@cd dbt && dbt seed --profiles-dir profiles

# Data Generation
generate-sample-data: ## Generate sample insurance data
	@echo "📈 Generating sample data..."
	@python scripts/generate_sample_data.py

# Airflow Operations
start-airflow: ## Initialize and start Airflow
	@echo "🌪️ Starting Airflow..."
	@docker-compose exec airflow-webserver airflow db init
	@docker-compose exec airflow-webserver airflow users create \
		--username admin \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@insurance.com \
		--password admin123

# Spark Operations
submit-spark-job: ## Submit a Spark job (usage: make submit-spark-job JOB=policy_etl.py)
	@echo "⚡ Submitting Spark job: $(JOB)"
	@docker-compose exec spark-master spark-submit \
		--master spark://spark-master:7077 \
		--deploy-mode client \
		/opt/bitnami/spark/jobs/$(JOB)

# Kafka Operations
create-kafka-topics: ## Create Kafka topics
	@echo "📡 Creating Kafka topics..."
	@./scripts/create-kafka-topics.sh

produce-test-data: ## Produce test data to Kafka
	@echo "📨 Producing test data to Kafka..."
	@python kafka/producers/test_producer.py

# dbt Operations
dbt-run: ## Run dbt models
	@echo "🔄 Running dbt models..."
	@cd dbt && dbt run --profiles-dir profiles

dbt-test: ## Run dbt tests
	@echo "🧪 Running dbt tests..."
	@cd dbt && dbt test --profiles-dir profiles

dbt-docs: ## Generate and serve dbt documentation
	@echo "📚 Generating dbt documentation..."
	@cd dbt && dbt docs generate --profiles-dir profiles && dbt docs serve --profiles-dir profiles

# Testing
test: ## Run all tests
	@echo "🧪 Running tests..."
	@pytest tests/ -v

test-unit: ## Run unit tests
	@echo "🔬 Running unit tests..."
	@pytest tests/unit/ -v

test-integration: ## Run integration tests
	@echo "🔗 Running integration tests..."
	@pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests
	@echo "🎯 Running end-to-end tests..."
	@pytest tests/e2e/ -v

# Code Quality
lint: ## Run linting checks
	@echo "🔍 Running linting checks..."
	@black --check .
	@flake8 .
	@isort --check-only .

format: ## Format code
	@echo "✨ Formatting code..."
	@black .
	@isort .

mypy: ## Run type checking
	@echo "🔤 Running type checks..."
	@mypy .

# Monitoring
monitor: ## Open monitoring dashboards
	@echo "📊 Opening monitoring dashboards..."
	@echo "Grafana: http://localhost:3000 (admin/admin123)"
	@echo "Airflow: http://localhost:8081 (admin/admin123)"
	@echo "Spark UI: http://localhost:8090"
	@echo "Kafka UI: http://localhost:8080"
	@echo "Jupyter: http://localhost:8888?token=insurance123"

# Infrastructure
terraform-plan: ## Plan Terraform changes
	@echo "🏗️ Planning infrastructure changes..."
	@cd infrastructure/terraform && terraform plan

terraform-apply: ## Apply Terraform changes
	@echo "🏗️ Applying infrastructure changes..."
	@cd infrastructure/terraform && terraform apply

terraform-destroy: ## Destroy Terraform infrastructure
	@echo "💥 Destroying infrastructure..."
	@cd infrastructure/terraform && terraform destroy

# Data Quality
run-data-quality: ## Run data quality checks
	@echo "✅ Running data quality checks..."
	@python scripts/data_quality_checks.py

# Utilities
clean: ## Clean up containers and volumes
	@echo "🧹 Cleaning up..."
	@docker-compose down -v
	@docker system prune -f

clean-data: ## Clean up data files
	@echo "🗑️ Cleaning data files..."
	@rm -rf data/processed/*
	@rm -rf data/raw/*

backup-data: ## Backup database
	@echo "💾 Backing up database..."
	@./scripts/backup-database.sh

restore-data: ## Restore database from backup
	@echo "♻️ Restoring database..."
	@./scripts/restore-database.sh

# Development
dev-setup: setup install-deps up setup-databases generate-sample-data create-kafka-topics ## Complete development setup

shell-postgres: ## Open PostgreSQL shell
	@docker-compose exec postgres psql -U insurance_user -d insurance_db

shell-redis: ## Open Redis shell  
	@docker-compose exec redis redis-cli

shell-spark: ## Open Spark shell
	@docker-compose exec spark-master pyspark

# CI/CD
ci-test: lint test ## Run CI tests

cd-deploy: terraform-apply ## Deploy to cloud

# Learning Resources
tutorials: ## List available tutorials
	@echo "📚 Available tutorials:"
	@find docs/tutorials -name "*.md" | sed 's|docs/tutorials/||' | sort

show-architecture: ## Show architecture diagram
	@echo "🏗️ Architecture Overview:"
	@cat docs/architecture/overview.md