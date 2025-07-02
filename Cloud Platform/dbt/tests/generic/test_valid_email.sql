-- Custom test to validate email format

{% test valid_email(model, column_name) %}

    select {{ column_name }}
    from {{ model }}
    where {{ column_name }} is not null
      and not regexp_contains({{ column_name }}, r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

{% endtest %}