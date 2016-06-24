# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import models, fields


class ProjectLifecycle(models.Model):
    _name = 'compassion.project.ile'
    _description = 'Project lifecycle event'
    _order = 'date desc'

    project_id = fields.Many2one(
        'compassion.project', required=True, ondelete='cascade', readonly=True)
    date = fields.Date(readonly=True)
    type = fields.Selection([
        ('Suspension', 'Suspension'),
        ('Reactivation', 'Reactivation'),
        ('Transition', 'Transition'),
    ], readonly=True)
    reason = fields.Char(readonly=True)
    details = fields.Text(readonly=True)
    action_plan = fields.Text(readonly=True)

    # Reactivation
    ##############
    icp_improvement_desc = fields.Text(readonly=True)

    # Suspension
    ############
    suspension_start_date = fields.Date(readonly=True)
    suspension_end_date = fields.Date(readonly=True)

    hold_cdsp_funds = fields.Boolean(readonly=True)
    hold_csp_funds = fields.Boolean(readonly=True)
    hold_gifts = fields.Boolean(readonly=True)
    hold_s2b_letters = fields.Boolean(readonly=True)
    hold_b2s_letters = fields.Boolean(readonly=True)
    hold_child_updates = fields.Boolean(readonly=True)

    extension_1 = fields.Boolean(
        help='Suspension is extended by 30 days', readonly=True)
    extension_1_reason = fields.Text(readonly=True)
    extension_2 = fields.Boolean(
        help='Suspension is extended by additional 30 days (60 in total)',
        readonly=True)
    extension_2_reason = fields.Text(readonly=True)

    # Transition
    ############
    actual_transition_date = fields.Date(readonly=True)
    transition_complete = fields.Boolean(readonly=True)
    future_involvement = fields.Char(readonly=True)
    celebration_details = fields.Char(readonly=True)
    relationship_strengths = fields.Char(readonly=True)
