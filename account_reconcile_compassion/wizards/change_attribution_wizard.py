##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields, exceptions, _


class ChangeAttributionWizard(models.TransientModel):
    """
    self that helps the user doing changing the attribution of a payment,
    by automatically un-reconciling related move lines, cancelling
    related invoices and proposing modification of those invoices for a
    new attribution of the payment.
    """

    _name = "unreconcile.change.attribution.wizard"
    _description = "Wizard unreconcile change attribution"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    invoice_line_ids = fields.Many2many(
        "account.move.line",
        "change_attribution_wizard_line_rel",
        string="Related invoice lines",
        default=lambda self: self._get_invoice_lines(),
        readonly=True,
    )
    comment = fields.Text("Comment", help="Explain why you changed the attribution.")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_invoice_lines(self):
        """Returns the invoice line ids that can be updated.
        Context can either hold invoice ids or move line ids
        depending from where the user called the self.
        """
        active_ids = self.env.context.get("active_ids")
        model = self.env.context.get("active_model")
        invoices = self.env["account.move"]

        if model == "account.move.line":
            invoices = self._get_invoices_from_mvl_ids(active_ids)
        elif model == "account.invoice":
            invoices = invoices.browse(active_ids)

        return invoices.mapped("invoice_line_ids.id")

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def unreconcile(self):
        """ Unreconcile selected payments. """
        self.ensure_one()
        if not self.invoice_line_ids:
            raise exceptions.UserError(
                _(
                    "I couldn't find any invoice to modify. Please verify "
                    "your selection."
                )
            )

        # Unreconcile payments
        payment_ids = self.invoice_line_ids.mapped("move_id.")
        move_lines = payment_ids.mapped("full_reconcile_id.reconciled_line_ids")
        move_lines.remove_move_reconcile()

        # Cancel paid invoices and move invoice lines to a new
        # draft invoice.
        new_invoice = False
        invoice_ids = list()
        for invoice_line in self.invoice_line_ids:
            invoice = invoice_line.invoice_id
            if invoice.id not in invoice_ids:
                invoice_ids.append(invoice.id)
                if not new_invoice:
                    # We copy the first invoice to create a new one holding
                    # all modifications. The other invoices will be cancelled.
                    new_invoice = invoice.copy(
                        {
                            "date_invoice": invoice.date_invoice,
                            "comment": self.comment
                            or "New invoice after payment attribution changed.",
                            "invoice_line_ids": False,
                        }
                    )

                invoice.action_invoice_cancel()
                invoice.write(
                    {"comment": self.comment or "Payment attribution changed."}
                )
                for line in invoice.invoice_line_ids:
                    line.copy({"invoice_id": new_invoice.id})

        self = self.with_context(payment_ids=payment_ids.ids)
        new_invoice.to_reconcile = sum(payment_ids.mapped("credit"))

        return {
            "name": _("Change attribution"),
            "type": "ir.actions.act_window",
            "res_model": "account.invoice",
            "res_id": new_invoice.id,
            "view_mode": "form",
            "view_type": "form",
            "view_id": self.env.ref("account.invoice_form").id,
            "context": self.env.context,
        }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_invoices_from_mvl_ids(self, mvl_ids):
        mvl_obj = self.env["account.move.line"]
        invoice_obj = self.env["account.invoice"]
        move_lines = mvl_obj.browse(mvl_ids).filtered(lambda mvl: mvl.credit > 0)
        reconcile_ids = move_lines.mapped("full_reconcile_id.id")
        # Find related reconciled invoices
        invoices = invoice_obj.search(
            [
                ("move_id.line_id.full_reconcile_id", "in", reconcile_ids),
                ("state", "=", "paid"),
                ("residual", "=", 0.0),
            ]
        )
        return invoices


class AccountInvoice(models.Model):
    _inherit = "account.move"

    to_reconcile = fields.Float()

    def change_attribution(self):
        self.ensure_one()
        move_line_obj = self.env["account.move.line"]
        if self.amount_total != self.to_reconcile:
            raise exceptions.UserError(
                _(
                    "The invoice total amount should be equal to %s in order to"
                    " be reconciled against the payment."
                )
                % self.to_reconcile
            )

        self.action_invoice_open()

        # Reconcile all related move lines
        mvl_ids = self.env.context.get("payment_ids")
        if mvl_ids:
            move_lines = move_line_obj.search(
                [
                    ("move_id", "=", self.move_id.id),
                    ("account_id", "=", self.account_id.id),
                ]
            )
            move_lines |= move_line_obj.browse(mvl_ids)
            move_lines.reconcile("manual")
        self.to_reconcile = 0.0
        return True
