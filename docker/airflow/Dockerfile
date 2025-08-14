FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW_VERSION=2.8.0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/airflow

# Copy requirements
COPY requirements-airflow.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-airflow.txt

# Create Airflow user
RUN useradd -ms /bin/bash -d /opt/airflow airflow && \
    chown -R airflow: /opt/airflow

USER airflow

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK CMD ["curl", "--fail", "http://localhost:8080/health"] || exit 1

# Default command (will be overridden by docker-compose)
CMD ["airflow", "webserver"]