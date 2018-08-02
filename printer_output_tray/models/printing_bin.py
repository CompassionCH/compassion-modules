# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class PrinterBin(models.Model):
    _name = 'printing.bin'
    _description = 'Printer Bin'

    name = fields.Char(required=True)
    system_name = fields.Char(required=True, readonly=True)
    lang_forwarded_ids = fields.Many2many('res.lang', string="Languages")
    printer_id = fields.Many2one(
        comodel_name='printing.printer',
        string='Printer',
        required=True,
        readonly=True,
        ondelete='cascade',
    )

    def forward_lang(self, lang):
        bins_for_lang = self.lang_forwarded_ids \
            .filtered(lambda lang_forwarded: lang in lang_forwarded.code)
        return len(bins_for_lang) > 0
