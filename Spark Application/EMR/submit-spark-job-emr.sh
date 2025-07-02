#!/bin/bash

# Submit Spark Job to AWS EMR
# This script demonstrates multiple ways to submit Spark applications to EMR:
# 1. EMR Clusters (traditional long-running clusters)
# 2. EMR Serverless (serverless analytics)
# 3. EMR on EKS (container-based on Kubernetes)
#
# Prerequisites:
# - AWS CLI configured with appropriate permissions
# - S3 buckets for input/output data and application code
# - IAM roles configured for EMR

set -e

# Configuration variables
CLUSTER_NAME="${CLUSTER_NAME:-customer-analytics-cluster}"
REGION="${REGION:-us-west-2}"
EMR_RELEASE="${EMR_RELEASE:-emr-6.12.0}"
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-cluster}"  # Options: cluster, serverless, eks

# S3 configuration
S3_BUCKET="${S3_BUCKET:-your-data-lake-bucket}"
S3_CODE_PATH="${S3_CODE_PATH:-s3://${S3_BUCKET}/code/spark-applications/}"
INPUT_PATH="${INPUT_PATH:-s3://${S3_BUCKET}/raw-data/customer-data/}"
OUTPUT_PATH="${OUTPUT_PATH:-s3://${S3_BUCKET}/processed-data/customer-analytics/}"
LOGS_PATH="${LOGS_PATH:-s3://${S3_BUCKET}/logs/emr-logs/}"

# Application configuration
APP_NAME="${APP_NAME:-customer-analytics-$(date +%Y%m%d-%H%M%S)}"
PYTHON_FILE="${PYTHON_FILE:-customer-analytics-emr.py}"
JAR_FILES="${JAR_FILES:-s3://${S3_BUCKET}/jars/delta-core_2.12-2.4.0.jar}"

# Cluster configuration
EC2_KEY_NAME="${EC2_KEY_NAME:-your-ec2-key}"
EC2_SUBNET_ID="${EC2_SUBNET_ID:-subnet-12345678}"
MASTER_INSTANCE_TYPE="${MASTER_INSTANCE_TYPE:-m5.xlarge}"
WORKER_INSTANCE_TYPE="${WORKER_INSTANCE_TYPE:-m5.xlarge}"
WORKER_INSTANCE_COUNT="${WORKER_INSTANCE_COUNT:-3}"
MAX_WORKER_INSTANCES="${MAX_WORKER_INSTANCES:-10}"

# EMR Serverless configuration
SERVERLESS_APP_ID="${SERVERLESS_APP_ID:-}"
MAX_CAPACITY_UNITS="${MAX_CAPACITY_UNITS:-20}"
MAX_CONCURRENT_RUNS="${MAX_CONCURRENT_RUNS:-5}"

# Security configuration
EMR_SERVICE_ROLE="${EMR_SERVICE_ROLE:-EMR_DefaultRole}"
EMR_INSTANCE_PROFILE="${EMR_INSTANCE_PROFILE:-EMR_EC2_DefaultRole}"
EMR_SERVERLESS_ROLE="${EMR_SERVERLESS_ROLE:-EMRServerlessRole}"

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Submit a Spark job to AWS EMR"
    echo ""
    echo "Environment Variables:"
    echo "  DEPLOYMENT_MODE        Deployment mode: cluster, serverless, eks (default: cluster)"
    echo "  CLUSTER_NAME           EMR cluster name (default: customer-analytics-cluster)"
    echo "  REGION                 AWS region (default: us-west-2)"
    echo "  S3_BUCKET              S3 bucket for data and code (required)"
    echo "  INPUT_PATH             Input data path (default: s3://BUCKET/raw-data/customer-data/)"
    echo "  OUTPUT_PATH            Output data path (default: s3://BUCKET/processed-data/customer-analytics/)"
    echo "  APP_NAME               Application name (default: auto-generated)"
    echo ""
    echo "Options:"
    echo "  -h, --help             Show this help message"
    echo "  --create-cluster       Create new EMR cluster"
    echo "  --terminate-cluster    Terminate EMR cluster"
    echo "  --cluster-status       Check cluster status"
    echo "  --step-status          Check step status"
    echo "  --list-clusters        List active clusters"
    echo "  --upload-code          Upload application code to S3"
    echo "  --serverless           Use EMR Serverless"
    echo "  --create-serverless-app Create EMR Serverless application"
    echo "  --dry-run              Generate configurations but don't submit"
    echo ""
    echo "Examples:"
    echo "  # Submit to existing cluster"
    echo "  CLUSTER_NAME=j-XXXXXXXXXXXXX $0"
    echo ""
    echo "  # Create cluster and submit job"
    echo "  $0 --create-cluster"
    echo ""
    echo "  # Use EMR Serverless"
    echo "  $0 --serverless"
    echo ""
    echo "  # Upload code and submit to cluster"
    echo "  $0 --upload-code --create-cluster"
}

