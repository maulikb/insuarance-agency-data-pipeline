
  create view "insurance_db"."staging_staging"."stg_customers__dbt_tmp"
    
    
  as (
    

-- Staging model for customer data
-- Applies basic cleaning and standardization

with source_data as (
    select * from "insurance_db"."raw_data"."customers"
),

cleaned_data as (
    select
        customer_id,
        
        -- Name standardization
        initcap(trim(first_name)) as first_name,
        initcap(trim(last_name)) as last_name,
        trim(first_name) || ' ' || trim(last_name) as full_name,
        
        -- Contact information
        lower(trim(email)) as email,
        regexp_replace(phone, '[^0-9]', '', 'g') as phone_cleaned,
        phone as phone_original,
        
        -- Personal details
        date_of_birth,
        extract(year from age(date_of_birth)) as age,
        case 
            when extract(year from age(date_of_birth)) < 25 then 'Young Adult (18-24)'
            when extract(year from age(date_of_birth)) < 35 then 'Adult (25-34)'
            when extract(year from age(date_of_birth)) < 50 then 'Middle Age (35-49)'
            when extract(year from age(date_of_birth)) < 65 then 'Mature (50-64)'
            else 'Senior (65+)'
        end as age_group,
        
        -- Address standardization
        initcap(trim(address_line_1)) as address_line_1,
        case 
            when address_line_2 is not null and trim(address_line_2) != ''
            then initcap(trim(address_line_2))
            else null
        end as address_line_2,
        initcap(trim(city)) as city,
        upper(trim(state_code)) as state_code,
        regexp_replace(zip_code, '[^0-9-]', '', 'g') as zip_code,
        upper(trim(country)) as country,
        
        -- Business fields
        lower(trim(customer_type)) as customer_type,
        
        -- Risk assessment
        risk_score,
        case 
            when risk_score <= 3 then 'Low Risk'
            when risk_score <= 6 then 'Medium Risk'
            else 'High Risk'
        end as risk_category,
        
        -- Metadata
        created_at,
        updated_at,
        source_system,
        
        -- Data quality flags
        case when email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$' then true else false end as is_email_valid,
        case when length(regexp_replace(phone, '[^0-9]', '', 'g')) = 10 then true else false end as is_phone_valid,
        case when date_of_birth > current_date - interval '120 years' and date_of_birth < current_date - interval '18 years' then true else false end as is_age_valid
        
    from source_data
),

final as (
    select 
        *,
        -- Overall data quality score
        case 
            when is_email_valid and is_phone_valid and is_age_valid then 'High'
            when (is_email_valid and is_phone_valid) or (is_email_valid and is_age_valid) then 'Medium'
            else 'Low'
        end as data_quality_score
        
    from cleaned_data
)

select * from final
  );