# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class ProjectCompassion(models.Model):
    _inherit = 'compassion.project'

    sponsorships_count = fields.Integer(compute='_compute_sponsorships_count')

    def _compute_sponsorships_count(self):

        for project in self:
            project.sponsorships_count = self.env['recurring.contract'].\
                search_count([('child_id.project_id', '=', project.id)])

    @api.multi
    def open_sponsorships(self):

        contract_list = self.env['recurring.contract'].search([
            ('child_id.project_id', '=', self.id)])

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sponsorships',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'recurring.contract',
            'domain': [('id', 'in', contract_list.ids)],
            'target': 'current',
            'context': self.env.context
        }

    @api.multi
    def suspend_funds(self):
        """ When a project is suspended, We update all contracts of
        sponsored children in the project, so that we don't create invoices
        during the period of suspension.
        We also remove the children on internet.
        """
        res = super(ProjectCompassion, self).suspend_funds()
        contracts = self.env['recurring.contract']
        for project in self:
            contracts |= self.env['recurring.contract'].search([
                ('child_code', 'like', project.fcp_id),
                ('state', 'in', ('active', 'waiting', 'mandate'))])
        res = res and contracts.suspend_contract()

        return res

    @api.multi
    def reactivate_project(self):
        """ When project is reactivated, we re-open cancelled invoices,
        or we change open invoices if fund is set to replace sponsorship
        product. We also change attribution of invoices paid in advance.
        """
        res = super(ProjectCompassion, self).reactivate_project()
        contracts = self.env['recurring.contract']
        for project in self:
            contracts |= self.env['recurring.contract'].search([
                ('child_code', 'like', project.fcp_id),
                ('state', 'in', ('active', 'waiting', 'mandate'))])
        contracts.reactivate_contract()
        return res

    def hold_gifts_action(self):
        contracts = self.env['recurring.contract'].search([
            ('child_code', 'like', self.fcp_id),
            ('state', 'in', ('active', 'waiting', 'mandate'))])
        contracts.hold_gifts()

    def reactivate_gifts(self):
        contracts = self.env['recurring.contract'].search([
            ('child_code', 'like', self.fcp_id),
            ('state', 'in', ('active', 'waiting', 'mandate'))])
        contracts.reactivate_gifts()
