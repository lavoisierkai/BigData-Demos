# Bamboo CI/CD for Data Platform Automation

This directory demonstrates Atlassian Bamboo automation for data platform deployments, showcasing enterprise-grade CI/CD practices for data engineering projects.

## Architecture Overview

```
Bamboo Plans → Build Stages → Test Stages → Deploy Stages → Monitor
```

### Key Components
- **Build Plans**: Automated build and test execution
- **Deployment Projects**: Environment-specific deployments
- **Release Management**: Controlled production releases
- **Integration Testing**: Comprehensive validation pipelines
- **Monitoring**: Performance and health monitoring

## Directory Structure

```
Bamboo/
├── README.md                          # This documentation
└── plans/                             # Bamboo plan configurations
    └── data-platform-build.yaml      # Main build plan implementation
```

**Note**: This is a demonstration of Bamboo CI/CD concepts. The current implementation includes a basic build plan configuration. For a complete enterprise setup, additional directories would include:

- `deployments/` - Deployment project configurations
- `scripts/` - Automation and utility scripts  
- `specs/` - Bamboo Specs as Code (Java-based)
- `environments/` - Environment-specific configurations
- `templates/` - Reusable plan and task templates

## Features Demonstrated

### 1. Bamboo Specs as Code
- **Java-based Configuration**: Version-controlled build plans
- **Dynamic Plan Generation**: Template-based plan creation
- **Environment Parameterization**: Flexible configuration management
- **Automated Plan Updates**: Self-updating build definitions

### 2. Multi-Stage Pipelines
- **Source Code Validation**: Linting, security scanning
- **Build Automation**: Artifact creation and packaging
- **Testing Automation**: Unit, integration, and performance tests
- **Deployment Automation**: Multi-environment deployments

### 3. Enterprise Integration
- **JIRA Integration**: Ticket tracking and release notes
- **Confluence Integration**: Documentation automation
- **BitBucket Integration**: Source code management
- **Slack/Teams Integration**: Notification and collaboration

### 4. Quality Assurance
- **Code Quality Gates**: SonarQube integration
- **Security Scanning**: SAST and dependency checks
- **Performance Testing**: Load and stress testing
- **Compliance Validation**: Regulatory compliance checks

## Getting Started

### Prerequisites
```bash
# Bamboo CLI (if available)
# Java 8 or 11 for Bamboo Specs
java -version

# Required tools for data platform
python --version
terraform --version
docker --version

# Cloud CLI tools
aws --version
az --version
```

### Setup Steps

1. **Configure Bamboo Connection**
```properties
# bamboo.properties
bamboo.url=https://your-bamboo-instance.com
bamboo.username=service-account
bamboo.password=service-token
```

2. **Deploy Bamboo Specs**
```bash
# Compile and deploy specs
cd specs/
mvn clean compile exec:java
```

3. **Configure Environments**
```bash
# Setup environment-specific variables
# Configure deployment environments in Bamboo UI
```

## Plan Configurations