# Function to check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo "Error: AWS CLI is not installed or not in PATH"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "Error: AWS credentials not configured"
        exit 1
    fi
    
    # Check required S3 bucket
    if [ -z "$S3_BUCKET" ]; then
        echo "Error: S3_BUCKET environment variable is required"
        exit 1
    fi
    
    # Check if S3 bucket exists
    if ! aws s3 ls "s3://${S3_BUCKET}" &> /dev/null; then
        echo "Error: S3 bucket ${S3_BUCKET} does not exist or is not accessible"
        exit 1
    fi
    
    echo "Prerequisites check completed successfully"
}

# Function to upload application code to S3
upload_code() {
    echo "Uploading application code to S3..."
    
    # Check if Python file exists
    if [ ! -f "$PYTHON_FILE" ]; then
        echo "Error: Python file $PYTHON_FILE not found"
        exit 1
    fi
    
    # Upload Python application
    aws s3 cp "$PYTHON_FILE" "${S3_CODE_PATH}${PYTHON_FILE}"
    
    # Upload any additional files if they exist
    if [ -f "requirements.txt" ]; then
        aws s3 cp "requirements.txt" "${S3_CODE_PATH}requirements.txt"
    fi
    
    echo "Code uploaded successfully to ${S3_CODE_PATH}"
}

