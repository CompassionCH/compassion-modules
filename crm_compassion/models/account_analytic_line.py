# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models


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
