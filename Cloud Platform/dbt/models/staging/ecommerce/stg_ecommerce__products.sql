{{ config(
    materialized='view',
    docs={'node_color': '#F8C471'}
) }}

with source as (
    select * from {{ source('ecommerce_raw', 'products') }}
),

renamed as (
    select
        -- Primary key
        product_id,
        
        -- Foreign keys
        category_id,
        
        -- Product identifiers
        product_name,
        sku,
        brand,
        
        -- Financial data
        price as current_price,
        cost as product_cost,
        
        -- Physical attributes
        weight,
        dimensions,
        
        -- Status and metadata
        status as product_status,
        created_at as product_created_at,
        updated_at as product_updated_at,
        
        -- Calculated fields
        case 
            when cost > 0 and cost is not null 
            then (price - cost) / price 
            else null
        end as margin_percentage,
        
        case 
            when cost > 0 and cost is not null 
            then price - cost 
            else null
        end as gross_margin,
        
        -- Price categorization
        case 
            when price < 25 then 'Budget'
            when price < 100 then 'Standard'
            when price < 500 then 'Premium'
            else 'Luxury'
        end as price_category,
        
        -- Weight categorization
        case 
            when weight is null then 'Unknown'
            when weight < 100 then 'Light'
            when weight < 1000 then 'Medium'
            when weight < 5000 then 'Heavy'
            else 'Very Heavy'
        end as weight_category,
        
        -- Brand categorization (simplified)
        case 
            when brand is null or brand = '' then 'No Brand'
            when upper(brand) in ('APPLE', 'NIKE', 'SAMSUNG', 'SONY', 'MICROSOFT') then 'Premium Brand'
            else 'Standard Brand'
        end as brand_category,
        
        -- Product name analysis
        length(product_name) as name_length,
        case 
            when lower(product_name) like '%sale%' or lower(product_name) like '%clearance%' then true
            else false
        end as is_sale_item,
        
        case 
            when lower(product_name) like '%new%' or lower(product_name) like '%latest%' then true
            else false
        end as is_new_product,
        
        -- Availability flags
        case 
            when status = 'active' then true
            else false
        end as is_available,
        
        case 
            when status = 'discontinued' then true
            else false
        end as is_discontinued,
        
        -- Product lifecycle
        date_diff(current_date(), date(created_at), day) as product_age_days,
        
        case 
            when date_diff(current_date(), date(created_at), day) < 30 then 'New'
            when date_diff(current_date(), date(created_at), day) < 365 then 'Recent'
            when date_diff(current_date(), date(created_at), day) < 1095 then 'Mature'
            else 'Legacy'
        end as product_lifecycle_stage,
        
        -- SKU analysis
        length(sku) as sku_length,
        case 
            when regexp_contains(sku, r'^[A-Z]{2,3}-\d{4,6}$') then 'Standard Format'
            when regexp_contains(sku, r'^\d+$') then 'Numeric Only'
            when regexp_contains(sku, r'^[A-Z]+$') then 'Alpha Only'
            else 'Non-Standard Format'
        end as sku_format,
        
        -- Data quality checks
        case 
            when product_name is null or product_name = '' then false
            when sku is null or sku = '' then false
            when price is null or price <= 0 then false
            when category_id is null then false
            else true
        end as is_valid_product,
        
        -- Dimensions parsing (assuming JSON format like '{"length": 10, "width": 5, "height": 3}')
        case 
            when dimensions is not null 
            then json_extract_scalar(dimensions, '$.length')
            else null
        end as product_length,
        
        case 
            when dimensions is not null 
            then json_extract_scalar(dimensions, '$.width')
            else null
        end as product_width,
        
        case 
            when dimensions is not null 
            then json_extract_scalar(dimensions, '$.height')
            else null
        end as product_height,
        
        -- Data lineage
        current_timestamp() as dbt_processed_at,
        '{{ var("dbt_run_started_at") }}' as dbt_run_started_at

    from source
),

with_calculated_metrics as (
    select 
        *,
        
        -- Volume calculation
        case 
            when product_length is not null 
                and product_width is not null 
                and product_height is not null
            then cast(product_length as float64) * 
                 cast(product_width as float64) * 
                 cast(product_height as float64)
            else null
        end as product_volume,
        
        -- Margin category
        case 
            when margin_percentage is null then 'Unknown'
            when margin_percentage < 0.1 then 'Low Margin'
            when margin_percentage < 0.3 then 'Medium Margin'
            when margin_percentage < 0.5 then 'High Margin'
            else 'Premium Margin'
        end as margin_category,
        
        -- Price per weight ratio
        case 
            when weight > 0 then price / weight * 1000  -- Price per kg
            else null
        end as price_per_kg,
        
        -- Product positioning
        case 
            when price_category = 'Luxury' and brand_category = 'Premium Brand' then 'Luxury Premium'
            when price_category = 'Premium' and brand_category = 'Premium Brand' then 'Premium'
            when price_category in ('Standard', 'Premium') and brand_category = 'Standard Brand' then 'Mainstream'
            when price_category = 'Budget' then 'Value'
            else 'Other'
        end as product_positioning
        
    from renamed
)

select * from with_calculated_metrics