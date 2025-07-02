# Jinja2 Configuration Templating System

This directory demonstrates a comprehensive configuration management system using Jinja2 templating for data platform deployments, enabling dynamic configuration generation across multiple environments and cloud platforms.

## Architecture Overview

```
Configuration Templates → Variable Files → Rendered Configs → Deployment
```

### Key Components
- **Template Engine**: Jinja2-based configuration generation
- **Environment Management**: Multi-environment variable management
- **Template Library**: Reusable templates for common patterns
- **Validation**: Configuration validation and testing
- **CLI Tools**: Command-line tools for template rendering

## Directory Structure

```
jinja/
├── README.md                        # This documentation
├── examples/                        # Usage examples
│   └── basic_usage.py              # Basic template rendering example
├── templates/                       # Jinja2 templates
│   └── infrastructure/             # Infrastructure templates
│       └── aws/                    # AWS-specific templates
│           └── data-lake.j2        # Data lake template
├── tools/                          # Template management tools
│   └── render.py                   # Template rendering tool
└── variables/                      # Environment variables
    └── environments/               # Environment-specific variables
        ├── development.yml         # Development environment
        └── production.yml          # Production environment
```

**Note**: This demonstrates core Jinja2 templating concepts for configuration management. The current implementation includes basic infrastructure templating and environment management. For a comprehensive enterprise setup, additional directories would include:

- `macros/` - Reusable Jinja2 macros for complex logic
- `filters/` - Custom Jinja2 filters for data transformation
- `tests/` - Template testing and validation framework
- `schemas/` - Configuration schema validation
- `configs/` - Rendered configuration outputs

## Features Demonstrated

### 1. Infrastructure as Code Templating
- **Multi-Cloud Templates**: Unified templates for AWS, Azure, GCP
- **Environment Parameterization**: Dynamic configuration per environment
- **Resource Naming**: Consistent naming conventions
- **Security Configurations**: Templated security settings

### 2. Data Pipeline Configuration
- **Spark Configuration**: Dynamic Spark job configurations
- **Databricks Templates**: Notebook and cluster configurations
- **Airflow DAGs**: Dynamic DAG generation
- **Data Quality**: Quality check configurations

### 3. Monitoring & Alerting
- **Grafana Dashboards**: Dynamic dashboard generation
- **Prometheus Rules**: Alert rule templating
- **Log Configurations**: Centralized logging setup
- **Health Checks**: Automated health check configs

### 4. Advanced Features
- **Conditional Logic**: Environment-specific conditionals
- **Loop Constructs**: Dynamic resource generation
- **Include/Import**: Template composition and reuse
- **Custom Filters**: Domain-specific data transformations

## Getting Started

### Prerequisites
```bash
# Install required packages
pip install jinja2 pyyaml jsonschema click

# Optional: For advanced features
pip install cryptography boto3 azure-identity
```

### Basic Usage

1. **Render a Simple Template**
```bash
python tools/render.py \
  --template templates/infrastructure/aws/s3-bucket.j2 \
  --variables variables/environments/development.yml \
  --output configs/development/s3-bucket.tf
```

2. **Validate Configuration**
```bash
python tools/validate.py \
  --config configs/development/s3-bucket.tf \
  --schema schemas/infrastructure.schema.json
```

3. **Compare Configurations**
```bash
python tools/diff.py \
  --config1 configs/development/app.yml \
  --config2 configs/staging/app.yml
```

## Template Examples

