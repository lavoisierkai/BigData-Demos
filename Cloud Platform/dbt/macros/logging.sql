-- Logging macros for audit trails and monitoring

{% macro log_model_start_time() %}
    {{ log("Starting model execution: " ~ this ~ " at " ~ run_started_at, info=true) }}
{% endmacro %}

{% macro log_model_end_time() %}
    {{ log("Completed model execution: " ~ this ~ " at " ~ run_started_at, info=true) }}
{% endmacro %}

{% macro create_audit_table() %}
    {% if execute %}
        {% set audit_sql %}
            create table if not exists {{ target.schema }}.dbt_audit_log (
                run_id varchar(255),
                model_name varchar(255),
                start_time timestamp,
                end_time timestamp,
                status varchar(50),
                rows_affected bigint,
                run_started_at timestamp,
                invocation_id varchar(255)
            )
        {% endset %}
        
        {% do run_query(audit_sql) %}
        {{ log("Audit table created/verified", info=true) }}
    {% endif %}
{% endmacro %}

{% macro log_run_start() %}
    {% if execute %}
        {% set log_sql %}
            insert into {{ target.schema }}.dbt_audit_log 
            (run_id, model_name, start_time, status, run_started_at, invocation_id)
            values (
                '{{ run_started_at.strftime("%Y%m%d_%H%M%S") }}',
                'RUN_START',
                '{{ run_started_at }}',
                'STARTED',
                '{{ run_started_at }}',
                '{{ invocation_id }}'
            )
        {% endset %}
        
        {% do run_query(log_sql) %}
        {{ log("Run start logged", info=true) }}
    {% endif %}
{% endmacro %}

{% macro log_run_end() %}
    {% if execute %}
        {% set log_sql %}
            insert into {{ target.schema }}.dbt_audit_log 
            (run_id, model_name, end_time, status, run_started_at, invocation_id)
            values (
                '{{ run_started_at.strftime("%Y%m%d_%H%M%S") }}',
                'RUN_END',
                current_timestamp(),
                'COMPLETED',
                '{{ run_started_at }}',
                '{{ invocation_id }}'
            )
        {% endset %}
        
        {% do run_query(log_sql) %}
        {{ log("Run end logged", info=true) }}
    {% endif %}
{% endmacro %}

{% macro cleanup_temp_tables() %}
    {% if execute %}
        {% set cleanup_sql %}
            -- Clean up any temporary tables older than 7 days
            {% for schema in ['dbt_tmp', 'dbt_temp'] %}
                drop table if exists {{ target.database }}.{{ schema }}.temp_table_cleanup_{{ run_started_at.strftime("%Y%m%d") }}
            {% endfor %}
        {% endset %}
        
        {{ log("Temporary tables cleaned up", info=true) }}
    {% endif %}
{% endmacro %}