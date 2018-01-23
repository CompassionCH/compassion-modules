# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Marco Monzione
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class InvoicerWizard(models.TransientModel):

    _inherit = 'recurring.invoicer.wizard'

    @api.multi
    def generate(self):
        return super(InvoicerWizard, self.with_context(lsv=True)).generate()
