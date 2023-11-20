CREATE OR REPLACE VIEW mis_spn_info AS (
    SELECT row_number() OVER (ORDER BY a.date) AS id, a.*
    FROM (
    -- all acquisition, new start
        SELECT
            CASE
                WHEN start_date::date < activation_date::date THEN start_date::date
                ELSE activation_date::date
            END AS date,
            %s AS account_id,
            correspondent_id,
            rc.partner_id,
            0 AS debit,
            1 AS credit,
            -1 as amount_currency,
            rc.id AS contract_id,
            %s AS currency_id,
            child_id,
            rc.company_id as report_company_id,
            %s as company_id,
            rco.analytic_id,
            pricelist_id,
            medium_id,
            source_id,
            campaign_id,
            sponsorship_line_id,
            sub_sponsorship_id,
            parent_id,
            end_reason_id,
            activation_date
        FROM
            recurring_contract rc
            LEFT JOIN recurring_contract_origin rco ON rco.id = rc.origin_id
        WHERE
            activation_date IS NOT NULL
            AND child_id IS NOT NULL

        UNION

        SELECT
            end_date::date AS date,
            %s AS account_id,
            correspondent_id,
            rc.partner_id,
            1 AS debit,
            0 AS credit,
            1 as amount_currency,
            rc.id AS contract_id,
            %s AS currency_id,
            child_id,
            rc.company_id as report_company_id,
            %s as company_id,
            rco.analytic_id,
            pricelist_id,
            medium_id,
            source_id,
            campaign_id,
            sponsorship_line_id,
            sub_sponsorship_id,
            parent_id,
            end_reason_id,
            activation_date
        FROM
            recurring_contract rc
            LEFT JOIN recurring_contract_origin rco ON rco.id = rc.origin_id
        WHERE
            activation_date IS NOT NULL
            AND end_date IS NOT NULL
            AND child_id IS NOT NULL

        UNION

        SELECT
            CASE
                WHEN activation_date IS NULL and start_date IS NULL THEN end_date::date
                WHEN activation_date IS NULL THEN start_date::date
                WHEN start_date::date < activation_date::date THEN start_date::date
                ELSE activation_date::date
            END AS date,
            %s AS account_id,
            correspondent_id,
            rc.partner_id,
            0 AS debit,
            1 AS credit,
            -1 as amount_currency,
            rc.id AS contract_id,
            %s AS currency_id,
            child_id,
            rc.company_id as report_company_id,
            %s as company_id,
            rco.analytic_id,
            pricelist_id,
            medium_id,
            source_id,
            campaign_id,
            sponsorship_line_id,
            sub_sponsorship_id,
            parent_id,
            end_reason_id,
            activation_date
        FROM
            recurring_contract rc
            LEFT JOIN recurring_contract_origin rco ON rco.id = rc.origin_id
        WHERE
--            (activation_date IS NULL OR
--            date_trunc('month', activation_date) > date_trunc('month', start_date))
--            AND
            child_id IS NOT NULL

        UNION
--
        SELECT
            CASE
                WHEN activation_date::date IS NULL THEN end_date::date
                ELSE activation_date::date
            END AS date,
            %s AS account_id,
            correspondent_id,
            rc.partner_id,
            1 AS debit,
            0 AS credit,
            1 as amount_currency,
            rc.id AS contract_id,
            %s AS currency_id,
            child_id,
            rc.company_id as report_company_id,
            %s as company_id,
            rco.analytic_id,
            pricelist_id,
            medium_id,
            source_id,
            campaign_id,
            sponsorship_line_id,
            sub_sponsorship_id,
            parent_id,
            end_reason_id,
            activation_date
        FROM
            recurring_contract rc
            LEFT JOIN recurring_contract_origin rco ON rco.id = rc.origin_id
        WHERE
            (activation_date is not null OR end_date is not null)
            AND child_id IS NOT NULL
        ) a
)
