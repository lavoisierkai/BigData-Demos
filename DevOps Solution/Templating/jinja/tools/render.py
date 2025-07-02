#!/usr/bin/env python3
"""
Template Rendering Tool
=====================

Command-line tool for rendering Jinja2 templates with variable substitution,
validation, and advanced features for data platform configuration management.

Usage:
    python render.py --template path/to/template.j2 --variables vars.yml --output result.txt
    python render.py --template-dir templates/ --variables-dir vars/ --output-dir configs/
    python render.py --batch-render batch_config.yml
"""

import click
import yaml
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from jinja2.exceptions import TemplateError, TemplateNotFound
except ImportError:
    print("Error: jinja2 is required. Install with: pip install jinja2")
    sys.exit(1)

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

# Custom Jinja2 filters
def to_base64(value):
    """Encode string to base64."""
    import base64
    return base64.b64encode(str(value).encode()).decode()

def from_base64(value):
    """Decode base64 string."""
    import base64
    return base64.b64decode(str(value).encode()).decode()

def to_json_pretty(value, indent=2):
    """Convert value to pretty-printed JSON."""
    return json.dumps(value, indent=indent, sort_keys=True)

def regex_replace(value, pattern, replacement):
    """Replace text using regex pattern."""
    import re
    return re.sub(pattern, replacement, str(value))

def hash_sha256(value):
    """Generate SHA256 hash of value."""
    import hashlib
    return hashlib.sha256(str(value).encode()).hexdigest()

def random_string(length=8):
    """Generate random string of specified length."""
    import random
    import string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def env_var(var_name, default_value=""):
    """Get environment variable with optional default."""
    return os.environ.get(var_name, default_value)

# Custom Jinja2 functions
def current_timestamp():
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()

def file_exists(filepath):
    """Check if file exists."""
    return os.path.exists(filepath)

