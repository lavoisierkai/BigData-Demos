{{ config(
    materialized='view',
    docs={'node_color': '#85C1E9'}
) }}

-- Calculate product performance metrics across orders and time periods

with order_items as (
    select * from {{ ref('stg_ecommerce__order_items') }}
),

orders as (
    select * from {{ ref('stg_ecommerce__orders') }}
),

products as (
    select * from {{ ref('stg_ecommerce__products') }}
),

-- Join order items with order context
order_items_enriched as (
    select 
        oi.*,
        o.customer_id,
        o.order_date,
        o.order_status,
        o.order_status_category,
        o.is_completed_order,
        o.is_cancelled_order,
        o.order_season,
        o.order_day_type,
        o.order_time_of_day,
        o.holiday_period,
        o.payment_method_category
        
    from order_items oi
    inner join orders o on oi.order_id = o.order_id
),

-- Calculate product performance metrics
product_metrics as (
    select 
        product_id,
        
        -- Sales volume metrics
        count(distinct order_id) as total_orders_containing_product,
        count(order_item_id) as total_line_items,
        sum(quantity) as total_units_sold,
        count(distinct customer_id) as unique_customers,
        
        -- Revenue metrics
        sum(gross_item_amount) as total_gross_revenue,
        sum(net_item_amount) as total_net_revenue,
        sum(discount_amount_clean) as total_discounts_given,
        avg(unit_price) as avg_selling_price,
        avg(net_item_amount / quantity) as avg_net_price_per_unit,
        
        -- Performance ratios
        avg(discount_percentage) as avg_discount_percentage,
        sum(case when has_discount then 1 else 0 end) / count(*) as discount_frequency,
        
        -- Order completion analysis
        sum(case when is_completed_order then quantity else 0 end) as completed_units_sold,
        sum(case when is_completed_order then net_item_amount else 0 end) as completed_revenue,
        sum(case when is_cancelled_order then quantity else 0 end) as cancelled_units,
        sum(case when is_cancelled_order then net_item_amount else 0 end) as cancelled_revenue,
        
        -- Temporal patterns
        min(order_date) as first_sale_date,
        max(order_date) as last_sale_date,
        count(distinct date(order_date)) as active_sales_days,
        
        -- Seasonal performance
        sum(case when order_season = 'Spring' then quantity else 0 end) as spring_units,
        sum(case when order_season = 'Summer' then quantity else 0 end) as summer_units,
        sum(case when order_season = 'Fall' then quantity else 0 end) as fall_units,
        sum(case when order_season = 'Winter' then quantity else 0 end) as winter_units,
        
        sum(case when order_season = 'Spring' then net_item_amount else 0 end) as spring_revenue,
        sum(case when order_season = 'Summer' then net_item_amount else 0 end) as summer_revenue,
        sum(case when order_season = 'Fall' then net_item_amount else 0 end) as fall_revenue,
        sum(case when order_season = 'Winter' then net_item_amount else 0 end) as winter_revenue,
        
        -- Day type performance
        sum(case when order_day_type = 'Weekend' then quantity else 0 end) as weekend_units,
        sum(case when order_day_type = 'Weekday' then quantity else 0 end) as weekday_units,
        
        -- Time of day performance
        sum(case when order_time_of_day = 'Morning' then quantity else 0 end) as morning_units,
        sum(case when order_time_of_day = 'Afternoon' then quantity else 0 end) as afternoon_units,
        sum(case when order_time_of_day = 'Evening' then quantity else 0 end) as evening_units,
        sum(case when order_time_of_day = 'Night' then quantity else 0 end) as night_units,
        
        -- Holiday performance
        sum(case when holiday_period != 'Regular' then quantity else 0 end) as holiday_units,
        sum(case when holiday_period != 'Regular' then net_item_amount else 0 end) as holiday_revenue,
        
        -- Purchase behavior
        avg(quantity) as avg_quantity_per_line_item,
        max(quantity) as max_quantity_per_line_item,
        
        -- Revenue impact analysis
        sum(case when revenue_impact = 'High Impact' then 1 else 0 end) as high_impact_sales,
        sum(case when revenue_impact = 'Medium Impact' then 1 else 0 end) as medium_impact_sales,
        sum(case when revenue_impact = 'Low Impact' then 1 else 0 end) as low_impact_sales
        
    from order_items_enriched
    group by 1
),

