-- Custom test to check if values are within reasonable bounds

{% test reasonable_values(model, column_name, min_value=0, max_value=1000000) %}

    select {{ column_name }}
    from {{ model }}
    where {{ column_name }} is not null
      and ({{ column_name }} < {{ min_value }} or {{ column_name }} > {{ max_value }})

{% endtest %}