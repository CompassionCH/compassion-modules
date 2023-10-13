CREATE OR REPLACE VIEW mis_spn_info AS (
    SELECT row_number() OVER (ORDER BY a.date) AS id, a.*
    FROM (
        SELECT 
            CASE
                WHEN start_date::date < activation_date::date THEN start_date::date
                ELSE activation_date::date
            END AS date,
            aa.id AS account_id,
            correspondent_id,
            rc.partner_id,
            0 AS debit,
            1 AS credit,
            rc.id AS contract_id,
            18 AS currency_id,
            child_id,
            rc.company_id,
            rco.analytic_id,
            pricelist_id,
            medium_id,
            source_id,
            campaign_id,
            sponsorship_line_id,
            sub_sponsorship_id,
            parent_id,
            end_reason_id,
            FALSE as waiting,
            activation_date
        FROM
            recurring_contract rc
            LEFT JOIN recurring_contract_origin rco ON rco.id = rc.origin_id
            LEFT JOIN account_account aa ON aa.company_id = rc.company_id AND aa."name" = 'Child Sponsored'
        WHERE
            activation_date IS NOT NULL
            AND child_id IS NOT NULL

        UNION

        SELECT
            end_date::date AS date,
            aa.id AS account_id,
            correspondent_id,
            rc.partner_id,
            1 AS debit,
            0 AS credit,
            rc.id AS contract_id,
            18 AS currency_id,
            child_id,
            rc.company_id,
            rco.analytic_id,
            pricelist_id,
            medium_id,
            source_id,
            campaign_id,
            sponsorship_line_id,
            sub_sponsorship_id,
            parent_id,
            end_reason_id,
            FALSE as waiting,
            activation_date
        FROM
            recurring_contract rc
            LEFT JOIN recurring_contract_origin rco ON rco.id = rc.origin_id
            LEFT JOIN account_account aa ON aa.company_id = rc.company_id AND aa."name" = 'Child Sponsored'
        WHERE
            activation_date IS NOT NULL
            AND end_date IS NOT NULL
            AND child_id IS NOT NULL

        UNION

        SELECT
            CASE
                WHEN start_date::date < activation_date::date THEN start_date::date
                ELSE activation_date::date
            END AS date,
            aa.id AS account_id,
            correspondent_id,
            rc.partner_id,
            1 AS debit,
            0 AS credit,
            rc.id AS contract_id,
            18 AS currency_id,
            child_id,
            rc.company_id,
            rco.analytic_id,
            pricelist_id,
            medium_id,
            source_id,
            campaign_id,
            sponsorship_line_id,
            sub_sponsorship_id,
            parent_id,
            end_reason_id,
            TRUE as waiting,
            activation_date
        FROM
            recurring_contract rc
            LEFT JOIN recurring_contract_origin rco ON rco.id = rc.origin_id
            LEFT JOIN account_account aa ON aa.company_id = rc.company_id AND aa."name" = 'Child Sponsored'
        WHERE
            (activation_date IS NULL OR
            date_trunc('month', activation_date) > date_trunc('month', start_date))
            AND child_id IS NOT NULL


        UNION

--      Query to get the contracts which have been created but not activated yet
        SELECT
            CASE
                WHEN start_date::date < activation_date::date THEN start_date::date
                ELSE activation_date::date
            END AS date,
            aa.id AS account_id,
            correspondent_id,
            rc.partner_id,
            0 AS debit,
            1 AS credit,
            rc.id AS contract_id,
            18 AS currency_id,
            child_id,
            rc.company_id,
            rco.analytic_id,
            pricelist_id,
            medium_id,
            source_id,
            campaign_id,
            sponsorship_line_id,
            sub_sponsorship_id,
            parent_id,
            end_reason_id,
            FALSE as waiting,
            activation_date
        FROM
            recurring_contract rc
            LEFT JOIN recurring_contract_origin rco ON rco.id = rc.origin_id
            LEFT JOIN account_account aa ON aa.company_id = rc.company_id AND aa."name" = 'Contract Created'
        WHERE
            (activation_date IS NULL OR
            date_trunc('month', activation_date) > date_trunc('month', start_date))
            AND child_id IS NOT NULL


        UNION

--      Query to get the contracts which have been activated
        SELECT
            activation_date::date AS date,
            aa.id AS account_id,
            correspondent_id,
            rc.partner_id,
            1 AS debit,
            0 AS credit,
            rc.id AS contract_id,
            18 AS currency_id,
            child_id,
            rc.company_id,
            rco.analytic_id,
            pricelist_id,
            medium_id,
            source_id,
            campaign_id,
            sponsorship_line_id,
            sub_sponsorship_id,
            parent_id,
            end_reason_id,
            FALSE as waiting,
            activation_date
        FROM
            recurring_contract rc
            LEFT JOIN recurring_contract_origin rco ON rco.id = rc.origin_id
            LEFT JOIN account_account aa ON aa.company_id = rc.company_id AND aa."name" = 'Contract Created'
        WHERE
            child_id IS NOT NULL

        ) a
)