### 1. Data Platform Build Plan
```yaml
# plans/data-platform-build.yaml
plan:
  project-key: DP
  key: BUILD
  name: Data Platform Build
  description: Main build plan for data platform components

stages:
  - Code Quality:
      jobs:
        - Lint and Security Scan:
            tasks:
              - checkout
              - script: |
                  # Python linting
                  flake8 data-pipelines/
                  bandit -r data-pipelines/
                  
                  # Terraform validation
                  terraform fmt -check
                  terraform validate
              - sonar-scanner
              
  - Build and Test:
      jobs:
        - Unit Tests:
            tasks:
              - checkout
              - script: |
                  # Setup Python environment
                  python -m venv venv
                  source venv/bin/activate
                  pip install -r requirements.txt
                  
                  # Run tests
                  pytest tests/unit/ --junitxml=test-results.xml
              - test-parser:
                  type: junit
                  test-results: test-results.xml
                  
        - Integration Tests:
            tasks:
              - checkout
              - docker-compose:
                  file: tests/docker-compose.test.yml
                  action: up
              - script: |
                  # Wait for services
                  sleep 30
                  
                  # Run integration tests
                  pytest tests/integration/ --junitxml=integration-results.xml
              - docker-compose:
                  file: tests/docker-compose.test.yml
                  action: down
                  
  - Package:
      jobs:
        - Create Artifacts:
            tasks:
              - checkout
              - script: |
                  # Build Python wheels
                  python setup.py bdist_wheel
                  
                  # Package Spark applications
                  zip -r spark-apps.zip Spark\ Application/
                  
                  # Package Databricks notebooks
                  zip -r databricks-notebooks.zip Cloud\ Platform/databricks/
                  
                  # Package infrastructure templates
                  zip -r infrastructure.zip DevOps\ Solution/
              - artifact-definition:
                  name: Data Platform Artifacts
                  pattern: "**/*.whl,**/*.zip"
                  shared: true

triggers:
  - repository-polling:
      repository: Data Platform Repository
      
variables:
  python.version: "3.8"
  spark.version: "3.4.0"
  build.environment: "bamboo"

notifications:
  - hipchat:
      room: "Data Engineering"
      notify-committers: true
  - email:
      recipients: "data-team@company.com"
      subject: "Data Platform Build ${bamboo.buildResultKey} ${bamboo.buildState}"
```

### 2. Infrastructure Deployment Plan
```yaml
# plans/infrastructure-plan.yaml
plan:
  project-key: DP
  key: INFRA
  name: Infrastructure Deployment
  description: Deploy data platform infrastructure

stages:
  - Validate Infrastructure:
      jobs:
        - Terraform Validate:
            tasks:
              - checkout
              - script: |
                  cd DevOps\ Solution/Templating/terraform/aws/data-lake/
                  terraform init -backend=false
                  terraform validate
                  terraform fmt -check
                  
        - ARM Template Validate:
            tasks:
              - script: |
                  az deployment group validate \
                    --resource-group rg-dataplatform-dev \
                    --template-file DevOps\ Solution/Azure/arm-templates/azure-data-platform.json \
                    --parameters @DevOps\ Solution/Azure/arm-templates/parameters-dev.json

  - Deploy Infrastructure:
      jobs:
        - Deploy AWS:
            tasks:
              - checkout
              - script: |
                  cd DevOps\ Solution/Templating/terraform/aws/data-lake/
                  terraform init
                  terraform plan -var-file="environments/dev.tfvars" -out=tfplan
                  terraform apply tfplan
                  
        - Deploy Azure:
            tasks:
              - script: |
                  az deployment group create \
                    --resource-group rg-dataplatform-dev \
                    --template-file DevOps\ Solution/Azure/arm-templates/azure-data-platform.json \
                    --parameters @DevOps\ Solution/Azure/arm-templates/parameters-dev.json

manual-stage: Deploy Infrastructure

variables:
  aws.region: "us-west-2"
  azure.location: "East US 2"
  environment: "development"

final-tasks:
  - script: |
      # Health check after deployment
      python scripts/infrastructure-health-check.py
```

## Bamboo Specs as Code

