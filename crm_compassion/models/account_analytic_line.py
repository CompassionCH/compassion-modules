# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class AnalyticAccount(models.Model):
    """ Add year in name of analytic accounts. """
    _inherit = 'account.analytic.account'

    year = fields.Char()

    @api.multi
    def name_get(self):
        res = []
        for analytic in self:
            name = analytic.name
            if analytic.code:
                name = '[' + analytic.code + '] ' + name
            if analytic.year and not name.endswith(analytic.year):
                name = name + ' ' + analytic.year
            res.append((analytic.id, name))
        return res


class AnalyticLine(models.Model):
    """ Triggers for computation on event lines. """
    _inherit = 'account.analytic.line'

    @api.model
    def create(self, vals):
        line = super(AnalyticLine, self).create(vals)
        line.onchange_line()
        return line

    @api.multi
    def unlink(self):
        events = self.env['crm.event.compassion'].search([
            ('analytic_id', 'in', self.mapped('account_id').ids)
        ])
        super(AnalyticLine, self).unlink()
        events.update_analytics()
        return True

    @api.multi
    def write(self, vals):
        super(AnalyticLine, self).write(vals)
        self.onchange_line()
        return True

    @api.multi
    def onchange_line(self):
        events = self.env['crm.event.compassion'].search([
            ('analytic_id', 'in', self.mapped('account_id').ids)
        ])
        events.update_analytics()
