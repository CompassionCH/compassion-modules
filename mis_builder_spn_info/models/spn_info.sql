CREATE OR REPLACE VIEW mis_spn_info AS (
select row_number() OVER (ORDER BY a.date) as id,a.*
from (
    select activation_date::date as date, aa.id  as account_id,correspondent_id ,rc.partner_id ,0 as debit, 1 as credit, rc.id as contract_id,18 as currency_id,
    	child_id ,rc.company_id, rco.analytic_id  , pricelist_id ,medium_id ,source_id ,campaign_id ,sponsorship_line_id ,sub_sponsorship_id, parent_id,end_reason_id
    from recurring_contract rc left join recurring_contract_origin rco on rco.id =rc.origin_id
    left join account_account aa on aa.company_id =rc.company_id and aa."name" ='Sponsroship count'
    where activation_date is not null and child_id is not null
    union
    select end_date::date as date ,aa.id  as account_id, correspondent_id ,rc.partner_id ,1 as debit, 0 as credit ,rc.id as contract_id,18 as currency_id,
    	child_id ,rc.company_id, rco.analytic_id , pricelist_id ,medium_id ,source_id ,campaign_id ,sponsorship_line_id ,sub_sponsorship_id, parent_id,end_reason_id
    from recurring_contract rc left join recurring_contract_origin rco on rco.id =rc.origin_id
    left join account_account aa on aa.company_id =rc.company_id and aa."name" ='Sponsroship count'
    where activation_date is not null and end_date is not null and child_id is not null
    ) a
)