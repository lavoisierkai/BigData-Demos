# Amazon EKS - Kubernetes Data Platform

Amazon EKS (Elastic Kubernetes Service) provides a robust, scalable platform for containerized data workloads. This directory demonstrates comprehensive implementations of data platform patterns on Kubernetes, including Spark processing, streaming analytics, ML operations, and observability.

## Architecture Overview

```
EKS Data Platform Architecture
┌─────────────────────────────────────────────────────────────────┐
│                    Data Ingestion Layer                        │
├─────────────────────────────────────────────────────────────────┤
│ Kafka (Strimzi) │ Kinesis Gateway │ FluentD │ Vector          │
│ NATS Streaming │ Apache Pulsar │ Event-driven Ingestion      │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Processing Layer                              │
├─────────────────────────────────────────────────────────────────┤
│ Spark on K8s │ Flink │ Airflow │ Argo Workflows │ Kubeflow   │
│ Ray Clusters │ Dask │ Jupyter Hub │ Apache Beam              │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Storage Layer                               │
├─────────────────────────────────────────────────────────────────┤
│ S3 CSI Driver │ EFS │ EBS │ MinIO │ Redis │ PostgreSQL       │
│ Delta Lake │ Apache Iceberg │ Apache Hudi                    │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Analytics & ML Layer                         │
├─────────────────────────────────────────────────────────────────┤
│ Kubeflow │ MLflow │ Seldon │ KServe │ Feast │ Great Expectations │
│ Grafana │ Superset │ Jupyter │ Zeppelin │ Model Serving      │
└─────────────────────────────────────────────────────────────────┘
```

## Key Capabilities Demonstrated

### 1. **Cloud-Native Data Processing**
- **Spark on Kubernetes**: Dynamic executor scaling and resource optimization
- **Apache Flink**: Stream processing with checkpointing and state management
- **Workflow Orchestration**: Argo Workflows and Apache Airflow
- **Container-native ETL**: Containerized data pipelines with GitOps

### 2. **Machine Learning Operations**
- **Kubeflow**: End-to-end ML pipeline orchestration
- **Model Serving**: Seldon Core and KServe for model deployment
- **Feature Store**: Feast for feature management
- **Experiment Tracking**: MLflow integration

### 3. **Real-Time Analytics**
- **Streaming Platforms**: Kafka (Strimzi), Apache Pulsar
- **Stream Processing**: Flink, Spark Streaming, Kafka Streams
- **Event-Driven Architecture**: CloudEvents and Knative Eventing
- **Real-Time Dashboards**: Grafana with Prometheus metrics

## Directory Structure

