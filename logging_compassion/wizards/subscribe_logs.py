# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from odoo import api, models


class SubscribeLogs(models.TransientModel):
    _name = 'auditlog.subscriber'

    @api.model
    def subscribe_rules(self):
        xml_data = self.env['ir.model.data'].search([
            ('module', '=', 'logging_compassion'),
            ('model', '=', 'auditlog.rule')])
        rules = self.env['auditlog.rule'].browse(xml_data.mapped('res_id'))
        rules.subscribe()