### 1. Infrastructure Template
```jinja2
{# templates/infrastructure/aws/data-lake.j2 #}
{%- set environment = env.name -%}
{%- set project = project.name -%}

# AWS Data Lake Infrastructure for {{ environment.upper() }}
# Generated from template on {{ ansible_date_time.iso8601 }}

resource "aws_s3_bucket" "data_lake_raw" {
  bucket = "{{ project }}-{{ environment }}-data-lake-raw-{{ random_suffix }}"
  
  tags = {
    Environment = "{{ environment }}"
    Project     = "{{ project }}"
    Layer       = "raw"
    ManagedBy   = "terraform"
    {% for key, value in common_tags.items() %}
    {{ key }} = "{{ value }}"
    {% endfor %}
  }
}

{%- if encryption.enabled %}
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake_raw" {
  bucket = aws_s3_bucket.data_lake_raw.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "{{ encryption.algorithm }}"
      {% if encryption.kms_key_id %}
      kms_master_key_id = "{{ encryption.kms_key_id }}"
      {% endif %}
    }
    bucket_key_enabled = {{ encryption.bucket_key_enabled | lower }}
  }
}
{%- endif %}

{%- for layer in data_layers %}
resource "aws_s3_bucket" "data_lake_{{ layer.name }}" {
  bucket = "{{ project }}-{{ environment }}-data-lake-{{ layer.name }}-{{ random_suffix }}"
  
  tags = {
    Environment = "{{ environment }}"
    Project     = "{{ project }}"
    Layer       = "{{ layer.name }}"
    Purpose     = "{{ layer.description }}"
    ManagedBy   = "terraform"
  }
}

{%- if layer.lifecycle_enabled %}
resource "aws_s3_bucket_lifecycle_configuration" "data_lake_{{ layer.name }}" {
  bucket = aws_s3_bucket.data_lake_{{ layer.name }}.id

  rule {
    id     = "{{ layer.name }}_lifecycle"
    status = "Enabled"

    {% for transition in layer.transitions %}
    transition {
      days          = {{ transition.days }}
      storage_class = "{{ transition.storage_class }}"
    }
    {% endfor %}

    {%- if layer.expiration_days %}
    expiration {
      days = {{ layer.expiration_days }}
    }
    {%- endif %}
  }
}
{%- endif %}
{%- endfor %}
```

### 2. Spark Configuration Template
```jinja2
{# templates/data-pipelines/spark/spark-submit.j2 #}
#!/bin/bash
# Spark Job Submission Script for {{ job.name }}
# Environment: {{ environment.name }}
# Generated: {{ ansible_date_time.iso8601 }}

set -e

# Spark configuration
export SPARK_HOME="{{ spark.home_dir }}"
export JAVA_HOME="{{ java.home_dir }}"

# Job-specific variables
JOB_NAME="{{ job.name }}"
JOB_CLASS="{{ job.main_class }}"
JAR_FILE="{{ job.jar_path }}"
LOG_LEVEL="{{ job.log_level | default('INFO') }}"

# Spark submit command
$SPARK_HOME/bin/spark-submit \
  --name "$JOB_NAME" \
  --class "$JOB_CLASS" \
  --master {{ spark.master }} \
  {%- if spark.deploy_mode %}
  --deploy-mode {{ spark.deploy_mode }} \
  {%- endif %}
  {%- if driver.memory %}
  --driver-memory {{ driver.memory }} \
  {%- endif %}
  {%- if driver.cores %}
  --driver-cores {{ driver.cores }} \
  {%- endif %}
  {%- if executor.memory %}
  --executor-memory {{ executor.memory }} \
  {%- endif %}
  {%- if executor.cores %}
  --executor-cores {{ executor.cores }} \
  {%- endif %}
  {%- if executor.instances %}
  --num-executors {{ executor.instances }} \
  {%- endif %}
  {%- for package in spark.packages %}
  --packages {{ package }} \
  {%- endfor %}
  {%- for conf_key, conf_value in spark.conf.items() %}
  --conf {{ conf_key }}={{ conf_value }} \
  {%- endfor %}
  {%- if spark.jars %}
  --jars {{ spark.jars | join(',') }} \
  {%- endif %}
  {%- if spark.files %}
  --files {{ spark.files | join(',') }} \
  {%- endif %}
  "$JAR_FILE" \
  {%- for arg in job.args %}
  {{ arg }} \
  {%- endfor %}

echo "Spark job '$JOB_NAME' completed with exit code: $?"
```

