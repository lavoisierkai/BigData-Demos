{{ config(
    materialized='table',
    docs={'node_color': '#82E0AA'},
    indexes=[
      {'columns': ['customer_key'], 'unique': True},
      {'columns': ['customer_id'], 'unique': True},
      {'columns': ['email']},
      {'columns': ['customer_segment']},
      {'columns': ['lifetime_value_segment']},
      {'columns': ['rfm_segment']}
    ]
) }}

-- Customer dimension table with comprehensive customer attributes and calculated metrics

with customer_orders as (
    select * from {{ ref('int_customer_orders') }}
),

customers_base as (
    select * from {{ ref('stg_ecommerce__customers') }}
),

-- Create customer dimension with SCD Type 1 (slowly changing dimension)
customers_enriched as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['co.customer_id']) }} as customer_key,
        
        -- Natural key
        co.customer_id,
        
        -- Customer identifiers
        co.email,
        co.full_name,
        cb.first_name,
        cb.last_name,
        cb.phone,
        
        -- Customer classification
        co.customer_segment as original_segment,
        co.customer_status,
        co.is_active_customer,
        
        -- Customer quality metrics
        co.data_quality_score,
        cb.is_valid_email,
        cb.has_complete_name,
        cb.is_valid_phone,
        
        -- Registration information
        co.customer_created_at,
        cb.customer_tenure_days,
        
        -- Order behavior metrics
        coalesce(co.total_orders, 0) as total_orders,
        coalesce(co.completed_orders, 0) as completed_orders,
        coalesce(co.cancelled_orders, 0) as cancelled_orders,
        coalesce(co.high_value_orders, 0) as high_value_orders,
        
        -- Financial metrics
        coalesce(co.total_lifetime_value, 0) as total_lifetime_value,
        coalesce(co.completed_lifetime_value, 0) as completed_lifetime_value,
        coalesce(co.avg_order_value, 0) as avg_order_value,
        coalesce(co.max_order_value, 0) as max_order_value,
        coalesce(co.min_order_value, 0) as min_order_value,
        
        -- Purchase patterns
        coalesce(co.total_items_purchased, 0) as total_items_purchased,
        coalesce(co.avg_items_per_order, 0) as avg_items_per_order,
        coalesce(co.total_line_items, 0) as total_line_items,
        coalesce(co.avg_line_items_per_order, 0) as avg_line_items_per_order,
        
        -- Temporal patterns
        co.first_order_date,
        co.last_order_date,
        coalesce(co.unique_order_days, 0) as unique_order_days,
        coalesce(co.customer_tenure_days, 0) as customer_tenure_days,
        coalesce(co.days_since_last_order, 999) as days_since_last_order,
        coalesce(co.avg_orders_per_month, 0) as avg_orders_per_month,
        
        -- Behavioral segments
        coalesce(co.lifetime_value_segment, 'Minimal Value') as lifetime_value_segment,
        coalesce(co.purchase_frequency_segment, 'One-time') as purchase_frequency_segment,
        coalesce(co.shopping_day_preference, 'Unknown') as shopping_day_preference,
        coalesce(co.shopping_time_preference, 'Unknown') as shopping_time_preference,
        coalesce(co.product_tier_preference, 'Unknown') as product_tier_preference,
        coalesce(co.discount_sensitivity, 'Unknown') as discount_sensitivity,
        
        -- Churn indicators
        coalesce(co.is_at_risk_of_churn, false) as is_at_risk_of_churn,
        coalesce(co.cancellation_rate, 0) as cancellation_rate,
        coalesce(co.completion_rate, 0) as completion_rate,
        
        -- RFM Scores
        coalesce(co.recency_score, 1) as recency_score,
        coalesce(co.frequency_score, 1) as frequency_score,
        coalesce(co.monetary_score, 1) as monetary_score,
        
        -- Shopping preferences
        coalesce(co.preferred_payment_method, 'Unknown') as preferred_payment_method,
        coalesce(co.payment_methods_used, 0) as payment_methods_used,
        
        -- Order timing patterns
        coalesce(co.weekend_orders, 0) as weekend_orders,
        coalesce(co.weekday_orders, 0) as weekday_orders,
        coalesce(co.morning_orders, 0) as morning_orders,
        coalesce(co.afternoon_orders, 0) as afternoon_orders,
        coalesce(co.evening_orders, 0) as evening_orders,
        coalesce(co.night_orders, 0) as night_orders,
        
        -- Seasonal patterns
        coalesce(co.spring_orders, 0) as spring_orders,
        coalesce(co.summer_orders, 0) as summer_orders,
        coalesce(co.fall_orders, 0) as fall_orders,
        coalesce(co.winter_orders, 0) as winter_orders,
        
        -- Value distribution
        coalesce(co.low_value_orders, 0) as low_value_orders,
        coalesce(co.medium_value_orders, 0) as medium_value_orders,
        coalesce(co.high_value_orders_count, 0) as high_value_orders_count,
        coalesce(co.premium_value_orders, 0) as premium_value_orders,
        
        -- Discount behavior
        coalesce(co.avg_discount_percentage, 0) as avg_discount_percentage,
        coalesce(co.total_discounts_received, 0) as total_discounts_received,
        coalesce(co.orders_with_discounts, 0) as orders_with_discounts,
        
        -- Product preferences
        coalesce(co.total_budget_items, 0) as total_budget_items,
        coalesce(co.total_standard_items, 0) as total_standard_items,
        coalesce(co.total_premium_items, 0) as total_premium_items,
        coalesce(co.total_luxury_items, 0) as total_luxury_items,
        
        -- Data lineage
        current_timestamp() as dbt_processed_at,
        current_timestamp() as dim_created_at,
        current_timestamp() as dim_updated_at
        
    from customer_orders co
    full outer join customers_base cb on co.customer_id = cb.customer_id
),

