#!/usr/bin/env python3
"""
Basic Jinja2 Templating Usage Example
====================================

This example demonstrates basic usage of the Jinja2 templating system
for data platform configuration management.

Usage:
    python basic_usage.py
"""

import os
import sys
import yaml
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

from render import TemplateRenderer

def main():
    """Demonstrate basic template rendering functionality."""
    
    print("=== Jinja2 Template System Demo ===\n")
    
    # Get paths
    base_dir = Path(__file__).parent.parent
    template_dir = base_dir / 'templates' / 'infrastructure' / 'aws'
    variables_dir = base_dir / 'variables' / 'environments'
    output_dir = base_dir / 'configs' / 'development'
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize renderer
    print("1. Initializing template renderer...")
    renderer = TemplateRenderer([str(template_dir)])
    
    # Load development variables
    print("2. Loading development environment variables...")
    dev_vars_file = variables_dir / 'development.yml'
    variables = renderer.load_variables([str(dev_vars_file)])
    
    print(f"   Loaded {len(variables)} variable groups")
    print(f"   Environment: {variables['environment']['name']}")
    print(f"   Project: {variables['project']['name']}")
    print(f"   Region: {variables['environment']['region']}")
    
    # Render AWS data lake template
    print("\n3. Rendering AWS data lake infrastructure template...")
    template_name = 'data-lake.j2'
    
    try:
        rendered_content = renderer.render_template(template_name, variables)
        
        # Write to output file
        output_file = output_dir / 'data-lake.tf'
        with open(output_file, 'w') as f:
            f.write(rendered_content)
        
        print(f"   ✓ Template rendered successfully to: {output_file}")
        print(f"   ✓ Generated {len(rendered_content.splitlines())} lines of Terraform code")
        
        # Show some sample content
        lines = rendered_content.splitlines()
        print(f"\n   Sample content (first 10 lines):")
        for i, line in enumerate(lines[:10]):
            print(f"     {i+1:2d}: {line}")
        
        if len(lines) > 10:
            print(f"     ... ({len(lines) - 10} more lines)")
    
    except Exception as e:
        print(f"   ✗ Error rendering template: {e}")
        return False
    
    # Demonstrate variable inspection
    print("\n4. Template variables used:")
    print(f"   - Data layers: {len(variables['data_layers'])}")
    for layer in variables['data_layers']:
        print(f"     • {layer['name']}: {layer['description']}")
    
    print(f"   - EMR enabled: {variables['emr']['enabled']}")
    print(f"   - Security encryption: {variables['security']['encryption']['enabled']}")
    print(f"   - Auto scaling: {variables['emr']['auto_scaling']['enabled']}")
    
    # Generate summary
    print("\n5. Generation Summary:")
    print(f"   ✓ Template: {template_name}")
    print(f"   ✓ Variables: {dev_vars_file.name}")
    print(f"   ✓ Output: {output_file}")
    print(f"   ✓ Environment: {variables['environment']['name']}")
    
    return True

def demonstrate_production_differences():
    """Show differences between development and production configurations."""
    
    print("\n=== Development vs Production Comparison ===\n")
    
    # Get paths
    base_dir = Path(__file__).parent.parent
    variables_dir = base_dir / 'variables' / 'environments'
    
    # Initialize renderer
    renderer = TemplateRenderer()
    
    # Load both environments
    dev_vars = renderer.load_variables([str(variables_dir / 'development.yml')])
    prod_vars = renderer.load_variables([str(variables_dir / 'production.yml')])
    
    print("Key differences between environments:")
    print()
    
    # Compare key settings
    comparisons = [
        ('Environment Name', 'environment.name'),
        ('Region', 'environment.region'),
        ('Auto Shutdown', 'environment.auto_shutdown'),
        ('EMR Master Instance', 'emr.master_instance_type'),
        ('EMR Core Instances', 'emr.core_instance_count'),
        ('Auto Scaling Enabled', 'emr.auto_scaling.enabled'),
        ('Max Auto Scale', 'emr.auto_scaling.max_capacity'),
        ('Encryption Algorithm', 'security.encryption.algorithm'),
        ('Backup Retention', 'storage.backup_retention_days'),
        ('Monitoring Level', 'monitoring.log_level'),
    ]
    
    for description, path in comparisons:
        dev_val = get_nested_value(dev_vars, path)
        prod_val = get_nested_value(prod_vars, path)
        
        print(f"{description:20s} | Dev: {str(dev_val):15s} | Prod: {str(prod_val):15s}")
    
    print(f"\nData layers comparison:")
    print(f"{'Layer':15s} | {'Dev Retention':15s} | {'Prod Retention':15s}")
    print("-" * 50)
    
    for i, (dev_layer, prod_layer) in enumerate(zip(dev_vars['data_layers'], prod_vars['data_layers'])):
        dev_retention = dev_layer.get('expiration_days', 'N/A')
        prod_retention = prod_layer.get('expiration_days', 'N/A')
        print(f"{dev_layer['name']:15s} | {str(dev_retention):15s} | {str(prod_retention):15s}")

def get_nested_value(data, path):
    """Get nested value from dictionary using dot notation."""
    keys = path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return 'N/A'
    return value

def demonstrate_custom_filters():
    """Demonstrate custom Jinja2 filters."""
    
    print("\n=== Custom Filter Demonstration ===\n")
    
    from jinja2 import Environment
    
    # Create template with custom filters
    template_content = """
{%- set test_data = {"name": "test", "value": 12345} -%}
Original JSON: {{ test_data | tojson }}
Pretty JSON: {{ test_data | to_json_pretty }}
Base64 Encoded: {{ "hello world" | to_base64 }}
SHA256 Hash: {{ "sensitive_data" | hash_sha256 }}
Random String: {{ "" | random_string(12) }}
Current Time: {{ current_timestamp() }}
Environment Variable: {{ "USER" | env_var("unknown") }}
"""
    
    # Initialize renderer
    base_dir = Path(__file__).parent.parent
    renderer = TemplateRenderer([str(base_dir)])
    
    # Render with custom filters
    try:
        rendered = renderer.env.from_string(template_content).render()
        print("Custom filter examples:")
        print(rendered)
    except Exception as e:
        print(f"Error demonstrating filters: {e}")

if __name__ == '__main__':
    print("Starting Jinja2 Template System Demo...")
    print("=" * 50)
    
    # Run basic demo
    success = main()
    
    if success:
        # Show environment differences
        demonstrate_production_differences()
        
        # Show custom filters
        demonstrate_custom_filters()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nNext steps:")
        print("1. Explore the generated Terraform files in configs/")
        print("2. Try rendering with production variables")
        print("3. Create your own templates and variables")
        print("4. Use the CLI tool: python tools/render.py --help")
    else:
        print("\nDemo failed. Check the error messages above.")
        sys.exit(1)