##############################################################################
#
#    Copyright (C) 2014-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, exceptions, _


class MoveLine(models.Model):
    """ Adds a method to split a payment into several move_lines
    in order to reconcile only a partial amount, avoiding doing
    partial reconciliation. """

    _inherit = "account.move.line"

    def split_payment_and_reconcile(self):
        sum_credit = sum(self.mapped("credit"))
        sum_debit = sum(self.mapped("debit"))
        if sum_credit == sum_debit:
            # Nothing to do here
            return self.reconcile()

        # Check in which direction we are reconciling
        split_column = "credit" if sum_credit > sum_debit else "debit"
        difference = abs(sum_credit - sum_debit)

        for line in self:
            if getattr(line, split_column) > difference:
                # We will split this line
                move = line.move_id
                move_line = line
                break
        else:
            raise exceptions.UserError(
                _(
                    "This can only be done if one move line can be split "
                    "to cover the reconcile difference"
                )
            )

        # Edit move in order to split payment into two move lines
        move.button_cancel()
        move.write(
            {
                "line_ids": [
                    (1, move_line.id, {split_column: move_line.credit - difference}),
                    (
                        0,
                        0,
                        {
                            split_column: difference,
                            "name": self.env.context.get(
                                "residual_comment", move_line.name
                            ),
                            "account_id": move_line.account_id.id,
                            "date": move_line.date,
                            "date_maturity": move_line.date_maturity,
                            "journal_id": move_line.journal_id.id,
                            "partner_id": move_line.partner_id.id,
                        },
                    ),
                ]
            }
        )
        move.post()

        # Perform the reconciliation
        return self.reconcile()
