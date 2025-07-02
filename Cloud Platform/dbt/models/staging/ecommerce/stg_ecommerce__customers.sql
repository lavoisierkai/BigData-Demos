{{ config(
    materialized='view',
    docs={'node_color': '#F8C471'}
) }}

with source as (
    select * from {{ source('ecommerce_raw', 'customers') }}
),

renamed as (
    select
        -- Primary key
        customer_id,
        
        -- Customer identifiers
        email,
        phone,
        
        -- Customer details
        first_name,
        last_name,
        {{ dbt_utils.generate_surrogate_key(['first_name', 'last_name']) }} as full_name_key,
        concat(
            coalesce(first_name, ''), 
            ' ', 
            coalesce(last_name, '')
        ) as full_name,
        
        -- Customer classification
        customer_segment,
        status as customer_status,
        
        -- Timestamp fields
        created_at as customer_created_at,
        updated_at as customer_updated_at,
        
        -- Data quality flags
        case 
            when email is null or email = '' then false
            when not regexp_contains(email, r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') then false
            else true
        end as is_valid_email,
        
        case 
            when first_name is null or first_name = '' then false
            when last_name is null or last_name = '' then false
            else true
        end as has_complete_name,
        
        case 
            when phone is null or phone = '' then false
            when length(regexp_replace(phone, r'[^0-9]', '')) < 10 then false
            else true
        end as is_valid_phone,
        
        -- Derived fields
        case 
            when customer_segment = 'premium' then 1
            when customer_segment = 'standard' then 2
            when customer_segment = 'basic' then 3
            when customer_segment = 'trial' then 4
            else 5
        end as segment_priority,
        
        -- Active status flag
        case 
            when status = 'active' then true
            else false
        end as is_active_customer,
        
        -- Customer tenure
        date_diff(current_date(), date(created_at), day) as customer_tenure_days,
        
        -- Data lineage
        current_timestamp() as dbt_processed_at,
        '{{ var("dbt_run_started_at") }}' as dbt_run_started_at

    from source
),

final as (
    select 
        *,
        
        -- Data quality score
        (
            cast(is_valid_email as int) +
            cast(has_complete_name as int) +
            cast(is_valid_phone as int)
        ) / 3.0 as data_quality_score
        
    from renamed
)

select * from final