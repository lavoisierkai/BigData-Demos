{{ config(
    materialized='view',
    docs={'node_color': '#F8C471'}
) }}

with source as (
    select * from {{ source('ecommerce_raw', 'orders') }}
),

renamed as (
    select
        -- Primary key
        order_id,
        
        -- Foreign keys
        customer_id,
        shipping_address_id,
        billing_address_id,
        
        -- Order details
        order_date,
        order_status,
        total_amount,
        currency_code,
        payment_method,
        
        -- Timestamp fields
        created_at as order_created_at,
        updated_at as order_updated_at,
        
        -- Derived fields
        date(order_date) as order_date_day,
        extract(year from order_date) as order_year,
        extract(month from order_date) as order_month,
        extract(day from order_date) as order_day,
        extract(dayofweek from order_date) as order_day_of_week,
        extract(hour from order_date) as order_hour,
        
        -- Order timing analysis
        case 
            when extract(dayofweek from order_date) in (1, 7) then 'Weekend'
            else 'Weekday'
        end as order_day_type,
        
        case 
            when extract(hour from order_date) between 6 and 11 then 'Morning'
            when extract(hour from order_date) between 12 and 17 then 'Afternoon'
            when extract(hour from order_date) between 18 and 21 then 'Evening'
            else 'Night'
        end as order_time_of_day,
        
        -- Status categorization
        case 
            when order_status in ('pending', 'confirmed') then 'Processing'
            when order_status in ('shipped', 'delivered') then 'Fulfilled'
            when order_status in ('cancelled', 'returned') then 'Cancelled'
            else 'Other'
        end as order_status_category,
        
        -- Order value classification
        case 
            when total_amount < 50 then 'Low Value'
            when total_amount < 200 then 'Medium Value'
            when total_amount < 500 then 'High Value'
            else 'Premium Value'
        end as order_value_tier,
        
        -- Payment method categorization
        case 
            when lower(payment_method) like '%credit%' or lower(payment_method) like '%card%' then 'Credit Card'
            when lower(payment_method) like '%debit%' then 'Debit Card'
            when lower(payment_method) like '%paypal%' then 'PayPal'
            when lower(payment_method) like '%apple%pay%' then 'Apple Pay'
            when lower(payment_method) like '%google%pay%' then 'Google Pay'
            when lower(payment_method) like '%bank%' or lower(payment_method) like '%transfer%' then 'Bank Transfer'
            else 'Other'
        end as payment_method_category,
        
        -- Flags
        case 
            when order_status in ('delivered') then true
            else false
        end as is_completed_order,
        
        case 
            when order_status in ('cancelled', 'returned') then true
            else false
        end as is_cancelled_order,
        
        case 
            when total_amount >= {{ var('high_value_customer_threshold') }} then true
            else false
        end as is_high_value_order,
        
        -- Currency standardization (convert to USD if needed)
        case 
            when currency_code = 'USD' then total_amount
            when currency_code = 'EUR' then total_amount * 1.1  -- Simplified conversion
            when currency_code = 'GBP' then total_amount * 1.3
            when currency_code = 'CAD' then total_amount * 0.8
            else total_amount
        end as total_amount_usd,
        
        -- Data lineage
        current_timestamp() as dbt_processed_at,
        '{{ var("dbt_run_started_at") }}' as dbt_run_started_at

    from source
),

with_order_metrics as (
    select 
        *,
        
        -- Order processing time (if we have fulfillment data)
        case 
            when order_status = 'delivered' and order_created_at is not null 
            then date_diff(current_timestamp(), order_created_at, day)
            else null
        end as days_to_delivery,
        
        -- Seasonal analysis
        case 
            when order_month in (12, 1, 2) then 'Winter'
            when order_month in (3, 4, 5) then 'Spring'
            when order_month in (6, 7, 8) then 'Summer'
            when order_month in (9, 10, 11) then 'Fall'
        end as order_season,
        
        -- Holiday periods (simplified US holidays)
        case 
            when order_month = 11 and order_day >= 23 then 'Thanksgiving Week'
            when order_month = 12 and order_day >= 20 then 'Christmas Season'
            when order_month = 12 and order_day <= 5 then 'Christmas Season'
            when order_month = 1 and order_day <= 2 then 'New Year'
            when order_month = 7 and order_day = 4 then 'Independence Day'
            when order_month = 2 and order_day = 14 then 'Valentines Day'
            else 'Regular'
        end as holiday_period
        
    from renamed
)

select * from with_order_metrics