# Function to create EMR cluster
create_cluster() {
    echo "Creating EMR cluster: $CLUSTER_NAME"
    
    # Create cluster configuration
    cat > cluster-config.json << EOF
{
    "Name": "${CLUSTER_NAME}",
    "ReleaseLabel": "${EMR_RELEASE}",
    "Applications": [
        {"Name": "Spark"},
        {"Name": "Hive"},
        {"Name": "Hadoop"},
        {"Name": "JupyterEnterpriseGateway"},
        {"Name": "Livy"}
    ],
    "Configurations": [
        {
            "Classification": "spark-defaults",
            "Properties": {
                "spark.sql.adaptive.enabled": "true",
                "spark.sql.adaptive.coalescePartitions.enabled": "true",
                "spark.sql.adaptive.skewJoin.enabled": "true",
                "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
                "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
                "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
                "spark.hadoop.fs.s3.optimized.committer.enabled": "true",
                "spark.hadoop.fs.s3.committer.name": "partitioned",
                "spark.sql.parquet.compression.codec": "snappy",
                "spark.eventLog.enabled": "true",
                "spark.eventLog.dir": "${LOGS_PATH}/spark-events/",
                "spark.history.fs.logDirectory": "${LOGS_PATH}/spark-events/"
            }
        },
        {
            "Classification": "spark-hive-site",
            "Properties": {
                "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
            }
        }
    ],
    "Ec2InstanceAttributes": {
        "KeyName": "${EC2_KEY_NAME}",
        "InstanceProfile": "${EMR_INSTANCE_PROFILE}",
        "SubnetId": "${EC2_SUBNET_ID}",
        "EmrManagedSlaveSecurityGroup": "sg-xxxxxxxxx",
        "EmrManagedMasterSecurityGroup": "sg-xxxxxxxxx"
    },
    "ServiceRole": "${EMR_SERVICE_ROLE}",
    "JobFlowRole": "${EMR_INSTANCE_PROFILE}",
    "VisibleToAllUsers": true,
    "LogUri": "${LOGS_PATH}/cluster-logs/",
    "AutoTerminationPolicy": {
        "IdleTimeout": 3600
    },
    "ManagedScalingPolicy": {
        "ComputeLimits": {
            "UnitType": "Instances",
            "MinimumCapacityUnits": 2,
            "MaximumCapacityUnits": ${MAX_WORKER_INSTANCES}
        }
    }
}
EOF

    # Create instance groups configuration
    cat > instance-groups.json << EOF
[
    {
        "Name": "Master",
        "Market": "ON_DEMAND",
        "InstanceRole": "MASTER",
        "InstanceType": "${MASTER_INSTANCE_TYPE}",
        "InstanceCount": 1
    },
    {
        "Name": "Workers",
        "Market": "SPOT",
        "BidPrice": "0.15",
        "InstanceRole": "CORE",
        "InstanceType": "${WORKER_INSTANCE_TYPE}",
        "InstanceCount": ${WORKER_INSTANCE_COUNT}
    }
]
EOF

    # Create the cluster
    CLUSTER_ID=$(aws emr create-cluster \
        --cli-input-json file://cluster-config.json \
        --instance-groups file://instance-groups.json \
        --region "$REGION" \
        --query 'ClusterId' \
        --output text)
    
    echo "Cluster created with ID: $CLUSTER_ID"
    echo "Waiting for cluster to be ready..."
    
    # Wait for cluster to be ready
    aws emr wait cluster-running --cluster-id "$CLUSTER_ID" --region "$REGION"
    
    echo "Cluster $CLUSTER_ID is now running"
    export CLUSTER_ID
}

# Function to create EMR Serverless application
create_serverless_app() {
    echo "Creating EMR Serverless application..."
    
    # Create application configuration
    cat > serverless-app-config.json << EOF
{
    "name": "${APP_NAME}",
    "type": "SPARK",
    "releaseLabel": "${EMR_RELEASE}",
    "initialCapacity": {
        "DRIVER": {
            "workerCount": 1,
            "workerConfiguration": {
                "cpu": "2 vCPU",
                "memory": "4 GB",
                "disk": "20 GB"
            }
        },
        "EXECUTOR": {
            "workerCount": 4,
            "workerConfiguration": {
                "cpu": "4 vCPU",
                "memory": "8 GB",
                "disk": "20 GB"
            }
        }
    },
    "maximumCapacity": {
        "DRIVER": {
            "workerCount": 1,
            "workerConfiguration": {
                "cpu": "2 vCPU",
                "memory": "4 GB",
                "disk": "20 GB"
            }
        },
        "EXECUTOR": {
            "workerCount": ${MAX_CAPACITY_UNITS},
            "workerConfiguration": {
                "cpu": "4 vCPU",
                "memory": "8 GB",
                "disk": "20 GB"
            }
        }
    },
    "autoStartConfiguration": {
        "enabled": true
    },
    "autoStopConfiguration": {
        "enabled": true,
        "idleTimeoutMinutes": 15
    }
}
EOF

    # Create the application
    APP_ID=$(aws emr-serverless create-application \
        --cli-input-json file://serverless-app-config.json \
        --region "$REGION" \
        --query 'applicationId' \
        --output text)
    
    echo "EMR Serverless application created with ID: $APP_ID"
    echo "Waiting for application to be ready..."
    
    # Wait for application to be created
    aws emr-serverless get-application \
        --application-id "$APP_ID" \
        --region "$REGION" \
        --query 'application.state' \
        --output text
    
    export SERVERLESS_APP_ID="$APP_ID"
}

