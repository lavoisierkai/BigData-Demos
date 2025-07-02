# Azure DevOps CI/CD for Data Platforms

This directory demonstrates modern DevOps practices for data platform deployments using Azure DevOps pipelines, showcasing automated testing, deployment, and monitoring of data solutions.

## Architecture Overview

```
Source Code → Build Pipeline → Test Pipeline → Deploy Pipeline → Monitor
```

### Key Components
- **Infrastructure as Code**: ARM templates and Terraform deployment
- **Data Pipeline CI/CD**: Automated testing and deployment of data pipelines
- **Quality Gates**: Automated testing and validation at each stage
- **Multi-Environment**: Dev, staging, and production deployments
- **Monitoring**: Automated alerts and health checks

## Directory Structure

```
Azure_devops/
├── README.md                           # This documentation
├── pipelines/                          # YAML pipeline definitions
│   ├── infrastructure-pipeline.yml    # Infrastructure deployment
│   └── data-pipeline-ci.yml          # Data pipeline CI/CD
```

**Note**: This demonstrates Azure DevOps CI/CD concepts for data platforms. The current implementation includes basic pipeline definitions for infrastructure and data pipeline automation. For a comprehensive enterprise setup, additional directories would include:

- `templates/` - Reusable pipeline templates for build, test, and deployment stages
- `tests/` - Automated testing framework (unit, integration, data quality, performance)
- `scripts/` - Utility scripts for environment setup, deployment, and rollback procedures
- `environments/` - Environment-specific configurations (dev, staging, production)
- `policies/` - Branch protection rules, deployment gates, and security policies

## Features Demonstrated

### 1. Infrastructure as Code (IaC)
- **ARM Template Deployment**: Azure resources with parameterization
- **Terraform Integration**: Multi-cloud infrastructure management
- **Environment Promotion**: Consistent deployments across environments
- **Rollback Capabilities**: Automated rollback on failures

### 2. Data Pipeline CI/CD
- **Pipeline Validation**: Syntax and logic validation
- **Unit Testing**: Component-level testing
- **Integration Testing**: End-to-end pipeline testing
- **Performance Testing**: Load and stress testing

### 3. Quality Assurance
- **Code Quality**: Static analysis and linting
- **Data Quality**: Automated data validation
- **Security Scanning**: Vulnerability assessment
- **Compliance Checks**: Regulatory compliance validation

### 4. Deployment Strategies
- **Blue-Green Deployment**: Zero-downtime deployments
- **Canary Releases**: Gradual rollout with monitoring
- **Feature Flags**: Controlled feature activation
- **Automated Rollback**: Quick recovery from failures

## Getting Started

### Prerequisites
```bash
# Azure DevOps CLI
az extension add --name azure-devops

# Configure Azure DevOps
az devops configure --defaults organization=https://dev.azure.com/yourorg project=YourProject

# Required Azure permissions
az account show --query user.name
az role assignment list --assignee your-user@domain.com
```

### Setup Steps

1. **Create Service Connections**
```bash
# Azure Resource Manager connection
az devops service-endpoint azurerm create \
  --azure-rm-service-principal-id $servicePrincipalId \
  --azure-rm-subscription-id $subscriptionId \
  --azure-rm-subscription-name "Your Subscription" \
  --name "AzureRM-Connection"
```

2. **Import Pipelines**
```bash
# Import infrastructure pipeline
az pipelines create \
  --name "Infrastructure-Pipeline" \
  --yaml-path pipelines/infrastructure-pipeline.yml \
  --repository-type tfsgit \
  --repository YourRepo
```

3. **Configure Environments**
```bash
# Create development environment
az pipelines environment create \
  --name "Development" \
  --description "Development environment for data platform"
```

## Pipeline Examples

### 1. Infrastructure Deployment Pipeline
```yaml
# pipelines/infrastructure-pipeline.yml
trigger:
  branches:
    include:
    - main
  paths:
    include:
    - infrastructure/*

stages:
- stage: ValidateInfrastructure
  jobs:
  - job: ValidateARM
    steps:
    - task: AzureResourceManagerTemplateDeployment@3
      inputs:
        deploymentScope: 'Resource Group'
        action: 'Create Or Update Resource Group'
        resourceGroupName: '$(ResourceGroupName)'
        location: '$(Location)'
        templateLocation: 'Linked artifact'
        csmFile: 'infrastructure/main.json'
        deploymentMode: 'Validation'
```

