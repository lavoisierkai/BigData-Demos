{{ config(
    materialized='view',
    docs={'node_color': '#85C1E9'}
) }}

-- Aggregate customer order history and calculate key metrics

with orders as (
    select * from {{ ref('stg_ecommerce__orders') }}
),

order_items as (
    select * from {{ ref('stg_ecommerce__order_items') }}
),

customers as (
    select * from {{ ref('stg_ecommerce__customers') }}
),

-- Calculate order-level aggregations
order_aggregations as (
    select 
        o.order_id,
        o.customer_id,
        o.order_date,
        o.order_status,
        o.order_status_category,
        o.order_value_tier,
        o.payment_method_category,
        o.total_amount_usd,
        o.is_completed_order,
        o.is_cancelled_order,
        o.is_high_value_order,
        o.order_day_type,
        o.order_time_of_day,
        o.order_season,
        o.holiday_period,
        
        -- Order item aggregations
        count(oi.order_item_id) as items_in_order,
        sum(oi.quantity) as total_items_quantity,
        sum(oi.gross_item_amount) as total_gross_amount,
        sum(oi.net_item_amount) as total_net_amount,
        sum(oi.discount_amount_clean) as total_discount_amount,
        avg(oi.unit_price) as avg_item_price,
        max(oi.unit_price) as max_item_price,
        min(oi.unit_price) as min_item_price,
        
        -- Discount analysis
        case 
            when sum(oi.gross_item_amount) > 0 
            then sum(oi.discount_amount_clean) / sum(oi.gross_item_amount)
            else 0
        end as order_discount_percentage,
        
        sum(case when oi.has_discount then 1 else 0 end) as discounted_items_count,
        
        -- Price tier distribution
        sum(case when oi.price_tier = 'Budget' then oi.quantity else 0 end) as budget_items,
        sum(case when oi.price_tier = 'Standard' then oi.quantity else 0 end) as standard_items,
        sum(case when oi.price_tier = 'Premium' then oi.quantity else 0 end) as premium_items,
        sum(case when oi.price_tier = 'Luxury' then oi.quantity else 0 end) as luxury_items
        
    from orders o
    left join order_items oi on o.order_id = oi.order_id
    group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
),

-- Calculate customer-level aggregations
customer_order_metrics as (
    select 
        customer_id,
        
        -- Order count metrics
        count(*) as total_orders,
        count(case when is_completed_order then 1 end) as completed_orders,
        count(case when is_cancelled_order then 1 end) as cancelled_orders,
        count(case when is_high_value_order then 1 end) as high_value_orders,
        
        -- Financial metrics
        sum(total_amount_usd) as total_lifetime_value,
        sum(case when is_completed_order then total_amount_usd else 0 end) as completed_lifetime_value,
        avg(total_amount_usd) as avg_order_value,
        max(total_amount_usd) as max_order_value,
        min(total_amount_usd) as min_order_value,
        
        -- Item quantity metrics
        sum(total_items_quantity) as total_items_purchased,
        avg(total_items_quantity) as avg_items_per_order,
        sum(items_in_order) as total_line_items,
        avg(items_in_order) as avg_line_items_per_order,
        
        -- Temporal patterns
        min(order_date) as first_order_date,
        max(order_date) as last_order_date,
        count(distinct date(order_date)) as unique_order_days,
        
        -- Behavioral patterns
        count(case when order_day_type = 'Weekend' then 1 end) as weekend_orders,
        count(case when order_day_type = 'Weekday' then 1 end) as weekday_orders,
        
        count(case when order_time_of_day = 'Morning' then 1 end) as morning_orders,
        count(case when order_time_of_day = 'Afternoon' then 1 end) as afternoon_orders,
        count(case when order_time_of_day = 'Evening' then 1 end) as evening_orders,
        count(case when order_time_of_day = 'Night' then 1 end) as night_orders,
        
        -- Seasonal patterns
        count(case when order_season = 'Spring' then 1 end) as spring_orders,
        count(case when order_season = 'Summer' then 1 end) as summer_orders,
        count(case when order_season = 'Fall' then 1 end) as fall_orders,
        count(case when order_season = 'Winter' then 1 end) as winter_orders,
        
        -- Payment preferences
        mode() within group (order by payment_method_category) as preferred_payment_method,
        count(distinct payment_method_category) as payment_methods_used,
        
        -- Value tier distribution
        count(case when order_value_tier = 'Low Value' then 1 end) as low_value_orders,
        count(case when order_value_tier = 'Medium Value' then 1 end) as medium_value_orders,
        count(case when order_value_tier = 'High Value' then 1 end) as high_value_orders_count,
        count(case when order_value_tier = 'Premium Value' then 1 end) as premium_value_orders,
        
        -- Discount behavior
        avg(order_discount_percentage) as avg_discount_percentage,
        sum(total_discount_amount) as total_discounts_received,
        count(case when order_discount_percentage > 0 then 1 end) as orders_with_discounts,
        
        -- Product tier preferences
        sum(budget_items) as total_budget_items,
        sum(standard_items) as total_standard_items,
        sum(premium_items) as total_premium_items,
        sum(luxury_items) as total_luxury_items
        
    from order_aggregations
    group by 1
),

