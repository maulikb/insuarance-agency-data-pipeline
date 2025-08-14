

-- Staging model for claims data
-- Standardizes claim information and calculates business metrics

with source_data as (
    select * from "insurance_db"."raw_data"."claims"
),

cleaned_data as (
    select
        claim_id,
        policy_id,
        upper(trim(claim_number)) as claim_number,
        
        -- Claim classification
        lower(trim(claim_type)) as claim_type,
        lower(trim(claim_status)) as claim_status,
        
        -- Important dates
        incident_date,
        reported_date,
        
        -- Date-based calculations
        (reported_date::date - incident_date::date) as report_delay_days,
        case 
            when (reported_date::date - incident_date::date) = 0 then 'Same Day'
            when (reported_date::date - incident_date::date) <= 7 then 'Within Week'
            when (reported_date::date - incident_date::date) <= 30 then 'Within Month'
            else 'Over Month'
        end as report_delay_category,
        
        (current_date - reported_date::date) as claim_age_days,
        case 
            when (current_date - reported_date::date) <= 30 then 'Recent (≤30 days)'
            when (current_date - reported_date::date) <= 90 then 'Current (31-90 days)'
            when (current_date - reported_date::date) <= 180 then 'Aging (91-180 days)'
            else 'Old (>180 days)'
        end as claim_age_category,
        
        -- Financial amounts
        claim_amount,
        settlement_amount,
        
        -- Financial calculations
        case 
            when claim_amount > 0 and settlement_amount is not null 
            then settlement_amount / claim_amount
            else null 
        end as settlement_ratio,
        
        case 
            when settlement_amount is not null then claim_amount - settlement_amount
            else null
        end as reserve_amount,
        
        -- Claim severity classification
        case 
            when claim_amount <= 5000 then 'Minor'
            when claim_amount <= 25000 then 'Moderate'
            when claim_amount <= 100000 then 'Major'
            else 'Catastrophic'
        end as claim_severity,
        
        -- Status flags
        case when claim_status in ('approved', 'closed') and settlement_amount is not null then true else false end as is_settled,
        case when claim_status = 'denied' then true else false end as is_denied,
        case when claim_status in ('open', 'investigating') then true else false end as is_open,
        case when claim_amount > 25000 then true else false end as is_high_value,
        
        -- Investigation details
        adjuster_id,
        trim(description) as description,
        trim(incident_location) as incident_location,
        case 
            when incident_location is not null and trim(incident_location) != '' 
            then split_part(trim(incident_location), ',', -1) -- Extract state from location
            else null
        end as incident_state,
        
        case 
            when police_report_number is not null and trim(police_report_number) != ''
            then upper(trim(police_report_number))
            else null
        end as police_report_number,
        
        -- Flags for police involvement
        case when police_report_number is not null then true else false end as has_police_report,
        
        -- Metadata
        created_at,
        updated_at,
        source_system,
        
        -- Data quality checks
        case when claim_amount > 0 then true else false end as is_claim_amount_valid,
        case when incident_date <= reported_date then true else false end as are_dates_logical,
        case when incident_date <= current_date then true else false end as is_incident_date_valid,
        case 
            when settlement_amount is null or settlement_amount <= claim_amount 
            then true else false 
        end as is_settlement_reasonable
        
    from source_data
),

final as (
    select 
        *,
        -- Overall data quality assessment
        case 
            when is_claim_amount_valid and are_dates_logical and is_incident_date_valid and is_settlement_reasonable then 'High'
            when (is_claim_amount_valid and are_dates_logical) or (is_claim_amount_valid and is_incident_date_valid) then 'Medium'
            else 'Low'
        end as data_quality_score,
        
        -- Business priority for claims handling
        case 
            when is_high_value and is_open then 'Critical - High Value Open'
            when claim_age_days > 180 and is_open then 'Critical - Aging Open'
            when is_high_value then 'High Priority'
            when is_open then 'Standard Open'
            else 'Closed/Low Priority'
        end as handling_priority,
        
        -- Expected processing timeline
        case 
            when claim_severity = 'Minor' then '7-14 days'
            when claim_severity = 'Moderate' then '14-30 days'
            when claim_severity = 'Major' then '30-60 days'
            else '60+ days'
        end as expected_processing_time
        
    from cleaned_data
)

select * from final