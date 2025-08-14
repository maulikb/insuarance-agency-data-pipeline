#!/bin/bash

# Database Setup Script for Insurance Platform
set -e

echo "🗄️ Setting up Insurance Platform Databases..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U insurance_user -d insurance_db > /dev/null 2>&1; then
        print_status "PostgreSQL is ready!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        print_error "PostgreSQL did not become ready in time"
        exit 1
    fi
    
    echo -n "."
    sleep 2
done

# Initialize Airflow database
print_status "Initializing Airflow database..."
docker-compose exec -T airflow-webserver airflow db init || true

# Create Airflow admin user
print_status "Creating Airflow admin user..."
docker-compose exec -T airflow-webserver airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@insurance.com \
    --password admin123 || print_warning "Admin user might already exist"

# Wait for MinIO to be ready
print_status "Setting up MinIO buckets..."
sleep 5

# Create MinIO buckets using mc client
docker run --rm \
    --network insurance-data-platform_insurance-net \
    -e MC_HOST_minio=http://minioadmin:minioadmin123@minio:9000 \
    minio/mc:latest \
    sh -c "
    mc mb minio/insurance-raw --ignore-existing;
    mc mb minio/insurance-processed --ignore-existing;
    mc mb minio/insurance-archive --ignore-existing;
    mc mb minio/dbt-artifacts --ignore-existing;
    mc policy set public minio/insurance-raw;
    mc policy set public minio/insurance-processed;
    echo 'MinIO buckets created successfully'
    " || print_warning "MinIO setup might have failed"

# Verify database connections
print_status "Verifying database connections..."

# Test PostgreSQL connection
if docker-compose exec -T postgres psql -U insurance_user -d insurance_db -c "SELECT 1;" > /dev/null 2>&1; then
    print_status "PostgreSQL connection verified ✓"
else
    print_error "PostgreSQL connection failed ✗"
    exit 1
fi

# Test Redis connection
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_status "Redis connection verified ✓"
else
    print_error "Redis connection failed ✗"
    exit 1
fi

# Show database statistics
print_status "Database setup completed! Here's the summary:"
echo ""
echo "=== CONNECTION DETAILS ==="
echo "PostgreSQL:"
echo "  Host: localhost:5432"
echo "  Database: insurance_db"
echo "  User: insurance_user"
echo "  Password: insurance_pass"
echo ""
echo "Redis:"
echo "  Host: localhost:6379"
echo ""
echo "MinIO (S3-compatible):"
echo "  Console: http://localhost:9001"
echo "  API: http://localhost:9000"
echo "  Access Key: minioadmin"
echo "  Secret Key: minioadmin123"
echo ""
echo "Airflow:"
echo "  Web UI: http://localhost:8081"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "✅ All databases are ready for use!"