# Output values for Insurance Data Platform Infrastructure

#===========================================
# GENERAL
#===========================================

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = local.cluster_name
}

#===========================================
# NETWORKING
#===========================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = aws_subnet.database[*].id
}

#===========================================
# EKS CLUSTER
#===========================================

output "eks_cluster_id" {
  description = "EKS cluster ID"
  value       = aws_eks_cluster.main.id
}

output "eks_cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.main.arn
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_cluster_version" {
  description = "EKS cluster version"
  value       = aws_eks_cluster.main.version
}

output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "eks_node_group_arn" {
  description = "EKS node group ARN"
  value       = aws_eks_node_group.main.arn
}

output "eks_oidc_issuer_url" {
  description = "The URL on the EKS cluster OIDC Issuer"
  value       = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

#===========================================
# DATABASE
#===========================================

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.postgresql.endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.postgresql.port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.postgresql.db_name
}

output "rds_username" {
  description = "RDS master username"
  value       = aws_db_instance.postgresql.username
  sensitive   = true
}

#===========================================
# REDIS
#===========================================

output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_replication_group.redis.port
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint"
  value       = aws_elasticache_replication_group.redis.reader_endpoint_address
  sensitive   = true
}

#===========================================
# MSK (KAFKA)
#===========================================

output "kafka_bootstrap_brokers" {
  description = "MSK bootstrap brokers"
  value       = aws_msk_cluster.kafka.bootstrap_brokers
  sensitive   = true
}

output "kafka_bootstrap_brokers_tls" {
  description = "MSK bootstrap brokers TLS"
  value       = aws_msk_cluster.kafka.bootstrap_brokers_tls
  sensitive   = true
}

output "kafka_cluster_arn" {
  description = "MSK cluster ARN"
  value       = aws_msk_cluster.kafka.arn
}

output "kafka_zookeeper_connect_string" {
  description = "MSK zookeeper connect string"
  value       = aws_msk_cluster.kafka.zookeeper_connect_string
  sensitive   = true
}

#===========================================
# S3 BUCKETS
#===========================================

output "data_lake_bucket_name" {
  description = "Data lake S3 bucket name"
  value       = aws_s3_bucket.data_lake.bucket
}

output "data_lake_bucket_arn" {
  description = "Data lake S3 bucket ARN"
  value       = aws_s3_bucket.data_lake.arn
}

output "processed_data_bucket_name" {
  description = "Processed data S3 bucket name"
  value       = aws_s3_bucket.processed_data.bucket
}

output "processed_data_bucket_arn" {
  description = "Processed data S3 bucket ARN"
  value       = aws_s3_bucket.processed_data.arn
}

#===========================================
# EMR CLUSTER
#===========================================

output "emr_cluster_id" {
  description = "EMR cluster ID"
  value       = var.enable_emr ? aws_emr_cluster.spark[0].id : null
}

output "emr_cluster_master_public_dns" {
  description = "EMR cluster master public DNS"
  value       = var.enable_emr ? aws_emr_cluster.spark[0].master_public_dns : null
}

#===========================================
# IAM ROLES
#===========================================

output "eks_cluster_role_arn" {
  description = "EKS cluster IAM role ARN"
  value       = aws_iam_role.eks_cluster.arn
}

output "eks_node_group_role_arn" {
  description = "EKS node group IAM role ARN"
  value       = aws_iam_role.eks_node_group.arn
}

output "data_platform_policy_arn" {
  description = "Data platform IAM policy ARN"
  value       = aws_iam_policy.data_platform_policy.arn
}

#===========================================
# MONITORING
#===========================================

output "cloudwatch_log_group_names" {
  description = "CloudWatch log group names"
  value = {
    eks_cluster = aws_cloudwatch_log_group.eks_cluster.name
    airflow     = aws_cloudwatch_log_group.airflow.name
    spark       = aws_cloudwatch_log_group.spark.name
  }
}

#===========================================
# CONNECTION STRINGS
#===========================================

output "database_connection_string" {
  description = "Database connection string (without password)"
  value       = "postgresql://${aws_db_instance.postgresql.username}@${aws_db_instance.postgresql.endpoint}/${aws_db_instance.postgresql.db_name}"
  sensitive   = true
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:${aws_elasticache_replication_group.redis.port}"
  sensitive   = true
}

#===========================================
# KUBECTL CONFIGURATION
#===========================================

output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}

#===========================================
# SUMMARY INFORMATION
#===========================================

output "platform_summary" {
  description = "Summary of deployed resources"
  value = {
    cluster_name           = local.cluster_name
    environment           = var.environment
    region                = var.aws_region
    kubernetes_version    = aws_eks_cluster.main.version
    database_engine       = "PostgreSQL ${aws_db_instance.postgresql.engine_version}"
    cache_engine          = "Redis ${aws_elasticache_replication_group.redis.engine_version}"
    kafka_version         = var.kafka_version
    data_lake_bucket      = aws_s3_bucket.data_lake.bucket
    processed_data_bucket = aws_s3_bucket.processed_data.bucket
  }
}

#===========================================
# COST INFORMATION
#===========================================

output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (USD)"
  value = {
    eks_cluster   = "~$75 (control plane)"
    worker_nodes  = "~$200-400 (depends on instance types and count)"
    rds_postgres  = "~$50-150 (depends on instance class)"
    redis         = "~$50-100 (depends on node type)"
    kafka_msk     = "~$150-300 (depends on broker count and type)"
    s3_storage    = "~$20-50 (depends on data volume)"
    data_transfer = "~$20-100 (depends on usage)"
    total_estimate = "~$565-1175 per month"
  }
}

#===========================================
# NEXT STEPS
#===========================================

output "next_steps" {
  description = "Next steps after infrastructure deployment"
  value = [
    "1. Configure kubectl: ${local.kubectl_config_command}",
    "2. Install Helm charts for applications",
    "3. Set up monitoring and alerting",
    "4. Configure CI/CD pipelines", 
    "5. Deploy insurance data platform applications",
    "6. Set up data quality monitoring",
    "7. Configure backup and disaster recovery"
  ]
}