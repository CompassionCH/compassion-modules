##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class ReconcileSplitPaymentWizard(models.TransientModel):
    """Wizard that helps the user doing a full reconciliation when a customer
    paid more than excepted. It splits the payment into two move lines so
    that one invoice can be reconciled and the extra amount is kept in
    the customer balance. """

    _name = "reconcile.split.payment.wizard"
    _description = "Wizard reconcile split payment"

    comment = fields.Char("Indications on left amount", size=64)
    contract_ids = fields.Many2many(
        "recurring.contract",
        default=lambda self: self._get_contract_ids(),
        string="Related contracts",
        readonly=False,
    )

    def _get_contract_ids(self):
        move_line_obj = self.env["account.move.line"]
        contract_ids = False
        active_ids = self.env.context.get("active_ids")
        if active_ids:
            contract_ids = (
                move_line_obj.browse(active_ids)
                .filtered(lambda mvl: mvl.debit > 0)
                .mapped("move_id.invoice_line_ids.contract_id.id")
                or False
            )
        return contract_ids

    def reconcile_split_payment(self):
        """ Split the payment of a partner into two move_lines in order to
        reconcile one of them.
        """
        self.ensure_one()
        move_line_obj = self.env["account.move.line"].with_context(
            residual_comment=self.comment
        )
        move_lines = move_line_obj.browse(self.env.context.get("active_ids"))
        return move_lines.split_payment_and_reconcile()