```
eks/
├── README.md                          # This comprehensive guide
├── cluster-setup/                     # EKS cluster configuration
│   ├── terraform/                    # Infrastructure as Code
│   │   ├── main.tf                   # EKS cluster setup
│   │   ├── node-groups.tf            # Managed node groups
│   │   ├── networking.tf             # VPC and networking
│   │   ├── security.tf               # IAM roles and policies
│   │   ├── addons.tf                 # EKS addons (CNI, CoreDNS, etc.)
│   │   └── outputs.tf                # Output values
│   ├── eksctl/                       # eksctl configuration
│   │   ├── cluster-config.yaml       # Cluster configuration
│   │   ├── node-groups.yaml          # Node group definitions
│   │   └── addons-config.yaml        # Add-on configurations
│   └── helm-charts/                  # Essential cluster services
│       ├── aws-load-balancer-controller/ # ALB controller
│       ├── cluster-autoscaler/        # Cluster autoscaling
│       ├── metrics-server/            # Resource metrics
│       ├── cert-manager/              # Certificate management
│       └── external-dns/              # DNS management
├── data-platform/                     # Data platform workloads
│   ├── spark-operator/                # Spark Kubernetes Operator
│   │   ├── operator-deployment.yaml   # Spark operator setup
│   │   ├── spark-rbac.yaml           # RBAC configuration
│   │   ├── spark-applications/        # Spark application definitions
│   │   │   ├── etl-pipeline.yaml     # ETL Spark application
│   │   │   ├── ml-training.yaml      # ML training job
│   │   │   ├── streaming-analytics.yaml # Streaming application
│   │   │   └── batch-processing.yaml  # Batch processing job
│   │   ├── configurations/            # Spark configurations
│   │   │   ├── spark-defaults.conf    # Default Spark settings
│   │   │   ├── log4j.properties       # Logging configuration
│   │   │   └── driver-pod-template.yaml # Driver pod template
│   │   └── monitoring/                # Spark monitoring
│   │       ├── spark-history-server.yaml # History server
│   │       ├── prometheus-config.yaml  # Prometheus metrics
│   │       └── grafana-dashboards.yaml # Grafana dashboards
│   ├── flink/                         # Apache Flink deployment
│   │   ├── flink-operator/            # Flink Kubernetes Operator
│   │   ├── job-manager/               # JobManager configuration
│   │   ├── task-manager/              # TaskManager configuration
│   │   ├── applications/              # Flink applications
│   │   │   ├── stream-processing.yaml # Stream processing job
│   │   │   ├── fraud-detection.yaml   # Fraud detection pipeline
│   │   │   ├── real-time-analytics.yaml # Real-time analytics
│   │   │   └── event-processing.yaml   # Complex event processing
│   │   └── checkpointing/             # Checkpoint configuration
│   ├── kafka/                         # Apache Kafka (Strimzi)
│   │   ├── strimzi-operator/          # Strimzi Kafka operator
│   │   ├── kafka-cluster.yaml         # Kafka cluster definition
│   │   ├── topics/                    # Kafka topic definitions
│   │   │   ├── user-events.yaml      # User events topic
│   │   │   ├── transaction-data.yaml  # Transaction data topic
│   │   │   ├── iot-telemetry.yaml     # IoT telemetry topic
│   │   │   └── system-logs.yaml       # System logs topic
│   │   ├── connectors/                # Kafka Connect configurations
│   │   │   ├── s3-sink-connector.yaml # S3 sink connector
│   │   │   ├── jdbc-source-connector.yaml # JDBC source connector
│   │   │   └── elasticsearch-sink.yaml # Elasticsearch sink
│   │   ├── schema-registry/           # Confluent Schema Registry
│   │   └── monitoring/                # Kafka monitoring setup
│   ├── airflow/                       # Apache Airflow
│   │   ├── helm-values.yaml           # Airflow Helm configuration
│   │   ├── dags/                      # Data pipeline DAGs
│   │   │   ├── etl-pipeline.py        # ETL workflow
│   │   │   ├── ml-pipeline.py         # ML training pipeline
│   │   │   ├── data-quality-checks.py # Data quality validation
│   │   │   └── batch-processing.py    # Batch processing workflow
│   │   ├── plugins/                   # Custom Airflow plugins
│   │   ├── config/                    # Airflow configuration
│   │   └── secrets/                   # Secret management
│   └── argo-workflows/                # Argo Workflows
│       ├── workflow-controller.yaml   # Controller setup
│       ├── templates/                 # Workflow templates
│       │   ├── data-pipeline-template.yaml # Data pipeline template
│       │   ├── ml-training-template.yaml # ML training template
│       │   └── batch-job-template.yaml # Batch job template
│       ├── workflows/                 # Actual workflows
│       │   ├── daily-etl-workflow.yaml # Daily ETL process
│       │   ├── model-training-workflow.yaml # Model training
│       │   └── data-validation-workflow.yaml # Data validation
│       └── monitoring/                # Workflow monitoring
├── ml-platform/                       # Machine Learning Platform
│   ├── kubeflow/                      # Kubeflow installation
│   │   ├── kustomization.yaml         # Kubeflow components
│   │   ├── pipelines/                 # ML pipelines
│   │   │   ├── training-pipeline.yaml # Model training pipeline
│   │   │   ├── batch-prediction.yaml  # Batch prediction pipeline
│   │   │   ├── feature-engineering.yaml # Feature engineering
│   │   │   └── model-validation.yaml   # Model validation pipeline
│   │   ├── notebooks/                 # Jupyter notebook server
│   │   ├── katib/                     # Hyperparameter tuning
│   │   └── kfserving/                 # Model serving
│   ├── mlflow/                        # MLflow deployment
│   │   ├── mlflow-server.yaml         # MLflow tracking server
│   │   ├── model-registry/            # Model registry setup
│   │   ├── artifact-store/            # Artifact storage config
│   │   └── experiments/               # Experiment configurations
│   ├── seldon-core/                   # Model serving platform
│   │   ├── seldon-operator.yaml       # Seldon operator
│   │   ├── model-deployments/         # Model serving configurations
│   │   │   ├── fraud-detection-model.yaml # Fraud detection serving
│   │   │   ├── recommendation-model.yaml # Recommendation engine
│   │   │   └── sentiment-analysis.yaml # Sentiment analysis model
│   │   ├── a-b-testing/               # A/B testing setup
│   │   └── canary-deployments/        # Canary deployment configs
│   └── feast/                         # Feature store
│       ├── feast-core.yaml            # Feast core services
│       ├── feature-stores/            # Feature store definitions
│       ├── data-sources/              # Data source configurations
│       └── serving-configs/           # Feature serving setup
├── monitoring/                        # Monitoring and observability
│   ├── prometheus/                    # Prometheus monitoring
│   │   ├── prometheus-operator.yaml   # Prometheus operator
│   │   ├── prometheus-config.yaml     # Prometheus configuration
│   │   ├── service-monitors/          # Service monitoring rules
│   │   │   ├── spark-monitoring.yaml  # Spark metrics
│   │   │   ├── kafka-monitoring.yaml  # Kafka metrics
│   │   │   ├── flink-monitoring.yaml  # Flink metrics
│   │   │   └── airflow-monitoring.yaml # Airflow metrics
│   │   ├── alerting-rules/            # Alerting configurations
│   │   │   ├── data-pipeline-alerts.yaml # Pipeline alerts
│   │   │   ├── resource-alerts.yaml    # Resource alerts
│   │   │   └── ml-model-alerts.yaml    # ML model alerts
│   │   └── recording-rules/           # Prometheus recording rules
│   ├── grafana/                       # Grafana dashboards
│   │   ├── grafana-deployment.yaml    # Grafana setup
│   │   ├── dashboards/                # Dashboard definitions
│   │   │   ├── eks-cluster-overview.json # Cluster overview
│   │   │   ├── spark-applications.json # Spark monitoring
│   │   │   ├── kafka-cluster.json      # Kafka monitoring
│   │   │   ├── flink-jobs.json         # Flink job monitoring
│   │   │   ├── ml-pipelines.json       # ML pipeline monitoring
│   │   │   └── data-quality.json       # Data quality metrics
│   │   ├── datasources/               # Data source configurations
│   │   └── provisioning/              # Dashboard provisioning
│   ├── jaeger/                        # Distributed tracing
│   │   ├── jaeger-operator.yaml       # Jaeger operator
│   │   ├── jaeger-instance.yaml       # Jaeger deployment
│   │   └── tracing-config/            # Tracing configurations
│   ├── fluentd/                       # Log aggregation
│   │   ├── fluentd-daemonset.yaml     # Fluentd deployment
│   │   ├── config/                    # Fluentd configuration
│   │   │   ├── fluent.conf           # Main configuration
│   │   │   ├── kubernetes.conf        # Kubernetes logs
│   │   │   ├── spark-logs.conf        # Spark log parsing
│   │   │   └── kafka-logs.conf        # Kafka log parsing
│   │   └── outputs/                   # Output configurations
│   │       ├── elasticsearch.conf     # Elasticsearch output
│   │       ├── s3.conf               # S3 log storage
│   │       └── cloudwatch.conf        # CloudWatch logs
│   └── elastic-stack/                 # ELK stack for logging
│       ├── elasticsearch/             # Elasticsearch cluster
│       ├── logstash/                  # Logstash configuration
│       ├── kibana/                    # Kibana dashboards
│       └── filebeat/                  # Log shipping
├── security/                          # Security configurations
│   ├── rbac/                          # Role-based access control
│   │   ├── cluster-roles.yaml         # Cluster-wide roles
│   │   ├── service-accounts.yaml      # Service accounts
│   │   ├── role-bindings.yaml         # Role bindings
│   │   └── pod-security-policies.yaml # Pod security policies
│   ├── network-policies/              # Network security
│   │   ├── default-deny.yaml          # Default deny policy
│   │   ├── namespace-isolation.yaml   # Namespace isolation
│   │   ├── spark-network-policy.yaml  # Spark network rules
│   │   └── kafka-network-policy.yaml  # Kafka network rules
│   ├── pod-security/                  # Pod security standards
│   │   ├── security-contexts.yaml     # Security contexts
│   │   ├── admission-controllers/     # Admission controller configs
│   │   └── opa-gatekeeper/            # OPA Gatekeeper policies
│   ├── secrets-management/            # Secret management
│   │   ├── external-secrets/          # External Secrets Operator
│   │   ├── sealed-secrets/            # Sealed Secrets controller
│   │   ├── vault-integration/         # HashiCorp Vault
│   │   └── aws-secrets-manager/       # AWS Secrets Manager
│   └── image-security/                # Container image security
│       ├── image-scanning.yaml        # Image vulnerability scanning
│       ├── admission-policies.yaml    # Image admission policies
│       └── registry-configs.yaml      # Container registry configs
├── storage/                           # Storage configurations
│   ├── s3-csi/                        # S3 CSI driver
│   │   ├── csi-driver.yaml            # S3 CSI driver deployment
│   │   ├── storage-classes.yaml       # S3 storage classes
│   │   └── persistent-volumes/        # PV configurations
│   ├── efs/                           # EFS integration
│   │   ├── efs-csi-driver.yaml        # EFS CSI driver
│   │   ├── efs-storage-class.yaml     # EFS storage class
│   │   └── shared-storage.yaml        # Shared storage configs
│   ├── ebs/                           # EBS volumes
│   │   ├── ebs-csi-driver.yaml        # EBS CSI driver
│   │   ├── storage-classes.yaml       # EBS storage classes
│   │   └── volume-snapshots.yaml      # Volume snapshot configs
│   └── minio/                         # MinIO object storage
│       ├── minio-operator.yaml        # MinIO operator
│       ├── minio-tenant.yaml          # MinIO tenant
│       └── backup-configs.yaml        # Backup configurations
├── networking/                        # Networking configurations
│   ├── ingress/                       # Ingress controllers
│   │   ├── aws-load-balancer/         # AWS Load Balancer Controller
│   │   ├── nginx-ingress/             # NGINX Ingress Controller
│   │   └── istio-gateway/             # Istio Gateway
│   ├── service-mesh/                  # Service mesh
│   │   ├── istio/                     # Istio service mesh
│   │   ├── linkerd/                   # Linkerd service mesh
│   │   └── consul-connect/            # Consul Connect
│   └── dns/                           # DNS management
│       ├── external-dns.yaml          # External DNS
│       ├── coredns-config.yaml        # CoreDNS configuration
│       └── dns-policies.yaml          # DNS policies
├── backup-disaster-recovery/          # Backup and DR
│   ├── velero/                        # Velero backup
│   │   ├── velero-installation.yaml   # Velero setup
│   │   ├── backup-schedules.yaml      # Backup schedules
│   │   ├── restore-procedures.yaml    # Restore procedures
│   │   └── backup-policies.yaml       # Backup policies
│   ├── etcd-backup/                   # etcd backup
│   │   ├── etcd-backup-job.yaml       # Backup job
│   │   └── backup-schedule.yaml       # Backup scheduling
│   └── cross-region/                  # Cross-region DR
│       ├── replication-configs.yaml   # Data replication
│       └── failover-procedures.yaml   # Failover automation
├── gitops/                            # GitOps configurations
│   ├── argocd/                        # ArgoCD deployment
│   │   ├── argocd-install.yaml        # ArgoCD installation
│   │   ├── applications/              # Application definitions
│   │   │   ├── spark-operator-app.yaml # Spark operator application
│   │   │   ├── kafka-app.yaml          # Kafka application
│   │   │   ├── airflow-app.yaml        # Airflow application
│   │   │   └── monitoring-app.yaml     # Monitoring stack
│   │   ├── repositories/              # Git repository configs
│   │   ├── sync-policies/             # Sync policies
│   │   └── rbac-config.yaml           # ArgoCD RBAC
│   ├── flux/                          # Flux v2 GitOps
│   │   ├── flux-system/               # Flux system components
│   │   ├── sources/                   # Git sources
│   │   ├── kustomizations/            # Kustomization configs
│   │   └── helm-releases/             # Helm release configs
│   └── tekton/                        # Tekton CI/CD
│       ├── tekton-pipelines/          # Pipeline definitions
│       ├── tasks/                     # Reusable tasks
│       ├── triggers/                  # Event triggers
│       └── results/                   # Pipeline results
├── examples/                          # Complete example implementations
│   ├── real-time-analytics/           # Real-time analytics platform
│   │   ├── architecture-diagram.md    # Architecture documentation
│   │   ├── deployment-guide.md        # Deployment instructions
│   │   ├── kafka-setup/               # Kafka configuration
│   │   ├── flink-jobs/                # Flink processing jobs
│   │   ├── dashboard-configs/         # Monitoring dashboards
│   │   └── load-testing/              # Performance testing
│   ├── ml-pipeline/                   # End-to-end ML pipeline
│   │   ├── kubeflow-pipeline.yaml     # Kubeflow pipeline definition
│   │   ├── data-preparation/          # Data prep containers
│   │   ├── model-training/            # Training job configs
│   │   ├── model-serving/             # Serving configurations
│   │   └── monitoring/                # ML monitoring setup
│   ├── batch-processing/              # Large-scale batch processing
│   │   ├── spark-applications/        # Spark job definitions
│   │   ├── workflow-orchestration/    # Airflow/Argo workflows
│   │   ├── data-validation/           # Data quality checks
│   │   └── performance-tuning/        # Performance optimization
│   └── streaming-etl/                 # Streaming ETL pipeline
│       ├── kafka-streams/             # Kafka Streams applications
│       ├── flink-sql/                 # Flink SQL queries
│       ├── schema-registry/           # Schema management
│       └── monitoring/                # Pipeline monitoring
├── scripts/                           # Automation scripts
│   ├── cluster-setup.sh               # Cluster setup automation
│   ├── deploy-data-platform.sh       # Data platform deployment
│   ├── install-monitoring.sh         # Monitoring stack installation
│   ├── backup-cluster.sh              # Cluster backup script
│   ├── scale-workloads.sh             # Workload scaling
│   ├── performance-test.sh            # Performance testing
│   └── troubleshooting.sh             # Troubleshooting utilities
└── docs/                              # Documentation
    ├── getting-started.md             # Getting started guide
    ├── architecture-guide.md          # Architecture documentation
    ├── deployment-guide.md            # Deployment instructions
    ├── monitoring-guide.md            # Monitoring and observability
    ├── security-guide.md              # Security best practices
    ├── troubleshooting-guide.md       # Troubleshooting guide
    ├── performance-tuning.md          # Performance optimization
    └── best-practices.md              # Kubernetes best practices
```

