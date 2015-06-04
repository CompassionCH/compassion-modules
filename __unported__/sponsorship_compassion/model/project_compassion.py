# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models


class project_compassion(models.Model):
    _inherit = 'compassion.project'

    @api.one
    def suspend_funds(self):
        """ When a project is suspended, We update all contracts of
        sponsored children in the project, so that we don't create invoices
        during the period of suspension.
        We also remove the children on internet.
        """
        res = super(project_compassion, self).suspend_funds()
        contracts = self.env['recurring.contract'].search([
            ('child_code', 'like', self.code),
            ('state', 'in', ('active', 'waiting', 'mandate'))])
        res = res and contracts.suspend_contract()

        return res

    @api.one
    def _reactivate_project(self):
        """ When project is reactivated, we re-open cancelled invoices,
        or we change open invoices if fund is set to replace sponsorship
        product. We also change attribution of invoices paid in advance.
        """
        res = super(project_compassion, self)._reactivate_project()
        contracts = self.env['recurring.contract'].search([
            ('child_code', 'like', self.code),
            ('state', 'in', ('active', 'waiting', 'mandate'))])

        return res and contracts.reactivate_contract()