### 1. Build Plan Specification
```java
// specs/build-specs.java
package com.company.bamboo.specs;

import com.atlassian.bamboo.specs.api.BambooSpec;
import com.atlassian.bamboo.specs.api.builders.plan.Plan;
import com.atlassian.bamboo.specs.api.builders.plan.PlanIdentifier;
import com.atlassian.bamboo.specs.api.builders.project.Project;
import com.atlassian.bamboo.specs.util.BambooServer;

@BambooSpec
public class DataPlatformSpecs {
    
    public Plan createDataPlatformBuild() {
        return new Plan(
            new Project()
                .key("DP")
                .name("Data Platform"),
            "BUILD",
            "Data Platform Build")
            .description("Automated build and test for data platform")
            .pluginConfigurations(
                new ConcurrentBuilds()
                    .useSystemWideDefault(false)
                    .maximumNumberOfConcurrentBuilds(2)
            )
            .stages(
                new Stage("Code Quality")
                    .jobs(
                        new Job("Quality Checks", "QC")
                            .tasks(
                                new VcsCheckoutTask()
                                    .description("Checkout source code")
                                    .checkoutItems(
                                        new CheckoutItem()
                                            .repository("Data Platform Repository")
                                    ),
                                new ScriptTask()
                                    .description("Run code quality checks")
                                    .inlineBody(
                                        "#!/bin/bash\n" +
                                        "# Install dependencies\n" +
                                        "pip install flake8 bandit black\n" +
                                        "# Run linting\n" +
                                        "flake8 data-pipelines/ --max-line-length=88\n" +
                                        "# Run security checks\n" +
                                        "bandit -r data-pipelines/\n" +
                                        "# Check code formatting\n" +
                                        "black --check data-pipelines/"
                                    )
                            )
                    ),
                new Stage("Build and Test")
                    .jobs(
                        new Job("Unit Tests", "UT")
                            .tasks(
                                new VcsCheckoutTask()
                                    .description("Checkout source code"),
                                new ScriptTask()
                                    .description("Run unit tests")
                                    .inlineBody(
                                        "#!/bin/bash\n" +
                                        "# Setup test environment\n" +
                                        "python -m venv test-env\n" +
                                        "source test-env/bin/activate\n" +
                                        "pip install -r requirements.txt\n" +
                                        "pip install pytest pytest-cov\n" +
                                        "# Run tests with coverage\n" +
                                        "pytest tests/unit/ --cov=data-pipelines --junitxml=test-results.xml\n"
                                    ),
                                new TestParserTask(TestParserTaskProperties.TestType.JUNIT)
                                    .description("Parse test results")
                                    .resultDirectories("test-results.xml")
                            ),
                        new Job("Integration Tests", "IT")
                            .tasks(
                                new VcsCheckoutTask()
                                    .description("Checkout source code"),
                                new DockerTask()
                                    .description("Start test infrastructure")
                                    .dockerfileLocation("tests/Dockerfile.test")
                                    .imageName("data-platform-test")
                                    .command("up"),
                                new ScriptTask()
                                    .description("Run integration tests")
                                    .inlineBody(
                                        "#!/bin/bash\n" +
                                        "# Wait for services to start\n" +
                                        "sleep 30\n" +
                                        "# Run integration tests\n" +
                                        "pytest tests/integration/ --junitxml=integration-results.xml\n"
                                    ),
                                new DockerTask()
                                    .description("Stop test infrastructure")
                                    .command("down")
                            )
                            .finalTasks(
                                new DockerTask()
                                    .description("Cleanup test infrastructure")
                                    .command("down")
                            )
                    ),
                new Stage("Package")
                    .jobs(
                        new Job("Create Artifacts", "PKG")
                            .tasks(
                                new VcsCheckoutTask()
                                    .description("Checkout source code"),
                                new ScriptTask()
                                    .description("Build packages")
                                    .inlineBody(
                                        "#!/bin/bash\n" +
                                        "# Build Python wheels\n" +
                                        "python setup.py bdist_wheel\n" +
                                        "# Package notebooks\n" +
                                        "zip -r databricks-notebooks.zip Cloud\\ Platform/databricks/\n" +
                                        "# Package Spark applications\n" +
                                        "zip -r spark-applications.zip Spark\\ Application/\n" +
                                        "# Package infrastructure\n" +
                                        "zip -r infrastructure.zip DevOps\\ Solution/\n"
                                    )
                            )
                            .artifacts(
                                new Artifact()
                                    .name("Data Platform Packages")
                                    .copyPattern("**/*.whl")
                                    .copyPattern("**/*.zip")
                                    .shared(true)
                            )
                    )
            )
            .linkedRepositories("Data Platform Repository")
            .triggers(
                new RepositoryPollingTrigger()
                    .description("Poll for changes every 3 minutes")
            )
            .variables(
                new Variable("python.version", "3.8"),
                new Variable("spark.version", "3.4.0"),
                new Variable("environment", "bamboo")
            )
            .notifications(
                new Notification()
                    .type(new HipChatNotification()
                        .room("Data Engineering")
                        .notify(true)
                    )
                    .recipients(
                        new AnyNotificationRecipient(new AtlassianModule("com.atlassian.bamboo.plugins.bamboo-slack:recipient.slack"))
                            .recipientString("data-engineering")
                    )
            );
    }
    
    public static void main(String[] args) throws Exception {
        BambooServer bambooServer = new BambooServer("https://bamboo.company.com");
        new DataPlatformSpecs().createDataPlatformBuild().publish(bambooServer);
    }
}
```