-- Calculate derived performance indicators
product_performance as (
    select 
        *,
        
        -- Sales velocity (units per day since first sale)
        case 
            when date_diff(current_date(), date(first_sale_date), day) > 0
            then total_units_sold / date_diff(current_date(), date(first_sale_date), day)
            else total_units_sold
        end as avg_units_per_day,
        
        -- Revenue velocity
        case 
            when date_diff(current_date(), date(first_sale_date), day) > 0
            then total_net_revenue / date_diff(current_date(), date(first_sale_date), day)
            else total_net_revenue
        end as avg_revenue_per_day,
        
        -- Customer penetration
        case 
            when total_orders_containing_product > 0
            then unique_customers / total_orders_containing_product
            else 0
        end as avg_customers_per_order,
        
        -- Completion rates
        case 
            when total_units_sold > 0
            then completed_units_sold / total_units_sold
            else 0
        end as unit_completion_rate,
        
        case 
            when total_net_revenue > 0
            then completed_revenue / total_net_revenue
            else 0
        end as revenue_completion_rate,
        
        -- Cancellation rates
        case 
            when total_units_sold > 0
            then cancelled_units / total_units_sold
            else 0
        end as unit_cancellation_rate,
        
        -- Seasonal preferences
        case 
            when spring_units >= summer_units and spring_units >= fall_units and spring_units >= winter_units then 'Spring'
            when summer_units >= fall_units and summer_units >= winter_units then 'Summer'
            when fall_units >= winter_units then 'Fall'
            else 'Winter'
        end as peak_season,
        
        -- Shopping preference
        case 
            when weekend_units > weekday_units then 'Weekend Popular'
            else 'Weekday Popular'
        end as day_type_preference,
        
        -- Time preference
        case 
            when morning_units >= afternoon_units and morning_units >= evening_units and morning_units >= night_units then 'Morning'
            when afternoon_units >= evening_units and afternoon_units >= night_units then 'Afternoon'
            when evening_units >= night_units then 'Evening'
            else 'Night'
        end as time_preference,
        
        -- Holiday performance
        case 
            when total_units_sold > 0 and holiday_units / total_units_sold > 0.3 then 'Holiday Sensitive'
            when total_units_sold > 0 and holiday_units / total_units_sold > 0.1 then 'Holiday Responsive'
            else 'Holiday Neutral'
        end as holiday_sensitivity,
        
        -- Days since last sale
        date_diff(current_date(), date(last_sale_date), day) as days_since_last_sale,
        
        -- Sales consistency (active days vs total days since first sale)
        case 
            when date_diff(date(last_sale_date), date(first_sale_date), day) > 0
            then active_sales_days / date_diff(date(last_sale_date), date(first_sale_date), day)
            else 1
        end as sales_consistency_ratio
        
    from product_metrics
),

-- Final enrichment with product attributes
final as (
    select 
        p.product_id,
        p.product_name,
        p.sku,
        p.brand,
        p.brand_category,
        p.category_id,
        p.current_price,
        p.product_cost,
        p.margin_percentage,
        p.price_category,
        p.product_status,
        p.is_available,
        p.product_lifecycle_stage,
        p.product_positioning,
        
        -- Performance metrics
        pp.*,
        
        -- Performance categorization
        case 
            when pp.total_net_revenue >= 10000 and pp.total_units_sold >= 100 then 'Star Product'
            when pp.total_net_revenue >= 5000 and pp.total_units_sold >= 50 then 'High Performer'
            when pp.total_net_revenue >= 1000 and pp.total_units_sold >= 20 then 'Good Performer'
            when pp.total_net_revenue >= 100 and pp.total_units_sold >= 5 then 'Average Performer'
            else 'Low Performer'
        end as performance_category,
        
        -- Inventory insights
        case 
            when pp.days_since_last_sale > 90 then 'Slow Moving'
            when pp.days_since_last_sale > 30 then 'Moderate Moving'
            else 'Fast Moving'
        end as inventory_movement,
        
        -- Pricing insights
        case 
            when pp.avg_discount_percentage > 0.3 then 'Heavy Discounting'
            when pp.avg_discount_percentage > 0.1 then 'Moderate Discounting'
            when pp.avg_discount_percentage > 0 then 'Light Discounting'
            else 'No Discounting'
        end as pricing_strategy,
        
        -- Customer appeal
        case 
            when pp.unique_customers >= 100 then 'Broad Appeal'
            when pp.unique_customers >= 50 then 'Moderate Appeal'
            when pp.unique_customers >= 10 then 'Niche Appeal'
            else 'Limited Appeal'
        end as customer_appeal,
        
        -- Data lineage
        current_timestamp() as dbt_processed_at
        
    from product_performance pp
    inner join products p on pp.product_id = p.product_id
)

select * from final