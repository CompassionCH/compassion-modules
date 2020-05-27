##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields, _


class Partner(models.Model):
    _inherit = "crm.phonecall"

    is_from_employee = fields.Boolean(default=False)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if "origin" in self._context and \
                self._context.get('origin') == 'employee':
            res.is_from_employee = True
        return res