### 2. Deployment Project Specification
```java
// specs/deployment-specs.java
package com.company.bamboo.specs;

import com.atlassian.bamboo.specs.api.BambooSpec;
import com.atlassian.bamboo.specs.api.builders.deployment.Deployment;
import com.atlassian.bamboo.specs.api.builders.deployment.Environment;
import com.atlassian.bamboo.specs.api.builders.deployment.ReleaseNaming;

@BambooSpec
public class DataPlatformDeploymentSpecs {
    
    public Deployment createDataPlatformDeployment() {
        return new Deployment(
            new PlanIdentifier("DP", "BUILD"),
            "Data Platform Deployment")
            .description("Deploy data platform to multiple environments")
            .releaseNaming(new ReleaseNaming("release-${bamboo.buildNumber}"))
            .environments(
                new Environment("Development")
                    .description("Development environment deployment")
                    .tasks(
                        new CleanWorkingDirectoryTask(),
                        new ArtifactDownloaderTask()
                            .description("Download build artifacts")
                            .artifacts(
                                new DownloadItem()
                                    .artifact("Data Platform Packages")
                            ),
                        new ScriptTask()
                            .description("Deploy to development")
                            .inlineBody(
                                "#!/bin/bash\n" +
                                "# Extract artifacts\n" +
                                "unzip infrastructure.zip\n" +
                                "unzip databricks-notebooks.zip\n" +
                                "# Deploy infrastructure\n" +
                                "./scripts/deploy-infrastructure.sh development\n" +
                                "# Deploy data pipelines\n" +
                                "./scripts/deploy-data-pipelines.sh development\n" +
                                "# Run health checks\n" +
                                "python scripts/health-check.py --environment development\n"
                            )
                    )
                    .triggers(
                        new AfterSuccessfulBuildPlanTrigger()
                    ),
                    
                new Environment("Staging")
                    .description("Staging environment deployment")
                    .tasks(
                        new CleanWorkingDirectoryTask(),
                        new ArtifactDownloaderTask()
                            .description("Download build artifacts")
                            .artifacts(
                                new DownloadItem()
                                    .artifact("Data Platform Packages")
                            ),
                        new ScriptTask()
                            .description("Deploy to staging")
                            .inlineBody(
                                "#!/bin/bash\n" +
                                "# Extract artifacts\n" +
                                "unzip infrastructure.zip\n" +
                                "unzip databricks-notebooks.zip\n" +
                                "# Deploy with staging configuration\n" +
                                "./scripts/deploy-infrastructure.sh staging\n" +
                                "./scripts/deploy-data-pipelines.sh staging\n" +
                                "# Run comprehensive tests\n" +
                                "python scripts/integration-test.py --environment staging\n" +
                                "python scripts/performance-test.py --environment staging\n"
                            )
                    )
                    .triggers(
                        new AfterSuccessfulDeploymentTrigger("Development")
                    ),
                    
                new Environment("Production")
                    .description("Production environment deployment")
                    .tasks(
                        new CleanWorkingDirectoryTask(),
                        new ArtifactDownloaderTask()
                            .description("Download build artifacts")
                            .artifacts(
                                new DownloadItem()
                                    .artifact("Data Platform Packages")
                            ),
                        new ScriptTask()
                            .description("Deploy to production")
                            .inlineBody(
                                "#!/bin/bash\n" +
                                "# Extract artifacts\n" +
                                "unzip infrastructure.zip\n" +
                                "unzip databricks-notebooks.zip\n" +
                                "# Deploy with production configuration\n" +
                                "./scripts/deploy-infrastructure.sh production\n" +
                                "./scripts/deploy-data-pipelines.sh production\n" +
                                "# Validate deployment\n" +
                                "python scripts/production-validation.py\n" +
                                "# Send deployment notification\n" +
                                "python scripts/send-deployment-notification.py\n"
                            )
                    )
                    .triggers(
                        new ManualDeploymentTrigger()
                    )
                    .notifications(
                        new Notification()
                            .type(new EmailNotification()
                                .recipients("data-team@company.com", "ops-team@company.com")
                                .subject("Production Deployment Complete")
                            )
                    )
            );
    }
}
```