### 2. Data Pipeline CI/CD
```yaml
# pipelines/data-pipeline-ci.yml
trigger:
  branches:
    include:
    - main
  paths:
    include:
    - data-pipelines/*

variables:
- group: DataPlatform-Variables

stages:
- stage: Build
  jobs:
  - job: BuildDataPipelines
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '3.8'
    
    - script: |
        pip install -r requirements.txt
        python -m pytest tests/unit/ --junitxml=test-results.xml
      displayName: 'Run Unit Tests'
```

### 3. ML Model Deployment
```yaml
# pipelines/ml-model-pipeline.yml
trigger:
  branches:
    include:
    - main
  paths:
    include:
    - ml-models/*

stages:
- stage: TrainModel
  jobs:
  - job: TrainAndValidate
    steps:
    - task: AzureCLI@2
      inputs:
        azureSubscription: 'AzureRM-Connection'
        scriptType: 'bash'
        scriptLocation: 'inlineScript'
        inlineScript: |
          az ml job create --file ml-training-job.yml
```

## Quality Gates & Policies

### 1. Branch Policies
```json
{
  "type": {
    "id": "fa4e907d-c16b-4a4c-9dfa-4906e5d171dd"
  },
  "isEnabled": true,
  "isBlocking": true,
  "settings": {
    "minimumApproverCount": 2,
    "creatorVoteCounts": false,
    "allowDownvotes": false,
    "resetOnSourcePush": true
  }
}
```

### 2. Deployment Gates
```json
{
  "id": 1,
  "name": "Data Quality Gate",
  "conditions": [
    {
      "name": "Data Quality Check",
      "conditionType": "query",
      "value": "SELECT COUNT(*) FROM validation_results WHERE status = 'FAILED'"
    }
  ],
  "timeout": 1440
}
```

## Testing Strategies

### 1. Unit Testing
```python
# tests/unit/test_data_transformation.py
import pytest
from pyspark.sql import SparkSession
from data_pipelines.transformations import clean_customer_data

def test_clean_customer_data():
    spark = SparkSession.builder.appName("test").getOrCreate()
    
    # Create test data
    test_data = [("1", "John", "Doe", "john@email.com")]
    df = spark.createDataFrame(test_data, ["id", "first_name", "last_name", "email"])
    
    # Apply transformation
    result = clean_customer_data(df)
    
    # Assert results
    assert result.count() == 1
    assert result.filter("email IS NOT NULL").count() == 1
```

### 2. Integration Testing
```python
# tests/integration/test_end_to_end_pipeline.py
def test_complete_data_pipeline():
    # Setup test environment
    setup_test_data()
    
    # Run data pipeline
    result = run_data_pipeline()
    
    # Validate results
    assert_data_quality(result)
    assert_business_rules(result)
    
    # Cleanup
    cleanup_test_data()
```

### 3. Data Quality Testing
```sql
-- tests/data-quality/customer_data_quality.sql
SELECT 
  'customer_data' as table_name,
  COUNT(*) as total_records,
  SUM(CASE WHEN email IS NULL THEN 1 ELSE 0 END) as null_emails,
  SUM(CASE WHEN email NOT LIKE '%@%' THEN 1 ELSE 0 END) as invalid_emails
FROM customers
HAVING null_emails > 0 OR invalid_emails > 0
```

## Environment Management

### 1. Development Environment
```yaml
# environments/dev.yml
variables:
  resourceGroupName: 'rg-dataplatform-dev'
  storageAccountName: 'stadataplatformdev'
  synapseWorkspaceName: 'synapse-dataplatform-dev'
  environment: 'development'
  costCenter: 'engineering'
```

### 2. Production Environment
```yaml
# environments/prod.yml
variables:
  resourceGroupName: 'rg-dataplatform-prod'
  storageAccountName: 'stadataplatformprod'
  synapseWorkspaceName: 'synapse-dataplatform-prod'
  environment: 'production'
  costCenter: 'operations'
```

## Monitoring & Alerting

### 1. Pipeline Monitoring
```yaml
# pipelines/monitoring-pipeline.yml
schedules:
- cron: "0 */6 * * *"  # Every 6 hours
  displayName: Health Check Schedule
  branches:
    include:
    - main

jobs:
- job: HealthCheck
  steps:
  - task: AzureCLI@2
    inputs:
      azureSubscription: 'AzureRM-Connection'
      scriptType: 'bash'
      scriptLocation: 'inlineScript'
      inlineScript: |
        # Check pipeline health
        python scripts/health-check.py
        
        # Send alerts if needed
        if [ $? -ne 0 ]; then
          python scripts/send-alert.py
        fi
```

