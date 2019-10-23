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
    @api.onchange('printing_printer_id')
    def on_change_printer(self):
        for report in self:
            report.printer_options = False
