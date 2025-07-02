#!/bin/bash

# Submit Spark Job to AWS EKS
# This script demonstrates how to submit a Spark application to EKS using the Spark Operator
# 
# Prerequisites:
# - EKS cluster with Spark Operator installed
# - kubectl configured to access the EKS cluster
# - Docker image with Spark application code
# - S3 buckets for input/output data

set -e

# Configuration variables
CLUSTER_NAME="${CLUSTER_NAME:-data-platform-cluster}"
NAMESPACE="${NAMESPACE:-spark-jobs}"
JOB_NAME="${JOB_NAME:-ecommerce-analytics-$(date +%Y%m%d-%H%M%S)}"
SPARK_VERSION="${SPARK_VERSION:-3.4.0}"
KUBERNETES_VERSION="${KUBERNETES_VERSION:-v1.27.0}"

# S3 configuration
S3_BUCKET="${S3_BUCKET:-your-data-lake-bucket}"
INPUT_PATH="${INPUT_PATH:-s3a://${S3_BUCKET}/raw-data/ecommerce/orders/}"
OUTPUT_PATH="${OUTPUT_PATH:-s3a://${S3_BUCKET}/processed-data/analytics/}"

# Docker image configuration
DOCKER_REGISTRY="${DOCKER_REGISTRY:-your-account.dkr.ecr.us-west-2.amazonaws.com}"
IMAGE_NAME="${IMAGE_NAME:-spark-analytics}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
FULL_IMAGE="${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

# Resource configuration
DRIVER_MEMORY="${DRIVER_MEMORY:-2g}"
DRIVER_CORES="${DRIVER_CORES:-1}"
EXECUTOR_MEMORY="${EXECUTOR_MEMORY:-4g}"
EXECUTOR_CORES="${EXECUTOR_CORES:-2}"
EXECUTOR_INSTANCES="${EXECUTOR_INSTANCES:-3}"
MAX_EXECUTOR_INSTANCES="${MAX_EXECUTOR_INSTANCES:-10}"

# Service account for IRSA (IAM Roles for Service Accounts)
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-spark-service-account}"

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Submit a Spark job to AWS EKS cluster"
    echo ""
    echo "Environment Variables:"
    echo "  CLUSTER_NAME           EKS cluster name (default: data-platform-cluster)"
    echo "  NAMESPACE              Kubernetes namespace (default: spark-jobs)"
    echo "  JOB_NAME               Spark application name (default: auto-generated)"
    echo "  S3_BUCKET              S3 bucket for data (required)"
    echo "  INPUT_PATH             Input data path (default: s3a://BUCKET/raw-data/ecommerce/orders/)"
    echo "  OUTPUT_PATH            Output data path (default: s3a://BUCKET/processed-data/analytics/)"
    echo "  DOCKER_REGISTRY        Docker registry URL (required)"
    echo "  IMAGE_NAME             Docker image name (default: spark-analytics)"
    echo "  IMAGE_TAG              Docker image tag (default: latest)"
    echo ""
    echo "Options:"
    echo "  -h, --help             Show this help message"
    echo "  --dry-run              Generate YAML but don't submit"
    echo "  --delete               Delete the Spark application"
    echo "  --status               Check job status"
    echo "  --logs                 Get job logs"
    echo "  --build-image          Build and push Docker image"
    echo ""
    echo "Examples:"
    echo "  # Submit job with default settings"
    echo "  $0"
    echo ""
    echo "  # Submit job with custom S3 bucket"
    echo "  S3_BUCKET=my-data-lake $0"
    echo ""
    echo "  # Build image and submit job"
    echo "  $0 --build-image"
    echo ""
    echo "  # Check job status"
    echo "  JOB_NAME=my-job $0 --status"
}

# Function to check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        echo "Error: kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        echo "Error: Cannot connect to Kubernetes cluster"
        echo "Make sure kubectl is configured to access your EKS cluster"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        echo "Creating namespace: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
    fi
    
    # Check if Spark Operator is installed
    if ! kubectl get crd sparkapplications.sparkoperator.k8s.io &> /dev/null; then
        echo "Error: Spark Operator is not installed"
        echo "Please install Spark Operator first"
        exit 1
    fi
    
    echo "Prerequisites check completed successfully"
}

# Function to build and push Docker image
build_and_push_image() {
    echo "Building and pushing Docker image..."
    
    # Create Dockerfile if it doesn't exist
    if [ ! -f "Dockerfile" ]; then
        create_dockerfile
    fi
    
    # Build the image
    docker build -t "${FULL_IMAGE}" .
    
    # Push to registry
    echo "Pushing image to registry..."
    docker push "${FULL_IMAGE}"
    
    echo "Image built and pushed successfully: ${FULL_IMAGE}"
}