-- Calculate derived metrics
customer_order_insights as (
    select 
        *,
        
        -- Customer lifecycle metrics
        date_diff(current_date(), date(first_order_date), day) as customer_tenure_days,
        date_diff(current_date(), date(last_order_date), day) as days_since_last_order,
        case 
            when last_order_date >= date_sub(current_date(), interval {{ var('churn_prediction_days') }} day) 
            then false 
            else true 
        end as is_at_risk_of_churn,
        
        -- Purchase frequency
        case 
            when date_diff(date(last_order_date), date(first_order_date), day) > 0
            then total_orders / (date_diff(date(last_order_date), date(first_order_date), day) / 30.0)
            else total_orders
        end as avg_orders_per_month,
        
        -- Customer value segments
        case 
            when completed_lifetime_value >= 2000 then 'High Value'
            when completed_lifetime_value >= 500 then 'Medium Value'
            when completed_lifetime_value >= 100 then 'Low Value'
            else 'Minimal Value'
        end as lifetime_value_segment,
        
        -- Order frequency segments
        case 
            when total_orders >= 20 then 'Frequent'
            when total_orders >= 5 then 'Regular'
            when total_orders >= 2 then 'Occasional'
            else 'One-time'
        end as purchase_frequency_segment,
        
        -- Behavioral insights
        case 
            when weekend_orders > weekday_orders then 'Weekend Shopper'
            else 'Weekday Shopper'
        end as shopping_day_preference,
        
        case 
            when morning_orders >= afternoon_orders 
                and morning_orders >= evening_orders 
                and morning_orders >= night_orders then 'Morning'
            when afternoon_orders >= evening_orders 
                and afternoon_orders >= night_orders then 'Afternoon'
            when evening_orders >= night_orders then 'Evening'
            else 'Night'
        end as shopping_time_preference,
        
        -- Product preferences
        case 
            when luxury_items > premium_items + standard_items + budget_items then 'Luxury Focused'
            when premium_items > standard_items + budget_items then 'Premium Focused'
            when standard_items > budget_items then 'Standard Focused'
            else 'Budget Focused'
        end as product_tier_preference,
        
        -- Discount sensitivity
        case 
            when avg_discount_percentage > 0.3 then 'High Discount Seeker'
            when avg_discount_percentage > 0.1 then 'Moderate Discount Seeker'
            when avg_discount_percentage > 0 then 'Low Discount Seeker'
            else 'Full Price Buyer'
        end as discount_sensitivity,
        
        -- Cancellation behavior
        case 
            when total_orders > 0 then cancelled_orders / total_orders 
            else 0 
        end as cancellation_rate,
        
        -- Order completion rate
        case 
            when total_orders > 0 then completed_orders / total_orders 
            else 0 
        end as completion_rate
        
    from customer_order_metrics
),

-- Final enrichment with customer data
final as (
    select 
        c.customer_id,
        c.email,
        c.full_name,
        c.customer_segment,
        c.customer_status,
        c.customer_created_at,
        c.is_active_customer,
        c.data_quality_score,
        
        -- Order metrics
        coi.*,
        
        -- RFM-style scoring (Recency, Frequency, Monetary)
        case 
            when coi.days_since_last_order <= 30 then 5
            when coi.days_since_last_order <= 60 then 4
            when coi.days_since_last_order <= 90 then 3
            when coi.days_since_last_order <= 180 then 2
            else 1
        end as recency_score,
        
        case 
            when coi.total_orders >= 20 then 5
            when coi.total_orders >= 10 then 4
            when coi.total_orders >= 5 then 3
            when coi.total_orders >= 2 then 2
            else 1
        end as frequency_score,
        
        case 
            when coi.completed_lifetime_value >= 2000 then 5
            when coi.completed_lifetime_value >= 1000 then 4
            when coi.completed_lifetime_value >= 500 then 3
            when coi.completed_lifetime_value >= 100 then 2
            else 1
        end as monetary_score,
        
        -- Data lineage
        current_timestamp() as dbt_processed_at
        
    from customer_order_insights coi
    inner join customers c on coi.customer_id = c.customer_id
)

select * from final