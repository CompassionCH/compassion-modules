# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, fields, models


class IrActionsReportXml(models.Model):
    _inherit = 'ir.actions.report.xml'

    printer_options = fields.Many2many('printer.option.choice',
                                       string='Printer Options')

    @api.multi
    def write(self, vals):
        if 'printing_printer_id' in vals:
            # The options are printer-dependent and must be cleared.
            vals['printer_options'] = [(5, 0, 0)]
        return super(IrActionsReportXml, self).write(vals)