## Enterprise Use Cases

### 1. **Real-Time Analytics Platform**
```
Components:
├── Kafka cluster for event ingestion (1M+ events/sec)
├── Flink for real-time stream processing
├── Spark for batch analytics and ML training
├── Prometheus + Grafana for monitoring
└── S3 + Delta Lake for data lake storage

Business Value:
├── Sub-second latency for real-time insights
├── 99.9% uptime with auto-scaling
├── Cost optimization with spot instances
└── Comprehensive monitoring and alerting
```

### 2. **Machine Learning Operations Platform**
```
Components:
├── Kubeflow for ML pipeline orchestration
├── MLflow for experiment tracking and model registry
├── Seldon Core for model serving and A/B testing
├── Feast for feature store management
└── Prometheus for ML model monitoring

Business Value:
├── Automated ML pipeline deployment
├── Model versioning and rollback capabilities
├── Real-time model scoring (< 100ms latency)
└── Comprehensive ML observability
```

### 3. **Data Lake Processing Platform**
```
Components:
├── Spark on K8s for large-scale data processing
├── Airflow for workflow orchestration
├── Delta Lake for ACID transactions
├── Great Expectations for data quality
└── Grafana for data pipeline monitoring

Business Value:
├── Petabyte-scale data processing
├── Data quality validation and monitoring
├── Cost-effective compute with auto-scaling
└── Lineage tracking and governance
```

