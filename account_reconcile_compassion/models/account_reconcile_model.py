from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class AccountReconcileModel(models.Model):
    _inherit = "account.reconcile.model"

    avoid_thankyou_letter = fields.Boolean(
        default=True,
        help="Check to disable thank you letter for donation"
    )
    comment = fields.Char("Gift instructions", readonly=False)
    sponsorship_id = fields.Many2one(
        "recurring.contract", "Sponsorship", readonly=False
    )
    only_this_month = fields.Boolean(
        default=False, help="Check to search only from the start of the month"
    )

    @api.onchange("past_months_limit")
    def _uncheck_only_this_month(self):
        if self.past_months_limit and self.only_this_month:
            self.only_this_month = False

    @api.onchange("avoid_thankyou_letter")
    def _avoid_thankyou_letter(self):
        for line in self.line_ids:
            line.avoid_thankyou_letter = self.avoid_thankyou_letter
            print('avoid_thankyou_letter', line.avoid_thankyou_letter)

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
            product = (
                self.env["product.product"]
                .browse(product_id)
                .with_company(statement.company_id)
            )
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

            analytic_default = self.env["account.analytic.default"].account_get(
                product_id, company_id=statement.company_id.id
            )
            analytic = analytic_default.analytic_id
            res["analytic_id"] = {
                "id": analytic.id,
                "display_name": analytic.display_name,
            }
            res["analytic_tag_ids"] = [
                {"id": tag.id, "display_name": tag.display_name}
                for tag in analytic_default.analytic_tag_ids
            ]
            return res
        return False

    def _get_invoice_matching_query(self, st_lines_with_partner, excluded_ids):
        """Returns the query applying the current invoice_matching reconciliation
        model to the provided statement lines.

        :param st_lines_with_partner:
            A list of tuples (statement_line, partner),
            associating each statement line to treat with
            the corresponding partner, given by the partner map
        :param excluded_ids:    Account.move.lines to exclude.
        :return:                (query, params)
        """
        query, params = super()._get_invoice_matching_query(
            st_lines_with_partner, excluded_ids
        )
        for line in st_lines_with_partner:
            bs_line = line[0]
            bank_statement_date = bs_line.date or fields.Date.today()
            if self.past_months_limit == 0 and self.only_this_month:
                date_limit = bank_statement_date.replace(day=1)
            elif self.past_months_limit:
                date_limit = bank_statement_date - relativedelta(
                    months=self.past_months_limit
                )
            else:
                continue

            query = (
                query[: query.find(f"{bs_line.id} AND (") + 6 + len(str(bs_line.id))]
                + f" aml.date >= %(aml_date_limit{bs_line.id})s AND "
                + query[query.find(f"{bs_line.id} AND (") + 6 + len(str(bs_line.id)) :]
            )
            params[f"aml_date_limit{bs_line.id}"] = date_limit

        if params.get("aml_date_limit"):
            # We remove the date limit from the query because we use it inside each
            # line subquery.
            query = query.replace(" AND aml.date >= %(aml_date_limit)s", "")

        return query, params


class AccountReconcileModelLine(models.Model):
    _inherit = 'account.reconcile.model.line'

    product_id = fields.Many2one("product.product", "Product", readonly=False)
    avoid_thankyou_letter = fields.Boolean(
        default="self.model_id.avoid_thankyou_letter",
        readonly=True,
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.account_id = self.product_id.property_account_income_id
            self.analytic_tag_ids = (
                self.env["account.analytic.default"]
                .account_get(self.product_id.id, company_id=self.env.company.id)
                .analytic_tag_ids.ids
            )
