# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models


class compassion_project(models.Model):
    """ Update Contracts Project Workflow when Suspension status
        is changed.
    """
    _inherit = 'compassion.project'

    @api.multi
    def suspend_funds(self):
        super(compassion_project, self).suspend_funds()
        return self._transition_contracts('project_suspended')

    @api.multi
    def _reactivate_project(self):
        super(compassion_project, self)._reactivate_project()
        return self._transition_contracts('project_reactivation')

    def _suspend_extension(self):
        super(compassion_project, self)._suspend_extension()
        contracts = self.env['recurring.contract'].search([
            ('project_id', 'in', self.ids),
            ('project_state', '=', 'fund-suspended')])
        return contracts.write({'project_state': 'inform_extension'})

    def _transition_contracts(self, transition):
        contracts = self.env['recurring.contract'].search([
            ('project_id', 'in', self.ids)])
        return contracts.trg_validate(transition)