## Performance Characteristics

### Spark on Kubernetes
```
Throughput:
├── Batch processing: 10TB+ per hour
├── Streaming: 1M+ events/second
├── Auto-scaling: 2-1000+ executors
└── Cost optimization: 40-60% with Spot instances

Latency:
├── Job startup: < 30 seconds
├── Dynamic allocation: < 10 seconds
├── Checkpoint recovery: < 2 minutes
└── Query execution: Optimized with caching
```

### Apache Flink
```
Stream Processing:
├── Throughput: 10M+ events/second per TaskManager
├── Latency: < 10ms end-to-end processing
├── Fault tolerance: Exactly-once processing guarantees
└── State management: RocksDB backend with S3 checkpoints

Scalability:
├── Horizontal scaling: 1-1000+ TaskManagers
├── Vertical scaling: Memory and CPU optimization
├── Backpressure handling: Automatic flow control
└── Resource isolation: CPU and memory limits
```

### Kafka on Kubernetes (Strimzi)
```
Event Streaming:
├── Throughput: 1M+ messages/second per broker
├── Latency: < 5ms producer-to-consumer
├── Durability: Configurable replication and retention
└── Scaling: Dynamic broker and partition scaling

Operations:
├── Rolling updates: Zero-downtime upgrades
├── Monitoring: JMX metrics with Prometheus
├── Security: TLS encryption and SASL authentication
└── Schema evolution: Confluent Schema Registry
```

