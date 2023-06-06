##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez <sgonzalez@ikmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models, api


class RecurringContract(models.Model):
    _inherit = ["recurring.contract"]

    type = fields.Selection(selection_add=[('CSP', 'Survival Sponsorship')])

    @api.multi
    def invoice_paid(self, invoice):
        super().invoice_paid()
        self.filtered(lambda c: c.type == 'CSP').contract_active()
