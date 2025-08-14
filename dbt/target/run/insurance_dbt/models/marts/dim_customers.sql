
  
    

  create  table "insurance_db"."staging_marts"."dim_customers__dbt_tmp"
  
  
    as
  
  (
    

-- Customer dimension table
-- Provides comprehensive customer view for analytics

with customer_base as (
    select * from "insurance_db"."staging_staging"."stg_customers"
),

customer_policy_summary as (
    select 
        customer_id,
        count(distinct policy_id) as total_policies,
        count(distinct case when is_active then policy_id end) as active_policies,
        sum(case when is_active then premium_amount else 0 end) as total_active_premium,
        sum(premium_amount) as lifetime_premium,
        min(effective_date) as first_policy_date,
        max(effective_date) as latest_policy_date,
        
        -- Policy type diversity
        count(distinct policy_type) as policy_types_count,
        string_agg(distinct policy_type, ', ' order by policy_type) as policy_types,
        
        -- Premium tiers
        count(distinct case when premium_tier = 'Premium' then policy_id end) as premium_tier_policies,
        count(distinct case when premium_tier = 'Standard' then policy_id end) as standard_tier_policies,
        count(distinct case when premium_tier = 'Basic' then policy_id end) as basic_tier_policies
        
    from "insurance_db"."staging_staging"."stg_policies"
    group by customer_id
),

customer_claims_summary as (
    select 
        p.customer_id,
        count(distinct c.claim_id) as total_claims,
        count(distinct case when c.is_open then c.claim_id end) as open_claims,
        sum(c.claim_amount) as total_claimed_amount,
        sum(c.settlement_amount) as total_settled_amount,
        
        -- Claims by severity
        count(distinct case when c.claim_severity = 'Minor' then c.claim_id end) as minor_claims,
        count(distinct case when c.claim_severity = 'Moderate' then c.claim_id end) as moderate_claims,
        count(distinct case when c.claim_severity = 'Major' then c.claim_id end) as major_claims,
        count(distinct case when c.claim_severity = 'Catastrophic' then c.claim_id end) as catastrophic_claims,
        
        -- Recent claims activity
        count(distinct case when c.claim_age_days <= 365 then c.claim_id end) as claims_last_year,
        
        -- Average settlement ratio
        avg(case when c.is_settled then c.settlement_ratio else null end) as avg_settlement_ratio
        
    from "insurance_db"."staging_staging"."stg_policies" p
    left join "insurance_db"."staging_staging"."stg_claims" c on p.policy_id = c.policy_id
    group by p.customer_id
),

final as (
    select
        -- Customer identifiers
        c.customer_id,
        c.full_name,
        c.first_name,
        c.last_name,
        c.email,
        c.phone_cleaned as phone,
        
        -- Demographics
        c.age,
        c.age_group,
        c.date_of_birth,
        
        -- Address
        c.address_line_1,
        c.address_line_2,
        c.city,
        c.state_code,
        c.zip_code,
        c.country,
        
        -- Customer classification
        c.customer_type,
        c.risk_score,
        c.risk_category,
        
        -- Policy portfolio metrics
        coalesce(ps.total_policies, 0) as total_policies,
        coalesce(ps.active_policies, 0) as active_policies,
        coalesce(ps.total_active_premium, 0) as total_active_premium,
        coalesce(ps.lifetime_premium, 0) as lifetime_premium,
        ps.first_policy_date,
        ps.latest_policy_date,
        
        -- Customer tenure
        extract(day from (current_date - ps.first_policy_date)) as customer_tenure_days,
        case 
            when ps.first_policy_date is null then 'No Policies'
            when extract(day from (current_date - ps.first_policy_date)) <= 365 then 'New (≤1 year)'
            when extract(day from (current_date - ps.first_policy_date)) <= 1095 then 'Established (1-3 years)'
            when extract(day from (current_date - ps.first_policy_date)) <= 1825 then 'Mature (3-5 years)'
            else 'Veteran (>5 years)'
        end as customer_tenure_category,
        
        -- Policy diversity
        coalesce(ps.policy_types_count, 0) as policy_types_count,
        ps.policy_types,
        coalesce(ps.premium_tier_policies, 0) as premium_tier_policies,
        coalesce(ps.standard_tier_policies, 0) as standard_tier_policies,
        coalesce(ps.basic_tier_policies, 0) as basic_tier_policies,
        
        -- Claims history
        coalesce(cs.total_claims, 0) as total_claims,
        coalesce(cs.open_claims, 0) as open_claims,
        coalesce(cs.total_claimed_amount, 0) as total_claimed_amount,
        coalesce(cs.total_settled_amount, 0) as total_settled_amount,
        coalesce(cs.claims_last_year, 0) as claims_last_year,
        
        -- Claims by severity
        coalesce(cs.minor_claims, 0) as minor_claims,
        coalesce(cs.moderate_claims, 0) as moderate_claims,
        coalesce(cs.major_claims, 0) as major_claims,
        coalesce(cs.catastrophic_claims, 0) as catastrophic_claims,
        
        -- Claims metrics
        case 
            when coalesce(ps.total_policies, 0) > 0 
            then coalesce(cs.total_claims, 0)::float / ps.total_policies 
            else 0 
        end as claims_per_policy_ratio,
        
        case 
            when coalesce(ps.lifetime_premium, 0) > 0 
            then coalesce(cs.total_claimed_amount, 0) / ps.lifetime_premium 
            else 0 
        end as claims_to_premium_ratio,
        
        cs.avg_settlement_ratio,
        
        -- Customer value segmentation
        case 
            when coalesce(ps.total_active_premium, 0) >= 5000 then 'High Value'
            when coalesce(ps.total_active_premium, 0) >= 2000 then 'Medium Value'
            when coalesce(ps.total_active_premium, 0) > 0 then 'Standard Value'
            else 'No Active Policies'
        end as customer_value_segment,
        
        -- Risk profile
        case 
            when coalesce(cs.claims_last_year, 0) >= 3 then 'High Claims Activity'
            when coalesce(cs.claims_last_year, 0) >= 1 then 'Some Claims Activity'
            else 'Low Claims Activity'
        end as claims_activity_profile,
        
        case 
            when c.risk_category = 'High Risk' and coalesce(cs.claims_last_year, 0) >= 2 then 'High Risk High Claims'
            when c.risk_category = 'High Risk' then 'High Risk'
            when coalesce(cs.claims_last_year, 0) >= 2 then 'High Claims'
            else 'Standard'
        end as overall_risk_profile,
        
        -- Data quality
        c.data_quality_score,
        c.is_email_valid,
        c.is_phone_valid,
        c.is_age_valid,
        
        -- Metadata
        c.created_at,
        c.updated_at,
        current_timestamp as dimension_updated_at
        
    from customer_base c
    left join customer_policy_summary ps on c.customer_id = ps.customer_id  
    left join customer_claims_summary cs on c.customer_id = cs.customer_id
)

select * from final
  );
  