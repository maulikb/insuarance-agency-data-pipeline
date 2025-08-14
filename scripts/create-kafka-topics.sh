#!/bin/bash

# Kafka Topics Setup Script
set -e

echo "📡 Creating Kafka topics for Insurance Platform..."

# Colors
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

# Wait for Kafka to be ready
print_status "Waiting for Kafka to be ready..."
for i in {1..60}; do
    if docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; then
        print_status "Kafka is ready!"
        break
    fi
    
    if [ $i -eq 60 ]; then
        print_error "Kafka did not become ready in time"
        exit 1
    fi
    
    echo -n "."
    sleep 2
done

# Create topics function
create_topic() {
    local topic_name=$1
    local partitions=$2
    local replication=$3
    local retention=$4
    
    print_status "Creating topic: $topic_name"
    docker-compose exec -T kafka kafka-topics \
        --bootstrap-server localhost:9092 \
        --create \
        --if-not-exists \
        --topic "$topic_name" \
        --partitions "$partitions" \
        --replication-factor "$replication" \
        --config "retention.ms=$retention" || print_warning "Topic $topic_name might already exist"
}

# Create topics
print_status "Creating Kafka topics..."
create_topic "policy-events" 6 1 604800000
create_topic "claim-events" 6 1 604800000
create_topic "payment-events" 6 1 604800000
create_topic "customer-events" 3 1 2592000000
create_topic "underwriting-decisions" 3 1 2592000000
create_topic "agent-activities" 3 1 604800000
create_topic "data-quality-alerts" 1 1 259200000
create_topic "audit-logs" 1 1 7776000000

# Dead letter queue topics
print_status "Creating dead letter queue topics..."
DLQ_TOPICS=("policy-events-dlq" "claim-events-dlq" "payment-events-dlq" "customer-events-dlq")

for topic in "${DLQ_TOPICS[@]}"; do
    print_status "Creating DLQ topic: $topic"
    docker-compose exec -T kafka kafka-topics \
        --bootstrap-server localhost:9092 \
        --create \
        --if-not-exists \
        --topic "$topic" \
        --partitions 1 \
        --replication-factor 1 \
        --config retention.ms=604800000 || print_warning "DLQ topic $topic might already exist"
done

# Verify topics were created
print_status "Verifying topics..."
echo ""
echo "=== CREATED KAFKA TOPICS ==="
docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list

# Show topic configurations
echo ""
echo "=== TOPIC CONFIGURATIONS ==="
TOPIC_LIST=("policy-events" "claim-events" "payment-events" "customer-events" "underwriting-decisions" "agent-activities" "data-quality-alerts" "audit-logs")
for topic in "${TOPIC_LIST[@]}"; do
    echo "Topic: $topic"
    docker-compose exec -T kafka kafka-topics \
        --bootstrap-server localhost:9092 \
        --describe \
        --topic "$topic" | grep -E "(Topic:|PartitionCount:|ReplicationFactor:|Configs:)" || true
    echo ""
done

print_status "Kafka topics setup completed successfully! ✅"
echo ""
echo "You can now:"
echo "1. Produce test data: make produce-test-data"
echo "2. Monitor Kafka: http://localhost:8080 (Kafka UI)"
echo "3. View topics and messages in real-time"