## Automation Scripts

### 1. Infrastructure Deployment Script
```bash
#!/bin/bash
# scripts/deploy-scripts/deploy-infrastructure.sh

set -e

ENVIRONMENT=$1
if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment>"
    exit 1
fi

echo "Deploying infrastructure to $ENVIRONMENT environment..."

# Load environment-specific configuration
source "environments/${ENVIRONMENT}.properties"

# Deploy AWS infrastructure with Terraform
if [ "$DEPLOY_AWS" == "true" ]; then
    echo "Deploying AWS infrastructure..."
    cd "DevOps Solution/Templating/terraform/aws/data-lake"
    terraform init -backend-config="bucket=${TERRAFORM_STATE_BUCKET}"
    terraform plan -var-file="environments/${ENVIRONMENT}.tfvars" -out=tfplan
    terraform apply tfplan
    cd -
fi

# Deploy Azure infrastructure with ARM templates
if [ "$DEPLOY_AZURE" == "true" ]; then
    echo "Deploying Azure infrastructure..."
    az deployment group create \
        --resource-group "${AZURE_RESOURCE_GROUP}" \
        --template-file "DevOps Solution/Azure/arm-templates/azure-data-platform.json" \
        --parameters "@DevOps Solution/Azure/arm-templates/parameters-${ENVIRONMENT}.json" \
        --parameters projectName="${PROJECT_NAME}" environment="${ENVIRONMENT}"
fi

# Wait for infrastructure to be ready
echo "Waiting for infrastructure to be ready..."
sleep 60

# Validate deployment
python scripts/validate-infrastructure.py --environment "$ENVIRONMENT"

echo "Infrastructure deployment completed successfully!"
```

### 2. Data Pipeline Deployment Script
```bash
#!/bin/bash
# scripts/deploy-scripts/deploy-data-pipelines.sh

set -e

ENVIRONMENT=$1
if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment>"
    exit 1
fi

echo "Deploying data pipelines to $ENVIRONMENT environment..."

# Load environment configuration
source "environments/${ENVIRONMENT}.properties"

# Deploy Databricks notebooks
if [ "$DEPLOY_DATABRICKS" == "true" ]; then
    echo "Deploying Databricks notebooks..."
    databricks workspace import_dir \
        "Cloud Platform/databricks" \
        "/Workspace/DataPlatform/${ENVIRONMENT}" \
        --language PYTHON \
        --overwrite
fi

# Deploy Data Factory pipelines
if [ "$DEPLOY_DATA_FACTORY" == "true" ]; then
    echo "Deploying Data Factory pipelines..."
    
    # Deploy linked services
    az datafactory linked-service create \
        --factory-name "${DATA_FACTORY_NAME}" \
        --resource-group "${AZURE_RESOURCE_GROUP}" \
        --linked-service-name "AzureDataLakeStorage" \
        --properties "@DevOps Solution/Azure/data-factory/linkedServices/AzureDataLakeStorage.json"
    
    # Deploy datasets
    az datafactory dataset create \
        --factory-name "${DATA_FACTORY_NAME}" \
        --resource-group "${AZURE_RESOURCE_GROUP}" \
        --dataset-name "SourceDataset" \
        --properties "@DevOps Solution/Azure/data-factory/datasets/SourceDataset.json"
    
    # Deploy pipelines
    az datafactory pipeline create \
        --factory-name "${DATA_FACTORY_NAME}" \
        --resource-group "${AZURE_RESOURCE_GROUP}" \
        --pipeline "@DevOps Solution/Azure/data-factory/pipelines/ecommerce-etl-pipeline.json"
fi

# Deploy Metorikku configurations
if [ "$DEPLOY_SPARK_JOBS" == "true" ]; then
    echo "Deploying Spark job configurations..."
    
    # Upload Metorikku configurations to S3
    aws s3 cp "Spark Application/metorikku/config/" \
        "s3://${SPARK_CONFIG_BUCKET}/config/" \
        --recursive
    
    # Submit sample job to validate deployment
    spark-submit \
        --class com.yotpo.metorikku.Metorikku \
        --master yarn \
        metorikku.jar \
        --config "s3://${SPARK_CONFIG_BUCKET}/config/ecommerce-etl.yaml" \
        --variables environment="${ENVIRONMENT}"
fi

echo "Data pipeline deployment completed successfully!"
```

