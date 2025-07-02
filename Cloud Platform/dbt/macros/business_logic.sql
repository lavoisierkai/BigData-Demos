-- Business logic macros for common calculations and transformations

{% macro calculate_customer_lifetime_value(customer_id_col, order_amount_col, order_date_col) %}
    sum(case when {{ order_date_col }} >= current_date - interval 365 day 
             then {{ order_amount_col }} else 0 end) as ltv_12_months,
    sum(case when {{ order_date_col }} >= current_date - interval 90 day 
             then {{ order_amount_col }} else 0 end) as ltv_3_months,
    sum({{ order_amount_col }}) as ltv_total
{% endmacro %}

{% macro rfm_score(recency_col, frequency_col, monetary_col) %}
    case 
        when {{ recency_col }} <= 30 then 5
        when {{ recency_col }} <= 60 then 4
        when {{ recency_col }} <= 90 then 3
        when {{ recency_col }} <= 180 then 2
        else 1
    end as recency_score,
    
    case 
        when {{ frequency_col }} >= 20 then 5
        when {{ frequency_col }} >= 10 then 4
        when {{ frequency_col }} >= 5 then 3
        when {{ frequency_col }} >= 2 then 2
        else 1
    end as frequency_score,
    
    case 
        when {{ monetary_col }} >= 2000 then 5
        when {{ monetary_col }} >= 1000 then 4
        when {{ monetary_col }} >= 500 then 3
        when {{ monetary_col }} >= 100 then 2
        else 1
    end as monetary_score
{% endmacro %}

{% macro customer_segmentation(rfm_score_col) %}
    case 
        when {{ rfm_score_col }} >= 444 then 'Champions'
        when {{ rfm_score_col }} >= 334 then 'Loyal Customers'
        when {{ rfm_score_col }} >= 313 then 'Potential Loyalists'
        when {{ rfm_score_col }} >= 411 then 'New Customers'
        when {{ rfm_score_col }} >= 322 then 'Promising'
        when {{ rfm_score_col }} >= 222 then 'Need Attention'
        when {{ rfm_score_col }} >= 211 then 'About to Sleep'
        when {{ rfm_score_col }} >= 122 then 'At Risk'
        when {{ rfm_score_col }} >= 144 then 'Cannot Lose Them'
        when {{ rfm_score_col }} >= 111 then 'Hibernating'
        else 'Lost'
    end
{% endmacro %}

{% macro seasonality_adjustment(value_col, month_col) %}
    case 
        when {{ month_col }} in (11, 12, 1) then {{ value_col }} * 1.2  -- Holiday boost
        when {{ month_col }} in (6, 7, 8) then {{ value_col }} * 0.9    -- Summer dip
        else {{ value_col }}
    end
{% endmacro %}

{% macro churn_probability(days_since_last_order, avg_order_frequency) %}
    case 
        when {{ days_since_last_order }} > ({{ avg_order_frequency }} * 3) then 'High Risk'
        when {{ days_since_last_order }} > ({{ avg_order_frequency }} * 2) then 'Medium Risk'
        when {{ days_since_last_order }} > {{ avg_order_frequency }} then 'Low Risk'
        else 'Active'
    end
{% endmacro %}

{% macro product_performance_category(revenue_col, units_col) %}
    case 
        when {{ revenue_col }} >= 10000 and {{ units_col }} >= 100 then 'Star'
        when {{ revenue_col }} >= 5000 and {{ units_col }} >= 50 then 'High Performer'
        when {{ revenue_col }} >= 1000 and {{ units_col }} >= 20 then 'Good Performer'
        when {{ revenue_col }} >= 100 and {{ units_col }} >= 5 then 'Average Performer'
        else 'Low Performer'
    end
{% endmacro %}

{% macro margin_category(margin_percentage) %}
    case 
        when {{ margin_percentage }} >= 0.5 then 'High Margin'
        when {{ margin_percentage }} >= 0.3 then 'Medium Margin'
        when {{ margin_percentage }} >= 0.1 then 'Low Margin'
        when {{ margin_percentage }} >= 0 then 'Break Even'
        else 'Loss'
    end
{% endmacro %}

{% macro cohort_analysis(customer_id_col, order_date_col, first_order_date_col) %}
    date_trunc('month', {{ first_order_date_col }}) as cohort_month,
    date_diff(
        date_trunc('month', {{ order_date_col }}),
        date_trunc('month', {{ first_order_date_col }}),
        month
    ) as period_number
{% endmacro %}

{% macro generate_fiscal_year(date_col, fiscal_year_start_month=4) %}
    case 
        when extract(month from {{ date_col }}) >= {{ fiscal_year_start_month }}
        then extract(year from {{ date_col }})
        else extract(year from {{ date_col }}) - 1
    end
{% endmacro %}

{% macro generate_fiscal_quarter(date_col, fiscal_year_start_month=4) %}
    case 
        when extract(month from {{ date_col }}) >= {{ fiscal_year_start_month }} 
        then 
            case 
                when extract(month from {{ date_col }}) < {{ fiscal_year_start_month + 3 }} then 'Q1'
                when extract(month from {{ date_col }}) < {{ fiscal_year_start_month + 6 }} then 'Q2'
                when extract(month from {{ date_col }}) < {{ fiscal_year_start_month + 9 }} then 'Q3'
                else 'Q4'
            end
        else 
            case 
                when extract(month from {{ date_col }}) < {{ fiscal_year_start_month - 9 }} then 'Q2'
                when extract(month from {{ date_col }}) < {{ fiscal_year_start_month - 6 }} then 'Q3'
                when extract(month from {{ date_col }}) < {{ fiscal_year_start_month - 3 }} then 'Q4'
                else 'Q1'
            end
    end
{% endmacro %}

{% macro days_between(start_date, end_date) %}
    date_diff({{ end_date }}, {{ start_date }}, day)
{% endmacro %}

{% macro safe_divide(numerator, denominator) %}
    case 
        when {{ denominator }} = 0 or {{ denominator }} is null then null
        else {{ numerator }} / {{ denominator }}
    end
{% endmacro %}