## Security Implementation

### 1. **Pod Security Standards**
```yaml
# Restricted security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 3000
  fsGroup: 2000
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop:
    - ALL
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
```

### 2. **Network Security**
```yaml
# Network policy for Spark applications
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: spark-network-policy
spec:
  podSelector:
    matchLabels:
      app: spark
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: spark
    ports:
    - protocol: TCP
      port: 7077
```

### 3. **RBAC Configuration**
```yaml
# Service account with minimal permissions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: spark-service-account
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: spark-role
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "create", "delete"]
```

## Monitoring and Observability

### 1. **Metrics Collection**
- **Prometheus**: Cluster and application metrics
- **Custom Metrics**: Application-specific KPIs
- **Node Exporter**: System-level metrics
- **Kubernetes Metrics**: Resource utilization

### 2. **Distributed Tracing**
- **Jaeger**: End-to-end request tracing
- **OpenTelemetry**: Standardized observability
- **Correlation IDs**: Request correlation across services

### 3. **Log Aggregation**
- **Fluentd**: Log collection and parsing
- **Elasticsearch**: Log storage and indexing
- **Kibana**: Log analysis and visualization

### 4. **Alerting**
- **Alertmanager**: Alert routing and notification
- **PagerDuty**: Incident management integration
- **Slack**: Team notifications

