from dateutil.relativedelta import relativedelta

from odoo import api, models, fields


class AccountReconcileModel(models.Model):
    _inherit = "account.reconcile.model"

    product_id = fields.Many2one("product.product", "Product", readonly=False)
    # user_id = fields.Many2one("res.partner", "Ambassador", readonly=False)
    comment = fields.Char("Gift instructions", readonly=False)
    sponsorship_id = fields.Many2one(
        "recurring.contract", "Sponsorship", readonly=False
    )
    avoid_thankyou_letter = fields.Boolean(
        default=True,
        help="Check to disable thank you letter for donation"
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.account_id = self.with_company(self.company_id).product_id.property_account_income_id

    @api.model
    def product_changed(self, product_id, statement_id):
        """
        Helper to get the account and analytic account in reconcile view.
        :param product_id:
        :param statement_id:
        :return: account_id, analytic_id
        """
        if product_id:
            statement = self.env["account.bank.statement"].browse(statement_id)
            product = self.env["product.product"].browse(product_id).with_company(statement.company_id)
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
                .account_get(product_id, company_id=statement.company_id.id)
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
        query, params = super()._get_invoice_matching_query(st_lines_with_partner, excluded_ids)
        bank_statement_date = self.env.context.get("bank_statement_date")
        if params.get("aml_date_limit") and bank_statement_date:
            date_limit = bank_statement_date - relativedelta(months=self.past_months_limit)
            params['aml_date_limit'] = date_limit
        return query, params