# Function to create Dockerfile
create_dockerfile() {
    echo "Creating Dockerfile..."
    cat > Dockerfile << 'EOF'
FROM apache/spark-py:v3.4.0

USER root

# Install additional dependencies
RUN pip install --no-cache-dir \
    delta-spark==2.4.0 \
    boto3==1.28.85 \
    pandas==2.0.3 \
    numpy==1.24.3

# Copy application code
COPY sample-data-processing.py /opt/spark/work-dir/
COPY requirements.txt /opt/spark/work-dir/ 2>/dev/null || true

# Set working directory
WORKDIR /opt/spark/work-dir

USER 185

EOF
    echo "Dockerfile created"
}

# Function to generate Spark Application YAML
generate_spark_yaml() {
    cat > "${JOB_NAME}.yaml" << EOF
apiVersion: "sparkoperator.k8s.io/v1beta2"
kind: SparkApplication
metadata:
  name: ${JOB_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: spark-analytics
    version: v1
    environment: production
spec:
  type: Python
  pythonVersion: "3"
  mode: cluster
  image: "${FULL_IMAGE}"
  imagePullPolicy: Always
  mainApplicationFile: local:///opt/spark/work-dir/sample-data-processing.py
  arguments:
    - "${INPUT_PATH}"
    - "${OUTPUT_PATH}"
  sparkVersion: "${SPARK_VERSION}"
  restartPolicy:
    type: OnFailure
    onFailureRetries: 3
    onFailureRetryInterval: 10
    onSubmissionFailureRetries: 5
    onSubmissionFailureRetryInterval: 20
  driver:
    cores: ${DRIVER_CORES}
    coreLimit: "1200m"
    memory: "${DRIVER_MEMORY}"
    memoryOverhead: "512m"
    labels:
      version: ${SPARK_VERSION}
      app: spark-driver
    serviceAccount: ${SERVICE_ACCOUNT}
    annotations:
      eks.amazonaws.com/role-arn: "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/SparkJobRole"
    env:
      - name: AWS_REGION
        value: "us-west-2"
      - name: SPARK_CONF_DIR
        value: "/opt/spark/conf"
    volumeMounts:
      - name: spark-local-dir-1
        mountPath: /tmp
      - name: spark-conf-volume
        mountPath: /opt/spark/conf
  executor:
    cores: ${EXECUTOR_CORES}
    coreLimit: "2400m"
    memory: "${EXECUTOR_MEMORY}"
    memoryOverhead: "1g"
    instances: ${EXECUTOR_INSTANCES}
    labels:
      version: ${SPARK_VERSION}
      app: spark-executor
    env:
      - name: AWS_REGION
        value: "us-west-2"
    volumeMounts:
      - name: spark-local-dir-1
        mountPath: /tmp
  volumes:
    - name: spark-local-dir-1
      emptyDir: {}
    - name: spark-conf-volume
      configMap:
        name: spark-config
        optional: true
  dynamicAllocation:
    enabled: true
    initialExecutors: ${EXECUTOR_INSTANCES}
    minExecutors: 1
    maxExecutors: ${MAX_EXECUTOR_INSTANCES}
    targetExecutorRequestRatio: 0.8
  sparkConf:
    "spark.sql.adaptive.enabled": "true"
    "spark.sql.adaptive.coalescePartitions.enabled": "true"
    "spark.sql.adaptive.advisoryPartitionSizeInBytes": "128MB"
    "spark.sql.adaptive.skewJoin.enabled": "true"
    "spark.sql.adaptive.localShuffleReader.enabled": "true"
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer"
    "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension"
    "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog"
    "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem"
    "spark.hadoop.fs.s3a.aws.credentials.provider": "com.amazonaws.auth.WebIdentityTokenCredentialsProvider"
    "spark.hadoop.fs.s3a.fast.upload": "true"
    "spark.hadoop.fs.s3a.multipart.size": "104857600"
    "spark.hadoop.fs.s3a.multipart.threshold": "2147483647"
    "spark.hadoop.fs.s3a.committer.name": "magic"
    "spark.hadoop.fs.s3a.committer.magic.enabled": "true"
    "spark.kubernetes.container.image.pullPolicy": "Always"
    "spark.kubernetes.allocation.batch.size": "5"
    "spark.kubernetes.allocation.batch.delay": "1s"
    "spark.kubernetes.local.dirs.tmpfs": "true"
    "spark.local.dir": "/tmp"
    "spark.eventLog.enabled": "true"
    "spark.eventLog.dir": "s3a://${S3_BUCKET}/spark-logs/"
    "spark.history.fs.logDirectory": "s3a://${S3_BUCKET}/spark-logs/"
  monitoring:
    exposeDriverMetrics: true
    exposeExecutorMetrics: true
    prometheus:
      jmxExporterJar: "/opt/spark/jars/jmx_prometheus_javaagent-0.17.2.jar"
      port: 8090
EOF
}

# Function to submit the job
submit_job() {
    echo "Submitting Spark job: ${JOB_NAME}"
    
    # Generate YAML
    generate_spark_yaml
    
    if [ "$DRY_RUN" = "true" ]; then
        echo "Dry run mode - generated YAML:"
        cat "${JOB_NAME}.yaml"
        return
    fi
    
    # Apply the YAML
    kubectl apply -f "${JOB_NAME}.yaml"
    
    echo "Job submitted successfully!"
    echo "Job name: ${JOB_NAME}"
    echo "Namespace: ${NAMESPACE}"
    echo ""
    echo "Monitor the job with:"
    echo "  kubectl get sparkapplication ${JOB_NAME} -n ${NAMESPACE}"
    echo "  kubectl describe sparkapplication ${JOB_NAME} -n ${NAMESPACE}"
    echo "  kubectl logs -f spark-${JOB_NAME}-driver -n ${NAMESPACE}"
}

# Function to check job status
check_status() {
    echo "Checking status for job: ${JOB_NAME}"
    
    if kubectl get sparkapplication "${JOB_NAME}" -n "${NAMESPACE}" &> /dev/null; then
        kubectl get sparkapplication "${JOB_NAME}" -n "${NAMESPACE}" -o wide
        echo ""
        kubectl describe sparkapplication "${JOB_NAME}" -n "${NAMESPACE}"
    else
        echo "Job ${JOB_NAME} not found in namespace ${NAMESPACE}"
        exit 1
    fi
}

# Function to get job logs
get_logs() {
    echo "Getting logs for job: ${JOB_NAME}"
    
    # Check if driver pod exists
    DRIVER_POD="spark-${JOB_NAME}-driver"
    if kubectl get pod "${DRIVER_POD}" -n "${NAMESPACE}" &> /dev/null; then
        echo "Driver pod logs:"
        kubectl logs "${DRIVER_POD}" -n "${NAMESPACE}" --tail=100
        
        echo ""
        echo "Getting executor logs..."
        EXECUTOR_PODS=$(kubectl get pods -n "${NAMESPACE}" -l spark-app-name="${JOB_NAME}" -l spark-role=executor -o name)
        for pod in $EXECUTOR_PODS; do
            echo "Logs from $pod:"
            kubectl logs "$pod" -n "${NAMESPACE}" --tail=50
            echo "---"
        done
    else
        echo "Driver pod ${DRIVER_POD} not found"
        exit 1
    fi
}

# Function to delete job
delete_job() {
    echo "Deleting job: ${JOB_NAME}"
    
    if kubectl get sparkapplication "${JOB_NAME}" -n "${NAMESPACE}" &> /dev/null; then
        kubectl delete sparkapplication "${JOB_NAME}" -n "${NAMESPACE}"
        echo "Job ${JOB_NAME} deleted successfully"
    else
        echo "Job ${JOB_NAME} not found"
        exit 1
    fi
}

# Parse command line arguments
DRY_RUN=false
BUILD_IMAGE=false
DELETE_JOB=false
CHECK_STATUS=false
GET_LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --build-image)
            BUILD_IMAGE=true
            shift
            ;;
        --delete)
            DELETE_JOB=true
            shift
            ;;
        --status)
            CHECK_STATUS=true
            shift
            ;;
        --logs)
            GET_LOGS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required environment variables
if [ -z "$S3_BUCKET" ]; then
    echo "Error: S3_BUCKET environment variable is required"
    echo "Example: S3_BUCKET=my-data-lake $0"
    exit 1
fi

if [ -z "$DOCKER_REGISTRY" ] && [ "$BUILD_IMAGE" = "true" ]; then
    echo "Error: DOCKER_REGISTRY environment variable is required when building image"
    exit 1
fi

# Main execution
echo "AWS EKS Spark Job Submission Script"
echo "=================================="
echo "Cluster: ${CLUSTER_NAME}"
echo "Namespace: ${NAMESPACE}"
echo "Job: ${JOB_NAME}"
echo "Image: ${FULL_IMAGE}"
echo "Input: ${INPUT_PATH}"
echo "Output: ${OUTPUT_PATH}"
echo ""

# Execute based on operation
if [ "$DELETE_JOB" = "true" ]; then
    delete_job
elif [ "$CHECK_STATUS" = "true" ]; then
    check_status
elif [ "$GET_LOGS" = "true" ]; then
    get_logs
else
    check_prerequisites
    
    if [ "$BUILD_IMAGE" = "true" ]; then
        build_and_push_image
    fi
    
    submit_job
fi

echo "Operation completed successfully!"