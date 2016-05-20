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


class ProjectNeed(models.Model):
    _name = 'compassion.project.ile'
    _description = 'Project lifecycle event'
    _order = 'date desc'

    project_id = fields.Many2one(
        'compassion.project', required=True, ondelete='cascade')
    date = fields.Date()
    type = fields.Selection([
        ('Reactivation', 'Reactivation'),
        ('Suspension', 'Suspension'),
        ('Transition', 'Transition'),
    ])
    reason = fields.Char()
    details = fields.Text()
    action_plan = fields.Text()

    # Reactivation
    ##############
    icp_improvement_desc = fields.Text()

    # Suspension
    ############
    suspension_start_date = fields.Date()
    suspension_end_date = fields.Date()

    hold_cdsp_funds = fields.Boolean()
    hold_csp_funds = fields.Boolean()
    hold_gifts = fields.Boolean()
    hold_s2b_letters = fields.Boolean()
    hold_b2s_letters = fields.Boolean()
    hold_child_updates = fields.Boolean()

    extension_1 = fields.Boolean(help='Suspension is extended by 30 days')
    extension_1_reason = fields.Text()
    extension_2 = fields.Boolean(
        help='Suspension is extended by additional 30 days (60 in total)')
    extension_2_reason = fields.Text()

    # Transition
    ############
    actual_transition_date = fields.Date()
    transition_complete = fields.Boolean()
    future_involvement = fields.Char()
    celebration_details = fields.Char()
    relationship_strengths = fields.Char()
