
      
  
    

  create  table "insurance_db"."staging_marts"."fact_daily_metrics"
  
  
    as
  
  (
    

-- Daily business metrics fact table
-- Aggregates key business metrics by date, policy type, and geography

with daily_policy_metrics as (
    select 
        date_trunc('day', created_at)::date as metric_date,
        p.policy_type,
        c.state_code,
        
        -- New business metrics
        count(distinct p.policy_id) as new_policies_count,
        sum(p.premium_amount) as new_policies_premium,
        avg(p.premium_amount) as avg_new_policy_premium,
        sum(p.coverage_amount) as new_policies_coverage,
        
        -- Customer metrics
        count(distinct p.customer_id) as new_customers_count,
        
        -- Premium tiers
        count(distinct case when p.premium_tier = 'Premium' then p.policy_id end) as premium_tier_count,
        count(distinct case when p.premium_tier = 'Standard' then p.policy_id end) as standard_tier_count,
        count(distinct case when p.premium_tier = 'Basic' then p.policy_id end) as basic_tier_count
        
    from "insurance_db"."staging_staging"."stg_policies" p
    inner join "insurance_db"."staging_staging"."stg_customers" c on p.customer_id = c.customer_id
    where date_trunc('day', p.created_at)::date = '2024-01-01'
    
    
    
    group by 1, 2, 3
),

daily_claims_metrics as (
    select 
        date_trunc('day', cl.reported_date)::date as metric_date,
        p.policy_type,
        c.state_code,
        
        -- Claims volume
        count(distinct cl.claim_id) as new_claims_count,
        sum(cl.claim_amount) as new_claims_amount,
        avg(cl.claim_amount) as avg_claim_amount,
        sum(case when cl.is_settled then cl.settlement_amount else 0 end) as settled_amount,
        
        -- Claims by severity
        count(distinct case when cl.claim_severity = 'Minor' then cl.claim_id end) as minor_claims_count,
        count(distinct case when cl.claim_severity = 'Moderate' then cl.claim_id end) as moderate_claims_count,
        count(distinct case when cl.claim_severity = 'Major' then cl.claim_id end) as major_claims_count,
        count(distinct case when cl.claim_severity = 'Catastrophic' then cl.claim_id end) as catastrophic_claims_count,
        
        -- High value claims
        count(distinct case when cl.is_high_value then cl.claim_id end) as high_value_claims_count,
        
        -- Report delay metrics
        avg(cl.report_delay_days) as avg_report_delay_days,
        count(distinct case when cl.report_delay_category = 'Same Day' then cl.claim_id end) as same_day_reports,
        
        -- Affected policies
        count(distinct cl.policy_id) as policies_with_claims
        
    from "insurance_db"."staging_staging"."stg_claims" cl
    inner join "insurance_db"."staging_staging"."stg_policies" p on cl.policy_id = p.policy_id
    inner join "insurance_db"."staging_staging"."stg_customers" c on p.customer_id = c.customer_id
    where date_trunc('day', cl.reported_date)::date = '2024-01-01'
    
    
    
    group by 1, 2, 3
),

daily_payment_metrics as (
    select 
        date_trunc('day', py.payment_date)::date as metric_date,
        p.policy_type,
        c.state_code,
        
        -- Payment volume and amounts
        count(distinct py.payment_id) as payments_count,
        sum(py.payment_amount) as total_payments_amount,
        avg(py.payment_amount) as avg_payment_amount,
        
        -- Payment success rates
        count(distinct case when py.payment_status = 'completed' then py.payment_id end) as successful_payments,
        count(distinct case when py.payment_status = 'failed' then py.payment_id end) as failed_payments,
        
        -- Payment methods
        count(distinct case when py.payment_method = 'credit_card' then py.payment_id end) as credit_card_payments,
        count(distinct case when py.payment_method = 'bank_transfer' then py.payment_id end) as bank_transfer_payments,
        count(distinct case when py.payment_method = 'check' then py.payment_id end) as check_payments,
        
        -- Unique policies with payments
        count(distinct py.policy_id) as policies_with_payments
        
    from "insurance_db"."raw_data"."payments" py
    inner join "insurance_db"."staging_staging"."stg_policies" p on py.policy_id = p.policy_id
    inner join "insurance_db"."staging_staging"."stg_customers" c on p.customer_id = c.customer_id
    where date_trunc('day', py.payment_date)::date = '2024-01-01'
    
    
    
    group by 1, 2, 3
),

portfolio_metrics as (
    select 
        '2024-01-01'::date as metric_date,
        p.policy_type,
        c.state_code,
        
        -- Active portfolio metrics
        count(distinct case when p.is_active then p.policy_id end) as active_policies_count,
        sum(case when p.is_active then p.premium_amount else 0 end) as active_premium_portfolio,
        sum(case when p.is_active then p.coverage_amount else 0 end) as active_coverage_portfolio,
        
        -- Customer base
        count(distinct case when p.is_active then p.customer_id end) as active_customers_count
        
    from "insurance_db"."staging_staging"."stg_policies" p
    inner join "insurance_db"."staging_staging"."stg_customers" c on p.customer_id = c.customer_id
    where '2024-01-01'::date between p.effective_date and p.expiration_date
    group by 1, 2, 3
),

final as (
    select 
        coalesce(pm.metric_date, cm.metric_date, py.metric_date, po.metric_date) as metric_date,
        coalesce(pm.policy_type, cm.policy_type, py.policy_type, po.policy_type) as policy_type,
        coalesce(pm.state_code, cm.state_code, py.state_code, po.state_code) as state_code,
        
        -- New business metrics
        coalesce(pm.new_policies_count, 0) as new_policies_count,
        coalesce(pm.new_policies_premium, 0) as new_policies_premium,
        coalesce(pm.avg_new_policy_premium, 0) as avg_new_policy_premium,
        coalesce(pm.new_policies_coverage, 0) as new_policies_coverage,
        coalesce(pm.new_customers_count, 0) as new_customers_count,
        
        -- Premium tier distribution
        coalesce(pm.premium_tier_count, 0) as premium_tier_count,
        coalesce(pm.standard_tier_count, 0) as standard_tier_count, 
        coalesce(pm.basic_tier_count, 0) as basic_tier_count,
        
        -- Claims metrics
        coalesce(cm.new_claims_count, 0) as new_claims_count,
        coalesce(cm.new_claims_amount, 0) as new_claims_amount,
        coalesce(cm.avg_claim_amount, 0) as avg_claim_amount,
        coalesce(cm.settled_amount, 0) as settled_amount,
        
        -- Claims by severity
        coalesce(cm.minor_claims_count, 0) as minor_claims_count,
        coalesce(cm.moderate_claims_count, 0) as moderate_claims_count,
        coalesce(cm.major_claims_count, 0) as major_claims_count,
        coalesce(cm.catastrophic_claims_count, 0) as catastrophic_claims_count,
        coalesce(cm.high_value_claims_count, 0) as high_value_claims_count,
        
        -- Claims operational metrics
        coalesce(cm.avg_report_delay_days, 0) as avg_report_delay_days,
        coalesce(cm.same_day_reports, 0) as same_day_reports,
        coalesce(cm.policies_with_claims, 0) as policies_with_claims,
        
        -- Payment metrics
        coalesce(py.payments_count, 0) as payments_count,
        coalesce(py.total_payments_amount, 0) as total_payments_amount,
        coalesce(py.avg_payment_amount, 0) as avg_payment_amount,
        coalesce(py.successful_payments, 0) as successful_payments,
        coalesce(py.failed_payments, 0) as failed_payments,
        
        -- Payment methods
        coalesce(py.credit_card_payments, 0) as credit_card_payments,
        coalesce(py.bank_transfer_payments, 0) as bank_transfer_payments,
        coalesce(py.check_payments, 0) as check_payments,
        coalesce(py.policies_with_payments, 0) as policies_with_payments,
        
        -- Portfolio metrics
        coalesce(po.active_policies_count, 0) as active_policies_count,
        coalesce(po.active_premium_portfolio, 0) as active_premium_portfolio,
        coalesce(po.active_coverage_portfolio, 0) as active_coverage_portfolio,
        coalesce(po.active_customers_count, 0) as active_customers_count,
        
        -- Calculated KPIs
        case 
            when coalesce(pm.new_policies_count, 0) > 0 
            then coalesce(cm.new_claims_count, 0)::float / pm.new_policies_count 
            else 0 
        end as new_policies_claims_ratio,
        
        case 
            when coalesce(pm.new_policies_premium, 0) > 0 
            then coalesce(cm.new_claims_amount, 0) / pm.new_policies_premium 
            else 0 
        end as claims_to_new_premium_ratio,
        
        case 
            when coalesce(py.payments_count, 0) > 0 
            then coalesce(py.successful_payments, 0)::float / py.payments_count 
            else 0 
        end as payment_success_rate,
        
        case 
            when coalesce(cm.new_claims_count, 0) > 0 
            then coalesce(cm.same_day_reports, 0)::float / cm.new_claims_count 
            else 0 
        end as same_day_reporting_rate,
        
        -- Data quality indicators
        current_timestamp as created_at,
        '2024-01-01' as load_date
        
    from daily_policy_metrics pm
    full outer join daily_claims_metrics cm 
        on pm.metric_date = cm.metric_date 
        and pm.policy_type = cm.policy_type 
        and pm.state_code = cm.state_code
    full outer join daily_payment_metrics py 
        on coalesce(pm.metric_date, cm.metric_date) = py.metric_date 
        and coalesce(pm.policy_type, cm.policy_type) = py.policy_type 
        and coalesce(pm.state_code, cm.state_code) = py.state_code
    full outer join portfolio_metrics po 
        on coalesce(pm.metric_date, cm.metric_date, py.metric_date) = po.metric_date 
        and coalesce(pm.policy_type, cm.policy_type, py.policy_type) = po.policy_type 
        and coalesce(pm.state_code, cm.state_code, py.state_code) = po.state_code
)

select * from final
  );
  
  