class TemplateRenderer:
    """Advanced Jinja2 template renderer with custom filters and functions."""
    
    def __init__(self, template_dirs: List[str] = None, strict: bool = True):
        """Initialize template renderer.
        
        Args:
            template_dirs: List of directories to search for templates
            strict: If True, raise errors on undefined variables
        """
        self.template_dirs = template_dirs or ['.']
        self.strict = strict
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.template_dirs),
            autoescape=select_autoescape(['html', 'xml']),
            undefined=jinja2.StrictUndefined if strict else jinja2.Undefined,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self.env.filters.update({
            'to_base64': to_base64,
            'from_base64': from_base64,
            'to_json_pretty': to_json_pretty,
            'regex_replace': regex_replace,
            'hash_sha256': hash_sha256,
            'random_string': random_string,
            'env_var': env_var
        })
        
        # Register custom functions
        self.env.globals.update({
            'current_timestamp': current_timestamp,
            'file_exists': file_exists,
            'range': range,
            'len': len,
            'enumerate': enumerate,
            'zip': zip
        })
    
    def load_variables(self, var_files: List[str]) -> Dict[str, Any]:
        """Load variables from multiple YAML/JSON files.
        
        Args:
            var_files: List of variable file paths
            
        Returns:
            Merged dictionary of variables
        """
        variables = {}
        
        for var_file in var_files:
            if not os.path.exists(var_file):
                click.echo(f"Warning: Variable file {var_file} not found", err=True)
                continue
                
            with open(var_file, 'r') as f:
                try:
                    if var_file.endswith('.json'):
                        data = json.load(f)
                    else:
                        data = yaml.safe_load(f)
                    
                    if data:
                        variables.update(data)
                        
                except (yaml.YAMLError, json.JSONDecodeError) as e:
                    click.echo(f"Error loading {var_file}: {e}", err=True)
                    sys.exit(1)
        
        return variables
    
    def render_template(self, template_path: str, variables: Dict[str, Any]) -> str:
        """Render a single template with variables.
        
        Args:
            template_path: Path to template file
            variables: Variables to use in rendering
            
        Returns:
            Rendered template content
        """
        try:
            template = self.env.get_template(template_path)
            return template.render(**variables)
        except TemplateNotFound:
            click.echo(f"Error: Template {template_path} not found", err=True)
            sys.exit(1)
        except TemplateError as e:
            click.echo(f"Error rendering template {template_path}: {e}", err=True)
            sys.exit(1)
    
    def validate_output(self, content: str, schema_file: str) -> bool:
        """Validate rendered content against JSON schema.
        
        Args:
            content: Rendered content to validate
            schema_file: Path to JSON schema file
            
        Returns:
            True if valid, False otherwise
        """
        if not JSONSCHEMA_AVAILABLE:
            click.echo("Warning: jsonschema not available, skipping validation", err=True)
            return True
        
        if not os.path.exists(schema_file):
            click.echo(f"Warning: Schema file {schema_file} not found", err=True)
            return True
        
        try:
            # Try to parse content as JSON for validation
            data = json.loads(content)
            
            with open(schema_file, 'r') as f:
                schema = json.load(f)
            
            jsonschema.validate(data, schema)
            return True
            
        except json.JSONDecodeError:
            click.echo("Info: Content is not JSON, skipping schema validation")
            return True
        except jsonschema.ValidationError as e:
            click.echo(f"Validation error: {e.message}", err=True)
            return False
        except Exception as e:
            click.echo(f"Validation error: {e}", err=True)
            return False

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Jinja2 Template Rendering Tool for Data Platform Configuration Management."""
    pass

@cli.command()
@click.option('--template', '-t', required=True, help='Template file path')
@click.option('--variables', '-v', multiple=True, help='Variable file paths (can specify multiple)')
@click.option('--output', '-o', help='Output file path (stdout if not specified)')
@click.option('--template-dir', '-d', multiple=True, help='Template search directories')
@click.option('--validate', help='JSON schema file for validation')
@click.option('--strict/--no-strict', default=True, help='Strict mode for undefined variables')
@click.option('--dry-run', is_flag=True, help='Show rendered output without writing to file')
@click.option('--backup', is_flag=True, help='Create backup of existing output file')
def render(template, variables, output, template_dir, validate, strict, dry_run, backup):
    """Render a single template with variables."""
    
    # Setup template directories
    template_dirs = list(template_dir) if template_dir else ['.']
    
    # Add template file directory to search path
    template_path = Path(template)
    if template_path.is_absolute():
        template_dirs.insert(0, str(template_path.parent))
        template = template_path.name
    
    renderer = TemplateRenderer(template_dirs, strict)
    
    # Load variables
    var_files = list(variables) if variables else []
    variables_data = renderer.load_variables(var_files)
    
    # Render template
    click.echo(f"Rendering template: {template}")
    rendered_content = renderer.render_template(template, variables_data)
    
    # Validate if schema provided
    if validate:
        click.echo(f"Validating against schema: {validate}")
        if not renderer.validate_output(rendered_content, validate):
            click.echo("Validation failed", err=True)
            sys.exit(1)
        click.echo("Validation passed")
    
    # Output handling
    if dry_run:
        click.echo("=== DRY RUN - RENDERED CONTENT ===")
        click.echo(rendered_content)
        click.echo("=== END RENDERED CONTENT ===")
    elif output:
        output_path = Path(output)
        
        # Create backup if requested
        if backup and output_path.exists():
            backup_path = output_path.with_suffix(output_path.suffix + '.bak')
            output_path.rename(backup_path)
            click.echo(f"Created backup: {backup_path}")
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write rendered content
        with open(output_path, 'w') as f:
            f.write(rendered_content)
        
        click.echo(f"Template rendered to: {output}")
    else:
        click.echo(rendered_content)

@cli.command()
@click.option('--template-dir', '-t', required=True, help='Directory containing templates')
@click.option('--variables-dir', '-v', required=True, help='Directory containing variable files')
@click.option('--output-dir', '-o', required=True, help='Output directory')
@click.option('--pattern', '-p', default='*.j2', help='Template file pattern')
@click.option('--environment', '-e', help='Environment name (matches variable file)')
@click.option('--validate-dir', help='Directory containing validation schemas')
@click.option('--force/--no-force', default=False, help='Overwrite existing files')
def batch(template_dir, variables_dir, output_dir, pattern, environment, validate_dir, force):
    """Batch render multiple templates."""
    
    template_path = Path(template_dir)
    variables_path = Path(variables_dir)
    output_path = Path(output_dir)
    
    if not template_path.exists():
        click.echo(f"Error: Template directory {template_dir} not found", err=True)
        sys.exit(1)
    
    if not variables_path.exists():
        click.echo(f"Error: Variables directory {variables_dir} not found", err=True)
        sys.exit(1)
    
    # Find template files
    template_files = list(template_path.glob(pattern))
    if not template_files:
        click.echo(f"No template files found matching pattern: {pattern}")
        return
    
    # Setup renderer
    renderer = TemplateRenderer([str(template_path)])
    
    # Load variables
    var_files = []
    if environment:
        env_var_file = variables_path / f"{environment}.yml"
        if env_var_file.exists():
            var_files.append(str(env_var_file))
        else:
            click.echo(f"Warning: Environment file {env_var_file} not found")
    
    # Add common variable files
    for common_file in ['common.yml', 'global.yml']:
        common_path = variables_path / common_file
        if common_path.exists():
            var_files.append(str(common_path))
    
    if not var_files:
        click.echo("No variable files found")
        return
    
    variables_data = renderer.load_variables(var_files)
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Render each template
    for template_file in template_files:
        template_name = template_file.name
        output_name = template_name.replace('.j2', '')
        output_file = output_path / output_name
        
        if output_file.exists() and not force:
            click.echo(f"Skipping {output_file} (already exists, use --force to overwrite)")
            continue
        
        click.echo(f"Rendering {template_name} -> {output_name}")
        
        try:
            rendered_content = renderer.render_template(template_name, variables_data)
            
            # Validate if schema directory provided
            if validate_dir:
                schema_file = Path(validate_dir) / f"{output_name}.schema.json"
                if schema_file.exists():
                    if not renderer.validate_output(rendered_content, str(schema_file)):
                        click.echo(f"Validation failed for {output_name}", err=True)
                        continue
            
            # Write output
            with open(output_file, 'w') as f:
                f.write(rendered_content)
            
            click.echo(f"✓ {output_name}")
            
        except Exception as e:
            click.echo(f"✗ Error rendering {template_name}: {e}", err=True)

@cli.command()
@click.option('--config', '-c', required=True, help='Batch configuration file')
def batch_config(config):
    """Render templates using batch configuration file."""
    
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Error: Configuration file {config} not found", err=True)
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        batch_config = yaml.safe_load(f)
    
    for job in batch_config.get('jobs', []):
        click.echo(f"Processing job: {job.get('name', 'Unnamed')}")
        
        # Extract job parameters
        template_dir = job.get('template_dir', '.')
        template = job.get('template')
        variables = job.get('variables', [])
        output = job.get('output')
        validate_schema = job.get('validate')
        
        if not template:
            click.echo("Error: No template specified in job", err=True)
            continue
        
        # Setup renderer
        renderer = TemplateRenderer([template_dir])
        
        # Load variables
        variables_data = renderer.load_variables(variables)
        
        # Render template
        try:
            rendered_content = renderer.render_template(template, variables_data)
            
            # Validate if requested
            if validate_schema:
                if not renderer.validate_output(rendered_content, validate_schema):
                    click.echo(f"Validation failed for job: {job.get('name')}", err=True)
                    continue
            
            # Write output
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w') as f:
                    f.write(rendered_content)
                
                click.echo(f"✓ Rendered to {output}")
            else:
                click.echo(rendered_content)
                
        except Exception as e:
            click.echo(f"✗ Error processing job: {e}", err=True)

@cli.command()
@click.option('--file1', required=True, help='First configuration file')
@click.option('--file2', required=True, help='Second configuration file')
@click.option('--output', help='Output diff to file')
def diff(file1, file2, output):
    """Compare two configuration files."""
    
    try:
        import difflib
        
        with open(file1, 'r') as f:
            content1 = f.readlines()
        
        with open(file2, 'r') as f:
            content2 = f.readlines()
        
        diff_result = list(difflib.unified_diff(
            content1, content2,
            fromfile=file1, tofile=file2,
            lineterm=''
        ))
        
        if diff_result:
            diff_content = '\n'.join(diff_result)
            
            if output:
                with open(output, 'w') as f:
                    f.write(diff_content)
                click.echo(f"Diff written to {output}")
            else:
                click.echo(diff_content)
        else:
            click.echo("Files are identical")
            
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--template-dir', '-d', default='.', help='Template directory to list')
@click.option('--pattern', '-p', default='*.j2', help='Template file pattern')
@click.option('--show-vars', is_flag=True, help='Show template variables')
def list_templates(template_dir, pattern, show_vars):
    """List available templates."""
    
    template_path = Path(template_dir)
    
    if not template_path.exists():
        click.echo(f"Error: Directory {template_dir} not found", err=True)
        sys.exit(1)
    
    templates = list(template_path.glob(pattern))
    
    if not templates:
        click.echo(f"No templates found matching pattern: {pattern}")
        return
    
    click.echo(f"Templates in {template_dir}:")
    click.echo("=" * 50)
    
    for template in sorted(templates):
        click.echo(f"📄 {template.name}")
        
        if show_vars:
            # Simple variable extraction (basic implementation)
            try:
                with open(template, 'r') as f:
                    content = f.read()
                
                import re
                variables = set(re.findall(r'\{\{\s*([^}]+)\s*\}\}', content))
                
                if variables:
                    click.echo(f"   Variables: {', '.join(sorted(variables))}")
                
            except Exception:
                pass
        
        click.echo()

if __name__ == '__main__':
    cli()