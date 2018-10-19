# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>, Philippe Heer
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import models, fields, api
from odoo.addons.message_center_compassion.mappings \
    import base_mapping as mapping


class ProjectLifecycle(models.Model):
    _name = 'compassion.project.ile'
    _inherit = 'translatable.model'
    _description = 'Project lifecycle event'
    _order = 'date desc, id desc'

    project_id = fields.Many2one(
        'compassion.project', required=True, ondelete='cascade',
        readonly=True)
    date = fields.Date(readonly=True, default=fields.Date.today)
    type = fields.Selection('_get_type', readonly=True)
    action_plan = fields.Text(readonly=True)

    # Reactivation
    ##############
    icp_improvement_desc = fields.Text(readonly=True)

    # Suspension
    ############
    suspension_start_date = fields.Date(readonly=True)
    suspension_end_date = fields.Date(readonly=True)
    suspension_detail = fields.Char(readonly=True)
    suspension_reason_ids = fields.Many2many(
        'icp.lifecycle.reason', string='Suspension reason', readonly=True)

    hold_cdsp_funds = fields.Boolean(readonly=True)
    hold_csp_funds = fields.Boolean(readonly=True)
    hold_gifts = fields.Boolean(readonly=True)
    hold_s2b_letters = fields.Boolean(readonly=True)
    hold_b2s_letters = fields.Boolean(readonly=True)
    hold_child_updates = fields.Boolean(readonly=True)
    is_beneficiary_information_updates_withheld = fields.Boolean(
        readonly=True)

    extension_1 = fields.Boolean(
        help='Suspension is extended by 30 days', readonly=True)
    extension_1_reason_ids = fields.Many2many(
        'icp.suspension.extension.reason', readonly=True)
    extension_2 = fields.Boolean(
        help='Suspension is extended by additional 30 days (60 in total)',
        readonly=True)
    extension_2_reason_ids = fields.Many2many(
        'icp.suspension.extension.reason', readonly=True)

    # Transition
    ############
    transition_date = fields.Date(readonly=True)
    transition_complete = fields.Boolean(readonly=True)
    details = fields.Text(readonly=True)
    transition_reason_ids = fields.Many2many(
        'icp.lifecycle.reason', string='Transition reason', readonly=True,
        relation='compassion_project_ile_transition_reason_rel')
    projected_transition_date = fields.Date(readonly=True)
    future_involvement_ids = fields.Many2many(
        'icp.involvement', string='Future involvement', readonly=True)

    name = fields.Char(readonly=True, index=True, required=True)
    reactivation_date = fields.Date(readonly=True)
    project_status = fields.Selection(related='project_id.status')

    gender = fields.Char(size=1, default='M')

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Lifecycle event already exists')
    ]

    @api.model
    def _get_type(self):
        return [
            ('Suspension', 'Suspension'),
            ('Reactivation', 'Reactivation'),
            ('Transition', 'Transition'),
        ]

    @api.model
    def _get_project_status(self):
        return [
            ('Active', 'Active'),
            ('Phase Out', 'Phase Out'),
            ('Suspended', 'Suspended'),
            ('Transitioned', 'Transitioned'),
        ]

    @api.model
    def create(self, vals):
        """ Call suspension and reactivation process on projects. """
        project = self.env['compassion.project'].browse(
            vals.get('project_id'))
        fund_suspended = project.suspension == 'fund-suspended'
        hold_gifts = project.hold_gifts
        hold_letters = project.hold_s2b_letters
        lifecycle = self.search([('name', '=', vals['name'])])
        if lifecycle:
            lifecycle.write(vals)
        else:
            lifecycle = super(ProjectLifecycle, self).create(vals)
        if lifecycle.type == 'Suspension':
            if lifecycle.hold_cdsp_funds and not fund_suspended:
                project.suspend_funds()
            if lifecycle.hold_gifts and not hold_gifts:
                project.hold_gifts_action()
            if lifecycle.hold_s2b_letters and not hold_letters:
                project.hold_letters_action()
        if lifecycle.type == 'Reactivation':
            if fund_suspended:
                project.reactivate_project()
            if hold_gifts and not lifecycle.hold_gifts:
                project.reactivate_gifts()
            if hold_letters and not lifecycle.hold_s2b_letters:
                project.reactivate_letters()
        return lifecycle

    @api.model
    def process_commkit(self, commkit_data):
        project_mapping = mapping.new_onramp_mapping(
            self._name,
            self.env,
            'new_project_lifecyle')

        lifecycle_ids = list()
        for single_data in commkit_data.get('ICPLifecycleEventList',
                                            [commkit_data]):
            project = self.env['compassion.project'].search([
                ('icp_id', '=', single_data['ICP_ID'])
            ])
            if not project:
                project.create({'icp_id': single_data['ICP_ID']})
            vals = project_mapping.get_vals_from_connect(single_data)
            lifecycle = self.create(vals)
            lifecycle_ids.append(lifecycle.id)

            lifecycle.project_id.status = vals['project_status']
            lifecycle.project_id.last_update_date = fields.Date.today()

        return lifecycle_ids
