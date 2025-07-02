{{ config(
    materialized='table',
    docs={'node_color': '#82E0AA'},
    indexes=[
      {'columns': ['sale_key'], 'unique': True},
      {'columns': ['order_date_key']},
      {'columns': ['customer_key']},
      {'columns': ['product_key']},
      {'columns': ['order_id', 'order_item_id']},
    ],
    partition_by={
      'field': 'order_date',
      'data_type': 'date',
      'granularity': 'month'
    }
) }}

-- Sales fact table containing transactional data with dimensional references

with orders as (
    select * from {{ ref('stg_ecommerce__orders') }}
),

order_items as (
    select * from {{ ref('stg_ecommerce__order_items') }}
),

customers as (
    select * from {{ ref('dim_customers') }}
),

products as (
    select * from {{ ref('stg_ecommerce__products') }}
),

-- Create date dimension keys (simplified - in production you'd have a proper date dimension)
order_items_with_context as (
    select 
        oi.*,
        o.customer_id,
        o.order_date,
        o.order_status,
        o.order_status_category,
        o.order_value_tier,
        o.payment_method_category,
        o.total_amount_usd as order_total_amount,
        o.is_completed_order,
        o.is_cancelled_order,
        o.is_high_value_order,
        o.order_day_type,
        o.order_time_of_day,
        o.order_season,
        o.holiday_period,
        o.order_year,
        o.order_month,
        o.order_day,
        o.order_hour
        
    from order_items oi
    inner join orders o on oi.order_id = o.order_id
),

-- Build the fact table
fact_sales as (
    select
        -- Surrogate key for the fact
        {{ dbt_utils.generate_surrogate_key(['oic.order_id', 'oic.order_item_id']) }} as sale_key,
        
        -- Natural keys
        oic.order_id,
        oic.order_item_id,
        
        -- Dimensional foreign keys
        c.customer_key,
        {{ dbt_utils.generate_surrogate_key(['oic.product_id']) }} as product_key,
        
        -- Date keys (simplified format YYYYMMDD)
        cast(format_date('%Y%m%d', date(oic.order_date)) as int64) as order_date_key,
        cast(format_date('%Y%m', date(oic.order_date)) as int64) as order_month_key,
        cast(format_date('%Y', date(oic.order_date)) as int64) as order_year_key,
        
        -- Date and time attributes
        date(oic.order_date) as order_date,
        datetime(oic.order_date) as order_datetime,
        oic.order_year,
        oic.order_month,
        oic.order_day,
        oic.order_hour,
        oic.order_day_type,
        oic.order_time_of_day,
        oic.order_season,
        oic.holiday_period,
        
        -- Product attributes (denormalized for performance)
        oic.product_id,
        p.product_name,
        p.sku,
        p.brand,
        p.brand_category,
        p.category_id,
        p.price_category as product_price_category,
        p.product_positioning,
        
        -- Customer attributes (denormalized for performance)
        oic.customer_id,
        c.customer_segment,
        c.lifetime_value_segment,
        c.rfm_segment,
        c.customer_lifecycle_stage,
        
        -- Order attributes
        oic.order_status,
        oic.order_status_category,
        oic.order_value_tier,
        oic.payment_method_category,
        oic.is_completed_order,
        oic.is_cancelled_order,
        oic.is_high_value_order,
        
        -- Item-level details
        oic.quantity,
        oic.unit_price,
        oic.discount_amount_clean as discount_amount,
        oic.discount_percentage,
        oic.has_discount,
        oic.price_tier as item_price_tier,
        oic.quantity_category,
        oic.revenue_impact,
        
        -- Financial measures
        oic.gross_item_amount,
        oic.net_item_amount,
        oic.estimated_margin,
        
        -- Calculated measures
        oic.net_price_per_unit,
        case 
            when oic.is_completed_order then oic.net_item_amount 
            else 0 
        end as completed_revenue,
        
        case 
            when oic.is_completed_order then oic.quantity 
            else 0 
        end as completed_quantity,
        
        case 
            when oic.is_cancelled_order then oic.net_item_amount 
            else 0 
        end as cancelled_revenue,
        
        case 
            when oic.is_cancelled_order then oic.quantity 
            else 0 
        end as cancelled_quantity,
        
        -- Profitability measures
        case 
            when oic.is_completed_order then oic.estimated_margin 
            else 0 
        end as completed_margin,
        
        case 
            when oic.estimated_margin is not null and oic.net_item_amount > 0
            then oic.estimated_margin / oic.net_item_amount
            else null
        end as margin_percentage_calculated,
        
        -- Order-level measures (for aggregation context)
        oic.order_total_amount,
        case 
            when oic.order_total_amount > 0 
            then oic.net_item_amount / oic.order_total_amount 
            else 0 
        end as item_share_of_order,
        
        -- Flags for analysis
        case when oic.quantity > 1 then 1 else 0 end as is_multi_quantity,
        case when oic.discount_percentage > 0 then 1 else 0 end as is_discounted,
        case when oic.discount_percentage > 0.3 then 1 else 0 end as is_heavily_discounted,
        case when oic.unit_price >= 100 then 1 else 0 end as is_high_value_item,
        case when p.brand_category = 'Premium Brand' then 1 else 0 end as is_premium_brand,
        
        -- Cohort analysis fields
        case 
            when c.first_order_date = date(oic.order_date) then 1 
            else 0 
        end as is_first_purchase,
        
        case 
            when c.total_orders = 1 then 1 
            else 0 
        end as is_one_time_customer,
        
        -- Seasonal and temporal flags
        case when oic.order_season = 'Winter' then 1 else 0 end as is_winter_sale,
        case when oic.order_season = 'Spring' then 1 else 0 end as is_spring_sale,
        case when oic.order_season = 'Summer' then 1 else 0 end as is_summer_sale,
        case when oic.order_season = 'Fall' then 1 else 0 end as is_fall_sale,
        case when oic.holiday_period != 'Regular' then 1 else 0 end as is_holiday_sale,
        case when oic.order_day_type = 'Weekend' then 1 else 0 end as is_weekend_sale,
        
        -- Data quality and lineage
        oic.is_valid_line_item,
        current_timestamp() as dbt_processed_at,
        '{{ run_started_at }}' as dbt_run_started_at
        
    from order_items_with_context oic
    left join customers c on oic.customer_id = c.customer_id
    left join products p on oic.product_id = p.product_id
    where oic.is_valid_line_item = true  -- Only include valid transactions
),

-- Add some additional calculated fields
fact_sales_enriched as (
    select 
        *,
        
        -- Revenue per unit calculations
        case 
            when quantity > 0 then net_item_amount / quantity 
            else 0 
        end as revenue_per_unit,
        
        -- Discount impact
        case 
            when gross_item_amount > 0 
            then discount_amount / gross_item_amount 
            else 0 
        end as discount_impact_ratio,
        
        -- Customer order sequence (approximate)
        row_number() over (
            partition by customer_id 
            order by order_date, order_id, order_item_id
        ) as customer_order_sequence,
        
        -- Product sales rank for the period
        dense_rank() over (
            order by sum(net_item_amount) over (partition by product_id) desc
        ) as product_revenue_rank,
        
        -- Running totals for customer
        sum(net_item_amount) over (
            partition by customer_id 
            order by order_date, order_id, order_item_id 
            rows unbounded preceding
        ) as customer_running_total,
        
        -- Month-to-date and year-to-date aggregations
        sum(net_item_amount) over (
            partition by customer_id, order_year, order_month
            order by order_date, order_id, order_item_id 
            rows unbounded preceding
        ) as customer_mtd_total,
        
        sum(net_item_amount) over (
            partition by customer_id, order_year
            order by order_date, order_id, order_item_id 
            rows unbounded preceding
        ) as customer_ytd_total
        
    from fact_sales
)

select * from fact_sales_enriched