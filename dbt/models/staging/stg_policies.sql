{{
  config(
    materialized='view',
    tags=['staging', 'policies']
  )
}}

-- Staging model for policy data
-- Applies business logic and data standardization

with source_data as (
    select * from {{ source('raw_data', 'policies') }}
),

cleaned_data as (
    select
        policy_id,
        customer_id,
        upper(trim(policy_number)) as policy_number,
        
        -- Policy classification
        lower(trim(policy_type)) as policy_type,
        trim(product_name) as product_name,
        lower(trim(policy_status)) as policy_status,
        
        -- Dates
        effective_date,
        expiration_date,
        extract(day from (expiration_date - effective_date)) as policy_term_days,
        case 
            when extract(day from (expiration_date - effective_date)) <= 180 then 'Short Term (≤6 months)'
            when extract(day from (expiration_date - effective_date)) <= 365 then 'Standard (6-12 months)'
            else 'Long Term (>1 year)'
        end as policy_term_category,
        
        -- Financial amounts
        premium_amount,
        coverage_amount,
        deductible_amount,
        
        -- Calculated financial metrics
        case 
            when premium_amount > 0 then coverage_amount / premium_amount 
            else null 
        end as coverage_to_premium_ratio,
        
        case 
            when premium_amount <= {{ var('premium_tier_thresholds.basic') }} then 'Basic'
            when premium_amount <= {{ var('premium_tier_thresholds.standard') }} then 'Standard'
            else 'Premium'
        end as premium_tier,
        
        -- Monthly premium calculation
        case 
            when extract(day from (expiration_date - effective_date)) > 0 
            then premium_amount / (extract(day from (expiration_date - effective_date)) / 30.0)
            else premium_amount
        end as monthly_premium_estimate,
        
        -- Relationships
        agent_id,
        underwriter_id,
        
        -- Policy status flags
        case when policy_status = 'active' then true else false end as is_active,
        case when expiration_date >= current_date then true else false end as is_current,
        case when effective_date <= current_date and expiration_date >= current_date then true else false end as is_in_force,
        
        -- Age calculations
        extract(day from (current_date - effective_date)) as policy_age_days,
        case 
            when extract(day from (current_date - effective_date)) <= 30 then 'New (≤30 days)'
            when extract(day from (current_date - effective_date)) <= 365 then 'Current Year'
            when extract(day from (current_date - effective_date)) <= 730 then 'Previous Year'
            else 'Legacy (>2 years)'
        end as policy_age_category,
        
        -- Metadata
        created_at,
        updated_at,
        source_system,
        
        -- Data quality checks
        case when premium_amount > 0 then true else false end as is_premium_valid,
        case when coverage_amount >= premium_amount then true else false end as is_coverage_reasonable,
        case when effective_date <= expiration_date then true else false end as are_dates_logical
        
    from source_data
),

final as (
    select 
        *,
        -- Overall data quality assessment
        case 
            when is_premium_valid and is_coverage_reasonable and are_dates_logical then 'High'
            when (is_premium_valid and is_coverage_reasonable) or (is_premium_valid and are_dates_logical) then 'Medium'
            else 'Low'
        end as data_quality_score,
        
        -- Business priority classification
        case 
            when policy_status = 'active' and premium_amount > {{ var('premium_tier_thresholds.standard') }} then 'High Value Active'
            when policy_status = 'active' then 'Standard Active'
            when policy_status in ('cancelled', 'expired') then 'Inactive'
            else 'Other'
        end as business_priority
        
    from cleaned_data
)

select * from final