### 3. Health Check Script
```python
#!/usr/bin/env python3
# scripts/monitoring-scripts/health-check.py

import argparse
import requests
import boto3
import azure.mgmt.resource
import sys
import time
from typing import Dict, List

def check_aws_resources(environment: str) -> Dict[str, bool]:
    """Check AWS resource health"""
    results = {}
    
    # Initialize AWS clients
    s3_client = boto3.client('s3')
    glue_client = boto3.client('glue')
    emr_client = boto3.client('emr')
    
    try:
        # Check S3 buckets
        bucket_prefix = f"data-lake-{environment}"
        buckets = s3_client.list_buckets()
        data_lake_buckets = [b for b in buckets['Buckets'] 
                           if b['Name'].startswith(bucket_prefix)]
        results['s3_buckets'] = len(data_lake_buckets) >= 3  # raw, processed, curated
        
        # Check Glue catalog
        databases = glue_client.get_databases()
        catalog_db = f"{environment}_data_catalog"
        results['glue_catalog'] = any(db['Name'] == catalog_db 
                                    for db in databases['DatabaseList'])
        
        # Check EMR clusters (if any running)
        clusters = emr_client.list_clusters(ClusterStates=['RUNNING', 'WAITING'])
        results['emr_available'] = True  # EMR service is available
        
    except Exception as e:
        print(f"Error checking AWS resources: {e}")
        results['aws_error'] = str(e)
    
    return results

def check_azure_resources(environment: str) -> Dict[str, bool]:
    """Check Azure resource health"""
    results = {}
    
    try:
        # This would use Azure SDK to check resources
        # For demonstration, we'll simulate the checks
        results['data_factory'] = True
        results['synapse_workspace'] = True
        results['storage_account'] = True
        results['key_vault'] = True
        
    except Exception as e:
        print(f"Error checking Azure resources: {e}")
        results['azure_error'] = str(e)
    
    return results

def check_data_pipelines(environment: str) -> Dict[str, bool]:
    """Check data pipeline health"""
    results = {}
    
    try:
        # Check Databricks workspace (if accessible via API)
        # This would require Databricks API token
        results['databricks_accessible'] = True
        
        # Check recent pipeline runs
        # This would query pipeline execution logs
        results['recent_pipeline_success'] = True
        
        # Check data freshness
        # This would query latest data timestamps
        results['data_freshness_ok'] = True
        
    except Exception as e:
        print(f"Error checking data pipelines: {e}")
        results['pipeline_error'] = str(e)
    
    return results

def check_application_endpoints(environment: str) -> Dict[str, bool]:
    """Check application endpoint health"""
    results = {}
    
    # Define environment-specific endpoints
    endpoints = {
        'development': [
            'http://dev-api.company.com/health',
            'http://dev-dashboard.company.com/api/status'
        ],
        'staging': [
            'http://staging-api.company.com/health',
            'http://staging-dashboard.company.com/api/status'
        ],
        'production': [
            'http://api.company.com/health',
            'http://dashboard.company.com/api/status'
        ]
    }
    
    if environment in endpoints:
        for endpoint in endpoints[environment]:
            try:
                response = requests.get(endpoint, timeout=10)
                results[endpoint] = response.status_code == 200
            except Exception as e:
                print(f"Error checking {endpoint}: {e}")
                results[endpoint] = False
    
    return results

def generate_health_report(checks: Dict[str, Dict[str, bool]]) -> bool:
    """Generate health report and return overall status"""
    print("\n" + "="*50)
    print("HEALTH CHECK REPORT")
    print("="*50)
    
    overall_healthy = True
    
    for category, results in checks.items():
        print(f"\n{category.upper()}:")
        print("-" * 30)
        
        for check, status in results.items():
            if isinstance(status, bool):
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {check}: {'PASS' if status else 'FAIL'}")
                if not status:
                    overall_healthy = False
            else:
                print(f"  ⚠️  {check}: {status}")
                overall_healthy = False
    
    print("\n" + "="*50)
    if overall_healthy:
        print("🎉 OVERALL STATUS: HEALTHY")
        print("All systems are operational.")
    else:
        print("🚨 OVERALL STATUS: UNHEALTHY")
        print("Some systems require attention.")
    print("="*50)
    
    return overall_healthy

def main():
    parser = argparse.ArgumentParser(description='Health check for data platform')
    parser.add_argument('--environment', required=True, 
                       choices=['development', 'staging', 'production'],
                       help='Environment to check')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Starting health check for {args.environment} environment...")
    
    # Perform health checks
    health_checks = {
        'aws_resources': check_aws_resources(args.environment),
        'azure_resources': check_azure_resources(args.environment),
        'data_pipelines': check_data_pipelines(args.environment),
        'application_endpoints': check_application_endpoints(args.environment)
    }
    
    # Generate report
    is_healthy = generate_health_report(health_checks)
    
    # Exit with appropriate code
    sys.exit(0 if is_healthy else 1)

if __name__ == '__main__':
    main()
```