## Getting Started

### Prerequisites
```bash
# AWS CLI configuration
aws configure
aws eks update-kubeconfig --region us-west-2 --name data-platform-cluster

# Kubernetes tools
kubectl version --client
helm version

# Terraform for infrastructure
terraform --version
```

### Quick Start Deployment
```bash
# 1. Deploy EKS cluster
cd cluster-setup/terraform
terraform init && terraform apply

# 2. Install cluster essentials
./scripts/cluster-setup.sh

# 3. Deploy data platform
./scripts/deploy-data-platform.sh

# 4. Install monitoring
./scripts/install-monitoring.sh

# 5. Verify deployment
kubectl get pods --all-namespaces
```

### Example Workflow
```bash
# Deploy Spark application
kubectl apply -f data-platform/spark-operator/spark-applications/etl-pipeline.yaml

# Check application status
kubectl get sparkapplications

# View Spark UI
kubectl port-forward svc/spark-ui 4040:4040

# Monitor with Grafana
kubectl port-forward svc/grafana 3000:3000
```

## Best Practices Implemented

### 1. **Resource Management**
- **Resource Quotas**: Namespace-level resource limits
- **Limit Ranges**: Pod-level resource constraints
- **Priority Classes**: Workload prioritization
- **Horizontal Pod Autoscaler**: Dynamic scaling

### 2. **High Availability**
- **Multi-AZ Deployment**: Fault tolerance across zones
- **Pod Disruption Budgets**: Controlled disruptions
- **Cluster Autoscaler**: Node-level scaling
- **Backup Strategies**: Velero for cluster backups

### 3. **Cost Optimization**
- **Spot Instances**: Cost-effective compute
- **Vertical Pod Autoscaler**: Right-sizing containers
- **Cluster Proportional Autoscaler**: DNS scaling
- **Resource Efficiency**: CPU and memory optimization

### 4. **GitOps Deployment**
- **ArgoCD**: Declarative GitOps workflow
- **Helm Charts**: Parameterized deployments
- **Kustomize**: Configuration management
- **Git-based Workflows**: Version-controlled deployments

This comprehensive EKS implementation provides a production-ready, scalable, and secure platform for running data workloads on Kubernetes, demonstrating enterprise-grade cloud-native data architecture patterns.