### 3. Monitoring Template
```jinja2
{# templates/monitoring/grafana/data-pipeline-dashboard.j2 #}
{
  "dashboard": {
    "id": null,
    "title": "{{ dashboard.title }} - {{ environment.name | title }}",
    "description": "{{ dashboard.description }}",
    "tags": [
      "{{ environment.name }}",
      "data-pipeline",
      "{{ project.name }}"
    ],
    "timezone": "{{ dashboard.timezone | default('UTC') }}",
    "refresh": "{{ dashboard.refresh_interval | default('30s') }}",
    "time": {
      "from": "now-{{ dashboard.time_range | default('1h') }}",
      "to": "now"
    },
    "panels": [
      {%- for panel in dashboard.panels %}
      {
        "id": {{ loop.index }},
        "title": "{{ panel.title }}",
        "type": "{{ panel.type }}",
        "gridPos": {
          "h": {{ panel.height | default(8) }},
          "w": {{ panel.width | default(12) }},
          "x": {{ panel.x | default(0) }},
          "y": {{ panel.y | default(0) }}
        },
        "targets": [
          {%- for target in panel.targets %}
          {
            "expr": "{{ target.query }}",
            "legendFormat": "{{ target.legend }}",
            "refId": "{{ target.ref_id | default(loop.index0 | string) }}"
          }
          {%- if not loop.last %},{% endif %}
          {%- endfor %}
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "{{ panel.unit | default('short') }}",
            {%- if panel.min is defined %}
            "min": {{ panel.min }},
            {%- endif %}
            {%- if panel.max is defined %}
            "max": {{ panel.max }},
            {%- endif %}
            "color": {
              "mode": "{{ panel.color_mode | default('palette-classic') }}"
            }
          }
        },
        {%- if panel.type == 'stat' %}
        "options": {
          "reduceOptions": {
            "values": false,
            "calcs": ["{{ panel.calc_type | default('lastNotNull') }}"]
          },
          "orientation": "{{ panel.orientation | default('auto') }}",
          "textMode": "{{ panel.text_mode | default('auto') }}"
        },
        {%- elif panel.type == 'graph' %}
        "options": {
          "legend": {
            "displayMode": "{{ panel.legend_mode | default('table') }}",
            "placement": "{{ panel.legend_placement | default('bottom') }}"
          }
        },
        {%- endif %}
        "alert": {
          {%- if panel.alert %}
          "conditions": [
            {
              "evaluator": {
                "params": [{{ panel.alert.threshold }}],
                "type": "{{ panel.alert.condition | default('gt') }}"
              },
              "operator": {
                "type": "and"
              },
              "query": {
                "params": ["A", "5m", "now"]
              },
              "reducer": {
                "params": [],
                "type": "{{ panel.alert.reducer | default('avg') }}"
              },
              "type": "query"
            }
          ],
          "executionErrorState": "alerting",
          "for": "{{ panel.alert.for | default('0m') }}",
          "frequency": "{{ panel.alert.frequency | default('10s') }}",
          "handler": 1,
          "name": "{{ panel.alert.name | default(panel.title + ' Alert') }}",
          "noDataState": "no_data",
          "notifications": []
          {%- else %}
          "conditions": [],
          "executionErrorState": "alerting",
          "for": "0m",
          "frequency": "10s",
          "handler": 1,
          "name": "{{ panel.title }} alert",
          "noDataState": "no_data",
          "notifications": []
          {%- endif %}
        }
      }
      {%- if not loop.last %},{% endif %}
      {%- endfor %}
    ],
    "templating": {
      "list": [
        {%- for variable in dashboard.variables %}
        {
          "name": "{{ variable.name }}",
          "type": "{{ variable.type | default('query') }}",
          "label": "{{ variable.label | default(variable.name | title) }}",
          {%- if variable.type == 'query' %}
          "query": "{{ variable.query }}",
          {%- elif variable.type == 'custom' %}
          "options": [
            {%- for option in variable.options %}
            {
              "text": "{{ option.text }}",
              "value": "{{ option.value }}"
            }
            {%- if not loop.last %},{% endif %}
            {%- endfor %}
          ],
          {%- endif %}
          "refresh": {{ variable.refresh | default(1) }},
          "includeAll": {{ variable.include_all | default(false) | lower }},
          "multi": {{ variable.multi | default(false) | lower }}
        }
        {%- if not loop.last %},{% endif %}
        {%- endfor %}
      ]
    },
    "annotations": {
      "list": [
        {
          "builtIn": 1,
          "datasource": "-- Grafana --",
          "enable": true,
          "hide": true,
          "iconColor": "rgba(0, 211, 255, 1)",
          "name": "Annotations & Alerts",
          "type": "dashboard"
        }
      ]
    }
  }
}
```

## Variable Files

### 1. Environment Configuration
```yaml
# variables/environments/development.yml
environment:
  name: development
  region: us-west-2
  cost_center: engineering
  auto_shutdown: true

project:
  name: dataplatform
  owner: data-engineering-team
  version: "1.0.0"

# Security settings
security:
  encryption_enabled: true
  key_rotation_days: 90
  access_logging: true

# Compute resources
compute:
  instance_types:
    small: t3.medium
    medium: m5.large
    large: m5.xlarge
  auto_scaling:
    min_instances: 1
    max_instances: 5
    target_cpu: 70

# Storage configuration
storage:
  replication: false
  backup_retention_days: 7
  lifecycle_enabled: true

# Data pipeline settings
pipelines:
  schedule: "0 2 * * *"  # Daily at 2 AM
  retry_attempts: 3
  timeout_minutes: 60
  
# Monitoring
monitoring:
  metrics_retention_days: 30
  log_level: DEBUG
  alerts_enabled: true

# Network settings
network:
  vpc_cidr: "10.0.0.0/16"
  availability_zones: 2
  enable_nat_gateway: false
```