## Best Practices

### 1. Plan Organization
- **Logical Grouping**: Organize plans by domain/function
- **Reusable Templates**: Create templates for common tasks
- **Environment Consistency**: Maintain consistency across environments
- **Documentation**: Document plan purpose and dependencies

### 2. Security & Compliance
- **Secret Management**: Use Bamboo's secure variables
- **Access Control**: Implement role-based permissions
- **Audit Logging**: Enable comprehensive audit trails
- **Compliance Scanning**: Integrate security scanning tools

### 3. Performance Optimization
- **Parallel Execution**: Use parallel stages where possible
- **Artifact Caching**: Cache dependencies and artifacts
- **Resource Management**: Optimize agent usage
- **Build Optimization**: Minimize build times

### 4. Monitoring & Alerting
- **Real-time Monitoring**: Monitor build and deployment status
- **Notification Strategy**: Configure appropriate notifications
- **Metrics Collection**: Collect build and deployment metrics
- **Troubleshooting**: Provide clear error messages and logs

## Troubleshooting Guide

### Common Issues
1. **Build Failures**: Check logs and dependencies
2. **Agent Issues**: Verify agent capabilities and connectivity
3. **Permission Errors**: Check service account permissions
4. **Timeout Issues**: Adjust timeout settings appropriately

### Debug Commands
```bash
# Check Bamboo agent status
curl -u username:password https://bamboo.company.com/rest/api/latest/agent

# View build logs
curl -u username:password https://bamboo.company.com/rest/api/latest/result/PROJECT-PLAN-BUILD/log

# Check plan configuration
curl -u username:password https://bamboo.company.com/rest/api/latest/plan/PROJECT-PLAN
```