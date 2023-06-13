##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class AccountStatement(models.Model):
    """ Adds a relation to a recurring invoicer. """

    _name = "account.bank.statement"
    _inherit = ["account.bank.statement", "mail.thread"]

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    invoice_ids = fields.One2many(
        "account.move",
        "bank_statement_id",
        string="Invoices",
        readonly=False,
    )
    generated_invoices_count = fields.Integer("Number invoices", compute="_compute_invoices")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_invoices(self):
        for stmt in self:
            stmt.generated_invoices_count = len(stmt.invoice_ids)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    def to_invoices(self):
        self.ensure_one()
        return {
            "name": "Generated Invoices",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "target": "current",
            "context": {
                "form_view_ref": "account.view_move_form",
                "journal_type": "sale",
            },
            "domain": [("id", "in", self.invoice_ids.ids)]
        }

    def unlink(self):
        invoices = self.mapped("invoice_ids").filtered(lambda i: i.payment_state != "paid")
        invoices.button_draft()
        invoices.button_cancel()
        return super(AccountStatement, self).unlink()

    def button_reopen(self):
        self.invoice_ids.filtered(lambda i: i.payment_state != "paid").button_draft()
        return super().button_reopen()

    def button_post(self):
        self.invoice_ids.filtered(lambda i: i.state == "draft").action_post()
        return super().button_post()

    def auto_reconcile(self):
        """ Auto reconcile matching invoices through jobs to avoid timeouts """
        if self.env.context.get('async_mode', True):
            self.with_company(self.journal_id.company_id.id).with_delay()._auto_reconcile()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Auto reconcile',
                    'type': 'success',
                    'message': 'Reconciliation job has been queued',
                    'sticky': False,
                }
            }
        else:
            self._auto_reconcile()

    def _auto_reconcile(self):
        """ Inspired by the `if model.auto_reconcile` part of _apply_rules() """
        reconcile_model = self.env["account.reconcile.model"].search([
            ("rule_type", "!=", "writeoff_button"),
            "|", ("company_id", "=", self.journal_id.company_id.id),
            ("company_id", "=", False)
        ], limit=1)

        for bank_statement in self.filtered("line_ids"):
            reconcile_model = reconcile_model.with_context({
                "bank_statement_date": bank_statement.date
            })
            matching_amls = reconcile_model._apply_rules(bank_statement.line_ids)

            for line_id, result in matching_amls.items():
               self.with_delay()._reconcile_single_line(line_id, result, bank_statement, reconcile_model)

    def _reconcile_single_line(self, line_id, result, bank_statement, reconcile_model):
        """Reconcile method to run it as a job"""
        if result["aml_ids"]:
            line = bank_statement.line_ids.browse(line_id)
            move_lines = self.env["account.move.line"].browse(result["aml_ids"])
            # Check that line wasn't already reconciled

            move_lines = move_lines.filtered(lambda a: not a.reconciled)
            reconcile = reconcile_model._prepare_reconciliation(
                line, move_lines.ids)

            # An open balance is needed but no partner has been found.
            # if reconcile['open_balance_dict'] is False:
            #     continue

            # new_aml_dicts = reconcile['new_aml_dicts']
            # if reconcile['open_balance_dict']:
            #     new_aml_dicts.append(reconcile['open_balance_dict'])
            #
            line.with_context({"default_journal_id": None}).reconcile(reconcile)
            # line.process_reconciliation(
            #     counterpart_aml_dicts=reconcile['counterpart_aml_dicts'],
            #     payment_aml_rec=reconcile['payment_aml_rec'],
            #     new_aml_dicts=new_aml_dicts,
            # )
