# Variables for Insurance Data Platform Infrastructure

#===========================================
# GENERAL
#===========================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "insurance-data-platform"
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "data-engineering-team"
}

#===========================================
# NETWORKING
#===========================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to use"
  type        = number
  default     = 3
  
  validation {
    condition     = var.az_count >= 2 && var.az_count <= 6
    error_message = "AZ count must be between 2 and 6."
  }
}

#===========================================
# EKS CLUSTER
#===========================================

variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "node_group_instance_types" {
  description = "Instance types for EKS node group"
  type        = list(string)
  default     = ["m5.xlarge", "m5.2xlarge"]
}

variable "node_group_scaling_config" {
  description = "Scaling configuration for EKS node group"
  type = object({
    desired_size = number
    max_size     = number
    min_size     = number
  })
  default = {
    desired_size = 3
    max_size     = 10
    min_size     = 1
  }
}

variable "node_group_disk_size" {
  description = "Disk size for EKS worker nodes (in GB)"
  type        = number
  default     = 50
}

#===========================================
# DATABASE
#===========================================

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "insurance_user"
  sensitive   = true
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "db_allocated_storage" {
  description = "Initial allocated storage for RDS (in GB)"
  type        = number
  default     = 100
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS (in GB)"
  type        = number
  default     = 500
}

variable "db_backup_retention_period" {
  description = "Backup retention period (in days)"
  type        = number
  default     = 7
}

#===========================================
# REDIS
#===========================================

variable "redis_node_type" {
  description = "Node type for Redis cluster"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes in Redis cluster"
  type        = number
  default     = 2
}

#===========================================
# MSK (KAFKA)
#===========================================

variable "kafka_instance_type" {
  description = "Instance type for MSK brokers"
  type        = string
  default     = "kafka.m5.large"
}

variable "kafka_volume_size" {
  description = "Volume size for MSK brokers (in GB)"
  type        = number
  default     = 100
}

variable "kafka_version" {
  description = "Kafka version"
  type        = string
  default     = "2.8.1"
}

#===========================================
# EMR (SPARK)
#===========================================

variable "emr_release_label" {
  description = "EMR release label"
  type        = string
  default     = "emr-6.15.0"
}

variable "emr_master_instance_type" {
  description = "Instance type for EMR master node"
  type        = string
  default     = "m5.xlarge"
}

variable "emr_core_instance_type" {
  description = "Instance type for EMR core nodes"
  type        = string
  default     = "m5.large"
}

variable "emr_core_instance_count" {
  description = "Number of EMR core instances"
  type        = number
  default     = 3
}

#===========================================
# MONITORING
#===========================================

variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring for resources"
  type        = bool
  default     = true
}

variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log retention period (in days)"
  type        = number
  default     = 14
}

#===========================================
# SECURITY
#===========================================

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access resources"
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

variable "enable_encryption" {
  description = "Enable encryption for all resources"
  type        = bool
  default     = true
}

#===========================================
# COST OPTIMIZATION
#===========================================

variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = false
}

variable "spot_instance_types" {
  description = "Instance types for spot instances"
  type        = list(string)
  default     = ["m5.large", "m5.xlarge", "c5.large", "c5.xlarge"]
}

#===========================================
# BACKUP & DISASTER RECOVERY
#===========================================

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup"
  type        = bool
  default     = false
}

variable "backup_region" {
  description = "Backup region for disaster recovery"
  type        = string
  default     = "us-east-1"
}

#===========================================
# FEATURE FLAGS
#===========================================

variable "enable_databricks" {
  description = "Enable Databricks integration"
  type        = bool
  default     = false
}

variable "enable_glue" {
  description = "Enable AWS Glue for ETL"
  type        = bool
  default     = true
}

variable "enable_athena" {
  description = "Enable Amazon Athena for ad-hoc queries"
  type        = bool
  default     = true
}

variable "enable_quicksight" {
  description = "Enable Amazon QuickSight for dashboards"
  type        = bool
  default     = false
}