### 2. Performance Monitoring
```python
# scripts/performance-monitor.py
import azure.monitor.query as monitor
from datetime import datetime, timedelta

def check_pipeline_performance():
    # Query Azure Monitor for pipeline metrics
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    query = """
    AzureDiagnostics
    | where TimeGenerated between (datetime({start}) .. datetime({end}))
    | where Category == "PipelineRuns"
    | summarize avg(DurationInMs) by bin(TimeGenerated, 1h)
    """.format(start=start_time.isoformat(), end=end_time.isoformat())
    
    results = monitor_client.query_workspace(workspace_id, query)
    
    # Check for performance degradation
    for row in results.tables[0].rows:
        if row[1] > threshold:  # Duration threshold
            send_performance_alert(row)
```

## Security & Compliance

### 1. Secret Management
```yaml
# Use Azure Key Vault for secrets
steps:
- task: AzureKeyVault@2
  inputs:
    azureSubscription: 'AzureRM-Connection'
    KeyVaultName: 'kv-dataplatform'
    SecretsFilter: 'DatabaseConnectionString,ApiKey'
    RunAsPreJob: true

- script: |
    echo "##vso[task.setvariable variable=connectionString;issecret=true]$(DatabaseConnectionString)"
  displayName: 'Set Secret Variables'
```

### 2. Compliance Scanning
```yaml
# Compliance validation
- task: ms-codeanalysis.vss-microsoft-security-code-analysis-devops.build-task-credscan.CredScan@3
  displayName: 'Run Credential Scanner'
  inputs:
    toolMajorVersion: 'V2'
    scanFolder: '$(Build.SourcesDirectory)'
    debugMode: false
```

## Disaster Recovery

### 1. Backup Procedures
```powershell
# scripts/backup-environment.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$EnvironmentName,
    
    [Parameter(Mandatory=$true)]
    [string]$BackupLocation
)

# Backup Data Factory pipelines
$dataFactory = Get-AzDataFactoryV2 -ResourceGroupName $resourceGroup -Name $dataFactoryName
Export-AzDataFactoryV2 -DataFactory $dataFactory -BackupLocation $BackupLocation

# Backup Synapse artifacts
$synapseArtifacts = Get-AzSynapseNotebook -WorkspaceName $workspaceName
foreach ($artifact in $synapseArtifacts) {
    Export-AzSynapseNotebook -WorkspaceName $workspaceName -Name $artifact.Name -OutputFolder $BackupLocation
}
```

### 2. Rollback Procedures
```yaml
# Automated rollback on failure
- stage: Rollback
  condition: failed()
  jobs:
  - deployment: RollbackProduction
    environment: Production
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureResourceManagerTemplateDeployment@3
            inputs:
              deploymentScope: 'Resource Group'
              action: 'Create Or Update Resource Group'
              resourceGroupName: '$(ResourceGroupName)'
              templateLocation: 'URL of the file'
              csmFileLink: '$(PreviousDeploymentTemplate)'
              deploymentMode: 'Complete'
```

## Best Practices

1. **Version Control**
   - All pipeline definitions in source control
   - Semantic versioning for releases
   - Branch protection policies

2. **Testing Strategy**
   - Unit tests for all transformations
   - Integration tests for complete pipelines
   - Performance tests for large datasets

3. **Security**
   - Least privilege access
   - Secret management with Key Vault
   - Regular security scanning

4. **Monitoring**
   - Comprehensive logging
   - Real-time alerting
   - Performance monitoring

5. **Documentation**
   - Pipeline documentation
   - Runbook procedures
   - Troubleshooting guides

## Troubleshooting Guide

### Common Issues
1. **Permission Errors**: Check service principal permissions
2. **Template Failures**: Validate ARM template syntax
3. **Test Failures**: Review test data and assertions
4. **Deployment Timeouts**: Increase timeout settings

### Debug Commands
```bash
# Check pipeline run status
az pipelines runs show --id <run-id>

# View pipeline logs
az pipelines runs show --id <run-id> --open

# Check service connection
az devops service-endpoint list --query "[?name=='AzureRM-Connection']"
```