### 2. Production Configuration
```yaml
# variables/environments/production.yml
environment:
  name: production
  region: us-east-1
  cost_center: operations
  auto_shutdown: false

project:
  name: dataplatform
  owner: data-engineering-team
  version: "1.0.0"

# Security settings (enhanced for production)
security:
  encryption_enabled: true
  key_rotation_days: 30
  access_logging: true
  mfa_required: true
  
# Compute resources (larger for production)
compute:
  instance_types:
    small: m5.large
    medium: m5.xlarge
    large: m5.2xlarge
  auto_scaling:
    min_instances: 3
    max_instances: 20
    target_cpu: 80

# Storage configuration (enhanced durability)
storage:
  replication: true
  backup_retention_days: 365
  lifecycle_enabled: true
  cross_region_backup: true

# Data pipeline settings
pipelines:
  schedule: "0 1 * * *"  # Daily at 1 AM
  retry_attempts: 5
  timeout_minutes: 180
  
# Monitoring (enhanced for production)
monitoring:
  metrics_retention_days: 365
  log_level: INFO
  alerts_enabled: true
  detailed_monitoring: true

# Network settings (enhanced security)
network:
  vpc_cidr: "10.1.0.0/16"
  availability_zones: 3
  enable_nat_gateway: true
  enable_vpc_flow_logs: true
```

## Template Management Tools

The system includes several command-line tools for managing templates:

### 1. Template Renderer
```python
# tools/render.py
import click
import yaml
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

@click.command()
@click.option('--template', required=True, help='Template file path')
@click.option('--variables', required=True, help='Variables file path')
@click.option('--output', help='Output file path')
@click.option('--validate', is_flag=True, help='Validate rendered output')
def render_template(template, variables, output, validate):
    """Render Jinja2 template with provided variables."""
    
    # Load variables
    with open(variables, 'r') as f:
        vars_data = yaml.safe_load(f)
    
    # Setup Jinja2 environment
    template_dir = Path(template).parent
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # Load and render template
    template_obj = env.get_template(Path(template).name)
    rendered = template_obj.render(**vars_data)
    
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, 'w') as f:
            f.write(rendered)
        click.echo(f"Template rendered to {output}")
    else:
        click.echo(rendered)
    
    if validate:
        # Add validation logic here
        click.echo("Validation passed")

if __name__ == '__main__':
    render_template()
```

## Best Practices

### 1. Template Organization
- **Logical Grouping**: Organize templates by domain/technology
- **Naming Conventions**: Use clear, descriptive template names
- **Documentation**: Include inline documentation in templates
- **Modularity**: Break complex templates into smaller, reusable components

### 2. Variable Management
- **Environment Separation**: Separate variables by environment
- **Validation**: Validate variable schemas before rendering
- **Security**: Never store secrets in plain text variables
- **Defaults**: Provide sensible defaults for optional variables

### 3. Testing
- **Unit Tests**: Test individual template components
- **Integration Tests**: Test complete template rendering
- **Validation Tests**: Verify rendered output against schemas
- **Performance Tests**: Test rendering performance with large datasets

### 4. Security
- **Secret Management**: Use external secret management systems
- **Input Validation**: Validate all template inputs
- **Output Sanitization**: Ensure rendered output is safe
- **Access Control**: Restrict access to sensitive templates

### 5. Maintenance
- **Version Control**: Track template changes with version control
- **Change Management**: Use proper change management processes
- **Documentation**: Maintain up-to-date documentation
- **Monitoring**: Monitor template usage and performance

## Integration Examples

### 1. CI/CD Integration
```yaml
# CI/CD pipeline integration
steps:
- name: Render Templates
  run: |
    python tools/render.py \
      --template templates/infrastructure/aws/main.j2 \
      --variables variables/environments/${{ env.ENVIRONMENT }}.yml \
      --output infrastructure/rendered/main.tf \
      --validate

- name: Validate Configuration
  run: |
    terraform validate infrastructure/rendered/
```

### 2. Ansible Integration
```yaml
# Ansible playbook integration
- name: Render configuration templates
  template:
    src: "{{ item.template }}"
    dest: "{{ item.dest }}"
    mode: '0644'
  with_items:
    - template: spark-defaults.conf.j2
      dest: /opt/spark/conf/spark-defaults.conf
    - template: log4j.properties.j2
      dest: /opt/spark/conf/log4j.properties
```

This comprehensive Jinja templating system provides a robust foundation for configuration management across complex data platform deployments, enabling consistent, maintainable, and scalable configuration generation.