# Function to submit job to EMR cluster
submit_cluster_job() {
    echo "Submitting Spark job to EMR cluster: $CLUSTER_ID"
    
    # Create step configuration
    cat > spark-step.json << EOF
[
    {
        "Name": "${APP_NAME}",
        "ActionOnFailure": "TERMINATE_CLUSTER",
        "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": [
                "spark-submit",
                "--deploy-mode", "cluster",
                "--driver-memory", "4g",
                "--driver-cores", "2",
                "--executor-memory", "6g",
                "--executor-cores", "3",
                "--num-executors", "6",
                "--conf", "spark.sql.adaptive.enabled=true",
                "--conf", "spark.sql.adaptive.coalescePartitions.enabled=true",
                "--conf", "spark.sql.adaptive.skewJoin.enabled=true",
                "--conf", "spark.serializer=org.apache.spark.serializer.KryoSerializer",
                "--conf", "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension",
                "--conf", "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog",
                "--jars", "${JAR_FILES}",
                "${S3_CODE_PATH}${PYTHON_FILE}",
                "${INPUT_PATH}",
                "${OUTPUT_PATH}"
            ]
        }
    }
]
EOF

    # Submit the step
    STEP_ID=$(aws emr add-steps \
        --cluster-id "$CLUSTER_ID" \
        --steps file://spark-step.json \
        --region "$REGION" \
        --query 'StepIds[0]' \
        --output text)
    
    echo "Step submitted with ID: $STEP_ID"
    echo "Monitor the job with:"
    echo "  aws emr describe-step --cluster-id $CLUSTER_ID --step-id $STEP_ID --region $REGION"
    
    export STEP_ID
}

# Function to submit job to EMR Serverless
submit_serverless_job() {
    echo "Submitting Spark job to EMR Serverless: ${SERVERLESS_APP_ID}"
    
    # Create job run configuration
    cat > serverless-job.json << EOF
{
    "applicationId": "${SERVERLESS_APP_ID}",
    "executionRoleArn": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/${EMR_SERVERLESS_ROLE}",
    "name": "${APP_NAME}",
    "jobDriver": {
        "sparkSubmit": {
            "entryPoint": "${S3_CODE_PATH}${PYTHON_FILE}",
            "entryPointArguments": [
                "${INPUT_PATH}",
                "${OUTPUT_PATH}"
            ],
            "sparkSubmitParameters": "--conf spark.sql.adaptive.enabled=true --conf spark.sql.adaptive.coalescePartitions.enabled=true --conf spark.serializer=org.apache.spark.serializer.KryoSerializer --jars ${JAR_FILES}"
        }
    },
    "configurationOverrides": {
        "monitoringConfiguration": {
            "s3MonitoringConfiguration": {
                "logUri": "${LOGS_PATH}/serverless-logs/"
            }
        }
    },
    "tags": {
        "Environment": "production",
        "Application": "customer-analytics",
        "Owner": "data-team"
    }
}
EOF

    # Submit the job
    JOB_RUN_ID=$(aws emr-serverless start-job-run \
        --cli-input-json file://serverless-job.json \
        --region "$REGION" \
        --query 'jobRunId' \
        --output text)
    
    echo "Job submitted with ID: $JOB_RUN_ID"
    echo "Monitor the job with:"
    echo "  aws emr-serverless get-job-run --application-id ${SERVERLESS_APP_ID} --job-run-id $JOB_RUN_ID --region $REGION"
    
    export JOB_RUN_ID
}

# Function to check cluster status
check_cluster_status() {
    if [ -z "$CLUSTER_ID" ]; then
        echo "Error: CLUSTER_ID not set"
        exit 1
    fi
    
    echo "Checking status for cluster: $CLUSTER_ID"
    aws emr describe-cluster \
        --cluster-id "$CLUSTER_ID" \
        --region "$REGION" \
        --query 'Cluster.{Name:Name,State:Status.State,StateChangeReason:Status.StateChangeReason.Message}' \
        --output table
}