-- Calculate additional derived metrics and segments
customers_with_segments as (
    select 
        *,
        
        -- RFM composite score
        (recency_score * 100) + (frequency_score * 10) + monetary_score as rfm_score,
        
        -- RFM segment classification
        case 
            when recency_score >= 4 and frequency_score >= 4 and monetary_score >= 4 then 'Champions'
            when recency_score >= 2 and frequency_score >= 3 and monetary_score >= 3 then 'Loyal Customers'
            when recency_score >= 3 and frequency_score >= 1 and monetary_score >= 3 then 'Potential Loyalists'
            when recency_score >= 4 and frequency_score >= 1 and monetary_score >= 1 then 'New Customers'
            when recency_score >= 3 and frequency_score >= 2 and monetary_score >= 2 then 'Promising'
            when recency_score >= 2 and frequency_score >= 2 and monetary_score >= 2 then 'Need Attention'
            when recency_score >= 2 and frequency_score >= 1 and monetary_score >= 1 then 'About to Sleep'
            when recency_score <= 2 and frequency_score >= 2 and monetary_score >= 2 then 'At Risk'
            when recency_score <= 1 and frequency_score >= 4 and monetary_score >= 4 then 'Cannot Lose Them'
            when recency_score <= 1 and frequency_score >= 1 and monetary_score >= 1 then 'Hibernating'
            else 'Lost'
        end as rfm_segment,
        
        -- Customer lifecycle stage
        case 
            when total_orders = 0 then 'Prospect'
            when total_orders = 1 and days_since_last_order <= 30 then 'New Customer'
            when total_orders = 1 and days_since_last_order > 30 then 'One-time Customer'
            when total_orders >= 2 and days_since_last_order <= 90 then 'Active Customer'
            when total_orders >= 2 and days_since_last_order <= 180 then 'At Risk'
            when total_orders >= 2 and days_since_last_order > 180 then 'Inactive'
            else 'Unknown'
        end as customer_lifecycle_stage,
        
        -- Customer value tier (based on completed LTV and frequency)
        case 
            when completed_lifetime_value >= 2000 and total_orders >= 10 then 'VIP'
            when completed_lifetime_value >= 1000 and total_orders >= 5 then 'High Value'
            when completed_lifetime_value >= 500 and total_orders >= 3 then 'Medium Value'
            when completed_lifetime_value >= 100 and total_orders >= 2 then 'Standard Value'
            when completed_lifetime_value > 0 then 'Low Value'
            else 'No Value'
        end as customer_value_tier,
        
        -- Engagement level
        case 
            when avg_orders_per_month >= 2 then 'Highly Engaged'
            when avg_orders_per_month >= 1 then 'Engaged'
            when avg_orders_per_month >= 0.5 then 'Moderately Engaged'
            when avg_orders_per_month > 0 then 'Low Engagement'
            else 'No Engagement'
        end as engagement_level,
        
        -- Risk flags
        case 
            when cancellation_rate > 0.3 then true
            else false
        end as high_cancellation_risk,
        
        case 
            when completion_rate < 0.7 then true
            else false
        end as low_completion_risk,
        
        case 
            when data_quality_score < 0.5 then true
            else false
        end as data_quality_risk,
        
        -- Seasonality indicator
        case 
            when spring_orders = greatest(spring_orders, summer_orders, fall_orders, winter_orders) then 'Spring Shopper'
            when summer_orders = greatest(summer_orders, fall_orders, winter_orders) then 'Summer Shopper'
            when fall_orders = greatest(fall_orders, winter_orders) then 'Fall Shopper'
            when winter_orders > 0 then 'Winter Shopper'
            else 'No Seasonal Pattern'
        end as seasonal_preference,
        
        -- Discount behavior flag
        case 
            when avg_discount_percentage > 0.2 then true
            else false
        end as is_discount_sensitive
        
    from customers_enriched
)

select * from customers_with_segments