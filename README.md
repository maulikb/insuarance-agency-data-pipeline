# Insurance Data Platform

A comprehensive, enterprise-grade data platform for insurance companies built with modern data engineering tools and best practices. This platform provides end-to-end data processing, analytics, and monitoring capabilities for insurance operations including customers, policies, claims, and payments.

## 🏗️ Architecture Overview

This platform implements a modern data architecture with the following components:

- **Data Storage**: PostgreSQL with optimized schemas for insurance data
- **Message Streaming**: Apache Kafka for real-time event processing
- **Data Processing**: Apache Spark for large-scale data transformations
- **Analytics**: DBT for data modeling and transformations
- **API Layer**: FastAPI for RESTful data access
- **Monitoring**: Prometheus & Grafana for observability
- **Development**: Jupyter notebooks for data exploration
- **Storage**: MinIO for object storage (S3-compatible)
- **Memory Cache**: Redis for high-performance caching
- **Orchestration**: Docker Compose for local development

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Make (for convenient commands)
- 8GB+ RAM recommended

### 1. Clone and Setup

```bash
git clone https://github.com/maulikb/insuarance-agency-data-pipeline.git
cd insuarance-agency-data-pipeline
```

### 2. Start the Platform

```bash
# Start all services
make up

# Or manually with docker-compose
docker-compose up -d
```

### 3. Initialize Data

```bash
# Create Kafka topics
make create-kafka-topics

# Generate and load sample data
make generate-data
```

### 4. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **Jupyter Lab** | http://localhost:8888 | Data exploration and analysis |
| **Grafana** | http://localhost:3000 | Monitoring dashboards (admin/admin) |
| **Kafka UI** | http://localhost:8082 | Kafka topics and messages |
| **API Documentation** | http://localhost:8000/docs | FastAPI interactive docs |
| **Prometheus** | http://localhost:9090 | Metrics collection |
| **MinIO Console** | http://localhost:9001 | Object storage (minio/minio123) |

## 📊 Data Model

### Core Entities

- **Customers**: Individual and business customer records
- **Policies**: Insurance policies with coverage details
- **Claims**: Insurance claims processing and tracking
- **Agents**: Sales agents and territories
- **Payments**: Premium payments and billing
- **Underwriting**: Risk assessment decisions

### Database Schemas

- `raw_data`: Source system data replication
- `staging`: Cleaned and standardized data
- `marts`: Business-ready analytical models
- `audit`: Data lineage and change tracking
- `monitoring`: Data quality and pipeline health

## 🛠️ Development Commands

```bash
# Environment Management
make up              # Start all services
make down            # Stop all services
make restart         # Restart all services
make logs            # View all service logs

# Data Operations
make generate-data   # Generate sample insurance data
make create-kafka-topics  # Create Kafka topics
make run-dbt         # Run DBT transformations
make data-quality    # Run data quality checks

# Development Tools
make jupyter         # Access Jupyter Lab
make kafka-ui        # Access Kafka UI
make grafana         # Access Grafana dashboards
make api-docs        # Access API documentation

# Cleanup
make clean           # Remove containers and volumes
make clean-data      # Remove only data volumes
```

## 📈 Features

### Data Processing
- **Real-time Streaming**: Kafka-based event processing
- **Batch Processing**: Spark jobs for large-scale transformations
- **Data Quality**: Comprehensive validation and monitoring
- **Change Data Capture**: Track all data modifications

### Analytics & BI
- **Data Modeling**: DBT for dimensional modeling
- **Metrics Layer**: Pre-calculated KPIs and metrics
- **Visualization**: Grafana dashboards for operations
- **Ad-hoc Analysis**: Jupyter notebooks for exploration

### API & Integration
- **REST API**: FastAPI with automatic documentation
- **Authentication**: JWT-based security (future)
- **Rate Limiting**: API throttling and quotas
- **Data Export**: Multiple format support (JSON, CSV, Parquet)

### Monitoring & Observability
- **Application Metrics**: Performance and health monitoring
- **Data Quality Metrics**: Completeness, accuracy, freshness
- **Pipeline Monitoring**: ETL job success/failure tracking
- **Alerting**: Automated notifications for issues

## 🏢 Business Use Cases

### Customer Analytics
- Customer segmentation and risk profiling
- Lifetime value calculations
- Churn prediction and retention analysis

### Policy Management
- Policy portfolio analysis
- Premium optimization
- Coverage gap analysis

### Claims Processing
- Claims frequency and severity trends
- Fraud detection patterns
- Settlement time analysis

### Financial Reporting
- Revenue and profitability analysis
- Reserve calculations
- Regulatory compliance reporting

## 🔧 Configuration

### Environment Variables

Key configuration options in `docker-compose.yml`:

```yaml
# Database
POSTGRES_DB=insurance_db
POSTGRES_USER=insurance_user
POSTGRES_PASSWORD=insurance_pass

# Kafka
KAFKA_TOPICS_REPLICATION_FACTOR=1
KAFKA_AUTO_CREATE_TOPICS_ENABLE=true

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### Data Generation

Customize sample data generation in `scripts/generate_sample_data.py`:

```python
# Configuration
CUSTOMER_COUNT = 10000
POLICY_COUNT = 25000
CLAIM_COUNT = 5000
```

## 📚 Documentation

- [Architecture Documentation](docs/architecture/)
- [API Reference](http://localhost:8000/docs)
- [Data Model Guide](docs/data-model.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🧪 Testing

```bash
# Run data quality tests
make test-data-quality

# Run API tests
make test-api

# Run integration tests
make test-integration
```

## 📦 Deployment

### Production Deployment

For production deployment, consider:

- Use managed database services (AWS RDS, Azure Database)
- Deploy Kafka on managed services (AWS MSK, Confluent Cloud)
- Use container orchestration (Kubernetes, ECS)
- Implement proper secrets management
- Set up automated backups and disaster recovery

### Cloud Providers

- **AWS**: RDS, MSK, EKS, S3, CloudWatch
- **Azure**: Database, Event Hubs, AKS, Blob Storage
- **GCP**: Cloud SQL, Pub/Sub, GKE, Cloud Storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Roadmap

### Phase 1 (Current)
- [x] Core data platform setup
- [x] Basic insurance data model
- [x] Real-time streaming with Kafka
- [x] Monitoring and observability

### Phase 2 (Next)
- [ ] Machine learning integration
- [ ] Advanced analytics features
- [ ] API authentication and authorization
- [ ] Performance optimization

### Phase 3 (Future)
- [ ] Multi-tenant architecture
- [ ] Advanced security features
- [ ] Cloud-native deployment
- [ ] Real-time AI/ML inference

## 🐛 Troubleshooting

### Common Issues

**Containers won't start:**
```bash
# Check Docker resources
docker system df
docker system prune

# Restart Docker Desktop
# Increase memory allocation to 8GB+
```

**Database connection issues:**
```bash
# Check database status
docker-compose logs postgres

# Verify schema creation
make verify-db
```

**Kafka topics not created:**
```bash
# Check Kafka status
docker-compose logs kafka

# Recreate topics
make create-kafka-topics
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♀️ Support

For questions, issues, or contributions:

- Create an issue on GitHub
- Check the documentation
- Review existing issues and discussions

## ⭐ Acknowledgments

Built with modern data engineering tools and best practices:

- Apache Kafka for streaming
- PostgreSQL for OLTP storage
- Apache Spark for big data processing
- DBT for data transformations
- FastAPI for modern APIs
- Docker for containerization
- Grafana for visualization

---

**Note**: This is a demonstration platform for learning and development. For production use, implement proper security, scalability, and compliance measures.