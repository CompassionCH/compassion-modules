from odoo import api, models, fields, _
from odoo.exceptions import UserError

from dateutil.relativedelta import relativedelta
from odoo.osv.expression import get_unaccent_wrapper


class AccountReconcileModel(models.Model):
    _inherit = "account.reconcile.model"

    product_id = fields.Many2one("product.product", "Product", readonly=False)
    user_id = fields.Many2one("res.partner", "Ambassador", readonly=False)
    comment = fields.Char("Gift instructions", readonly=False)
    sponsorship_id = fields.Many2one(
        "recurring.contract", "Sponsorship", readonly=False
    )
    avoid_thankyou_letter = fields.Boolean(
        default=True,
        help="Check to disable thank you letter for donation",
        oldname="avoid_mobile_donation_notification"
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.account_id = self.product_id.property_account_income_id

    @api.model
    def product_changed(self, product_id):
        """
        Helper to get the account and analytic account in reconcile view.
        :param product_id:
        :return: account_id, analytic_id
        """
        if product_id and product_id["product_id"]:
            product = self.env["product.product"].browse(product_id["product_id"])
            account = product.property_account_income_id
            taxes = product.taxes_id
            res = {}
            if account:
                res["account_id"] = {
                    "id": account.id,
                    "display_name": account.display_name,
                }
            else:
                res["account_id"] = False

            if taxes:
                res["tax_id"] = {"id": taxes.id, "display_name": taxes.display_name}
            else:
                res["tax_id"] = False

            analytic_default = (
                self.env["account.analytic.default"]
                .account_get(product_id["product_id"])
            )
            analytic = analytic_default.analytic_id
            res["analytic_id"] = {
                "id": analytic.id, "display_name": analytic.display_name}
            res["analytic_tag_ids"] = [{
                "id": tag.id,
                "display_name": tag.display_name
            } for tag in analytic_default.analytic_tag_ids]
            return res
        return False

    def _get_invoice_matching_query(self, st_lines_with_partner, excluded_ids):
        ''' Returns the query applying the current invoice_matching reconciliation
        model to the provided statement lines.

        :param st_lines_with_partner: A list of tuples (statement_line, partner),
                                      associating each statement line to treate with
                                      the corresponding partner, given by the partner map
        :param excluded_ids:    Account.move.lines to exclude.
        :return:                (query, params)
        '''
        self.ensure_one()
        print("icit")
        if self.rule_type != 'invoice_matching':
            raise UserError(
                _('Programmation Error: Can\'t call _get_invoice_matching_query() for different rules than \'invoice_matching\''))

        unaccent = get_unaccent_wrapper(self._cr)

        # N.B: 'communication_flag' is there to distinguish invoice matching through the number/reference
        # (higher priority) from invoice matching using the partner (lower priority).
        query = r'''
        SELECT
            st_line.id                          AS id,
            aml.id                              AS aml_id,
            aml.currency_id                     AS aml_currency_id,
            aml.date_maturity                   AS aml_date_maturity,
            aml.amount_residual                 AS aml_amount_residual,
            aml.amount_residual_currency        AS aml_amount_residual_currency,
            ''' + self._get_select_communication_flag() + r''' AS communication_flag,
            ''' + self._get_select_payment_reference_flag() + r''' AS payment_reference_flag
        FROM account_bank_statement_line st_line
        JOIN account_move st_line_move          ON st_line_move.id = st_line.move_id
        JOIN res_company company                ON company.id = st_line_move.company_id
        , account_move_line aml
        LEFT JOIN account_move move             ON move.id = aml.move_id AND move.state = 'posted'
        LEFT JOIN account_account account       ON account.id = aml.account_id
        LEFT JOIN res_partner aml_partner       ON aml.partner_id = aml_partner.id
        LEFT JOIN account_payment payment       ON payment.move_id = move.id
        WHERE
            aml.company_id = st_line_move.company_id
            AND move.state = 'posted'
            AND account.reconcile IS TRUE
            AND aml.reconciled IS FALSE
            AND strpos(move.payment_reference, st_line_move.ref)>0
        '''

        # Add conditions to handle each of the statement lines we want to match
        st_lines_queries = []
        for st_line, partner in st_lines_with_partner:
            # In case we don't have any partner for this line, we try assigning one with the rule mapping
            if st_line.amount > 0:
                st_line_subquery = r"aml.balance > 0"
            else:
                st_line_subquery = r"aml.balance < 0"

            if self.match_same_currency:
                st_line_subquery += r" AND COALESCE(aml.currency_id, company.currency_id) = %s" % (
                            st_line.foreign_currency_id.id or st_line.move_id.currency_id.id)

            if partner:
                st_line_subquery += r" AND aml.partner_id = %s" % partner.id
            else:
                st_line_fields_consideration = [
                    (self.match_text_location_label, 'st_line.payment_ref'),
                    (self.match_text_location_note, 'st_line_move.narration'),
                    (self.match_text_location_reference, 'st_line_move.ref'),
                ]

                no_partner_query = " OR ".join([
                    r"""
                        (
                            substring(REGEXP_REPLACE(""" + sql_field + """, '[^0-9\s]', '', 'g'), '\S(?:.*\S)*') != ''
                            AND
                            (
                                (""" + self._get_select_communication_flag() + """)
                                OR
                                (""" + self._get_select_payment_reference_flag() + """)
                            )
                        )
                        OR
                        (
                            /* We also match statement lines without partners with amls
                            whose partner's name's parts (splitting on space) are all present
                            within the payment_ref, in any order, with any characters between them. */

                            aml_partner.name IS NOT NULL
                            AND """ + unaccent(sql_field) + r""" ~* ('^' || (
                                SELECT string_agg(concat('(?=.*\m', chunk[1], '\M)'), '')
                                  FROM regexp_matches(""" + unaccent("aml_partner.name") + r""", '\w{3,}', 'g') AS chunk
                            ))
                        )
                    """
                    for consider_field, sql_field in st_line_fields_consideration
                    if consider_field
                ])

                if no_partner_query:
                    st_line_subquery += " AND " + no_partner_query

            st_lines_queries.append(r"st_line.id = %s AND (%s)" % (st_line.id, st_line_subquery))

        query += r" AND (%s) " % " OR ".join(st_lines_queries)

        params = {}

        # If this reconciliation model defines a past_months_limit, we add a condition
        # to the query to only search on move lines that are younger than this limit.
        if self.past_months_limit:
            date_limit = fields.Date.context_today(self) - relativedelta(months=self.past_months_limit)
            query += "AND aml.date >= %(aml_date_limit)s"
            params['aml_date_limit'] = date_limit

        # Filter out excluded account.move.line.
        if excluded_ids:
            query += 'AND aml.id NOT IN %(excluded_aml_ids)s'
            params['excluded_aml_ids'] = tuple(excluded_ids)

        query += """
            ORDER BY CASE
                WHEN EXTRACT(MONTH from aml.date_maturity) = EXTRACT(MONTH from NOW())
                AND EXTRACT(YEAR from aml.date_maturity) = EXTRACT(YEAR from NOW())
                THEN 0
                ELSE 1
            END, aml_date_maturity, aml_id;
        """

        return query, params

