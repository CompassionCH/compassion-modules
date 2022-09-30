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

from odoo import api, fields, models


class AccountStatement(models.Model):
    """ Adds a relation to a recurring invoicer. """

    _name = "account.bank.statement"
    _inherit = ["account.bank.statement", "mail.thread"]

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(default=lambda b: b._default_name())
    invoice_ids = fields.Many2many(
        "account.move",
        string="Invoices",
        compute="_compute_invoices",
        readonly=False,
    )
    generated_invoices_count = fields.Integer("Invoices", compute="_compute_invoices")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _default_name(self):
        """ Find the appropriate sequence """
        journal_id = self.env.context.get("default_journal_id")
        if journal_id:
            journal = self.env["account.journal"].browse(journal_id)
            sequence = self.env["ir.sequence"].search([("name", "=", journal.name)])
            if sequence:
                return sequence.next_by_id()
        return ""

    def _compute_invoices(self):
        invoice_obj = self.env["account.move"]
        for stmt in self:
            invoices = invoice_obj.search([("name", "=", stmt.name)])
            stmt.invoice_ids = invoices
            stmt.generated_invoices_count = len(invoices)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    def to_invoices(self):
        self.ensure_one()
        return {
            "name": "Generated Invoices",
            "view_mode": "tree,form",
            "view_type": "form",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "target": "current",
            "context": {
                "form_view_ref": "account.invoice_form",
                "journal_type": "sale",
            },
        }

    def unlink(self):
        # self.mapped("invoice_ids").filtered(
        #     lambda i: i.state in ("draft", "open")
        # ).action_invoice_cancel()
        return super(AccountStatement, self).unlink()

    def auto_reconcile(self):
        """ Auto reconcile matching invoices through jobs to avoid timeouts
        Inspired by the `if model.auto_reconcile` part of _apply_rules()"""
        reconcile_model = self.env["account.reconcile.model"].search(
            [("rule_type", "!=", "writeoff_button")]
        )

        for bank_statement in self.filtered("line_ids"):
            matching_amls = reconcile_model._apply_rules(bank_statement.line_ids)

            for line_id, result in matching_amls.items():
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
                    line.reconcile(reconcile)
                    # line.process_reconciliation(
                    #     counterpart_aml_dicts=reconcile['counterpart_aml_dicts'],
                    #     payment_aml_rec=reconcile['payment_aml_rec'],
                    #     new_aml_dicts=new_aml_dicts,
                    # )