# Function to check step status
check_step_status() {
    if [ -z "$CLUSTER_ID" ] || [ -z "$STEP_ID" ]; then
        echo "Error: CLUSTER_ID and STEP_ID must be set"
        exit 1
    fi
    
    echo "Checking status for step: $STEP_ID"
    aws emr describe-step \
        --cluster-id "$CLUSTER_ID" \
        --step-id "$STEP_ID" \
        --region "$REGION" \
        --query 'Step.{Name:Name,State:Status.State,StateChangeReason:Status.StateChangeReason.Message}' \
        --output table
}

# Function to list active clusters
list_clusters() {
    echo "Active EMR clusters:"
    aws emr list-clusters \
        --active \
        --region "$REGION" \
        --query 'Clusters[].{Name:Name,Id:Id,State:Status.State,Created:Status.Timeline.CreationDateTime}' \
        --output table
}

# Function to terminate cluster
terminate_cluster() {
    if [ -z "$CLUSTER_ID" ]; then
        echo "Error: CLUSTER_ID not set"
        exit 1
    fi
    
    echo "Terminating cluster: $CLUSTER_ID"
    aws emr terminate-clusters \
        --cluster-ids "$CLUSTER_ID" \
        --region "$REGION"
    
    echo "Cluster termination initiated"
}

# Parse command line arguments
CREATE_CLUSTER=false
TERMINATE_CLUSTER=false
CLUSTER_STATUS=false
STEP_STATUS=false
LIST_CLUSTERS=false
UPLOAD_CODE=false
USE_SERVERLESS=false
CREATE_SERVERLESS_APP=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --create-cluster)
            CREATE_CLUSTER=true
            shift
            ;;
        --terminate-cluster)
            TERMINATE_CLUSTER=true
            shift
            ;;
        --cluster-status)
            CLUSTER_STATUS=true
            shift
            ;;
        --step-status)
            STEP_STATUS=true
            shift
            ;;
        --list-clusters)
            LIST_CLUSTERS=true
            shift
            ;;
        --upload-code)
            UPLOAD_CODE=true
            shift
            ;;
        --serverless)
            USE_SERVERLESS=true
            shift
            ;;
        --create-serverless-app)
            CREATE_SERVERLESS_APP=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main execution
echo "AWS EMR Spark Job Submission Script"
echo "==================================="
echo "Region: $REGION"
echo "S3 Bucket: $S3_BUCKET"
echo "Application: $APP_NAME"
echo "Deployment Mode: $DEPLOYMENT_MODE"
echo "Input Path: $INPUT_PATH"
echo "Output Path: $OUTPUT_PATH"
echo ""

# Execute based on operation
if [ "$LIST_CLUSTERS" = "true" ]; then
    list_clusters
elif [ "$CLUSTER_STATUS" = "true" ]; then
    check_cluster_status
elif [ "$STEP_STATUS" = "true" ]; then
    check_step_status
elif [ "$TERMINATE_CLUSTER" = "true" ]; then
    terminate_cluster
else
    check_prerequisites
    
    if [ "$UPLOAD_CODE" = "true" ]; then
        upload_code
    fi
    
    if [ "$DRY_RUN" = "true" ]; then
        echo "Dry run mode - configurations generated but not submitted"
        exit 0
    fi
    
    if [ "$USE_SERVERLESS" = "true" ] || [ "$CREATE_SERVERLESS_APP" = "true" ]; then
        if [ "$CREATE_SERVERLESS_APP" = "true" ] || [ -z "$SERVERLESS_APP_ID" ]; then
            create_serverless_app
        fi
        submit_serverless_job
    else
        if [ "$CREATE_CLUSTER" = "true" ] || [ -z "$CLUSTER_ID" ]; then
            create_cluster
        fi
        submit_cluster_job
    fi
fi

echo "Operation completed successfully!"