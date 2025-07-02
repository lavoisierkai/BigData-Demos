{{ config(
    materialized='view',
    docs={'node_color': '#F8C471'}
) }}

with source as (
    select * from {{ source('ecommerce_raw', 'order_items') }}
),

renamed as (
    select
        -- Primary key
        order_item_id,
        
        -- Foreign keys
        order_id,
        product_id,
        
        -- Item details
        quantity,
        unit_price,
        discount_amount,
        
        -- Timestamp fields
        created_at as item_created_at,
        updated_at as item_updated_at,
        
        -- Calculated fields
        (quantity * unit_price) as gross_item_amount,
        (quantity * unit_price) - coalesce(discount_amount, 0) as net_item_amount,
        
        -- Discount analysis
        coalesce(discount_amount, 0) as discount_amount_clean,
        case 
            when discount_amount is null or discount_amount = 0 then 0
            else discount_amount / (quantity * unit_price)
        end as discount_percentage,
        
        case 
            when discount_amount is null or discount_amount = 0 then false
            else true
        end as has_discount,
        
        -- Price point analysis
        case 
            when unit_price < 25 then 'Budget'
            when unit_price < 100 then 'Standard'
            when unit_price < 500 then 'Premium'
            else 'Luxury'
        end as price_tier,
        
        -- Quantity analysis
        case 
            when quantity = 1 then 'Single Item'
            when quantity between 2 and 5 then 'Small Quantity'
            when quantity between 6 and 20 then 'Medium Quantity'
            else 'Bulk Purchase'
        end as quantity_category,
        
        -- Revenue impact
        case 
            when (quantity * unit_price) - coalesce(discount_amount, 0) >= 100 then 'High Impact'
            when (quantity * unit_price) - coalesce(discount_amount, 0) >= 50 then 'Medium Impact'
            else 'Low Impact'
        end as revenue_impact,
        
        -- Data quality flags
        case 
            when quantity <= 0 then false
            when unit_price <= 0 then false
            when discount_amount < 0 then false
            when discount_amount > (quantity * unit_price) then false
            else true
        end as is_valid_line_item,
        
        -- Data lineage
        current_timestamp() as dbt_processed_at,
        '{{ var("dbt_run_started_at") }}' as dbt_run_started_at

    from source
),

with_margins as (
    select 
        *,
        
        -- Margin calculations (would need cost data from products)
        -- For now, using simplified assumptions
        case 
            when price_tier = 'Budget' then net_item_amount * 0.15      -- 15% margin
            when price_tier = 'Standard' then net_item_amount * 0.25    -- 25% margin
            when price_tier = 'Premium' then net_item_amount * 0.35     -- 35% margin
            when price_tier = 'Luxury' then net_item_amount * 0.45      -- 45% margin
        end as estimated_margin,
        
        -- Discount impact analysis
        case 
            when discount_percentage > 0.5 then 'Heavy Discount'
            when discount_percentage > 0.3 then 'Moderate Discount'
            when discount_percentage > 0.1 then 'Light Discount'
            when discount_percentage > 0 then 'Minimal Discount'
            else 'No Discount'
        end as discount_category,
        
        -- Unit economics
        net_item_amount / quantity as net_price_per_unit
        
    from renamed
)

select * from with_margins