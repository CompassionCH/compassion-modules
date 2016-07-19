# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#             Philippe Heer <heerphilippe@msn.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import models, fields, api
from openerp.addons.message_center_compassion.mappings \
    import base_mapping as mapping


class ProjectLifecycle(models.Model):
    _name = 'compassion.project.ile'
    _description = 'Project lifecycle event'
    _order = 'date desc'

    project_id = fields.Many2one(
        'compassion.project', required=True, ondelete='cascade',
        readonly=True)
    date = fields.Date(readonly=True, default=fields.Date.today())
    type = fields.Selection([
        ('Suspension', 'Suspension'),
        ('Reactivation', 'Reactivation'),
        ('Transition', 'Transition'),
    ], readonly=True)
    # reason = fields.Char(readonly=True)
    action_plan = fields.Text(readonly=True)

    # Reactivation
    ##############
    icp_improvement_desc = fields.Text(readonly=True)

    # Suspension
    ############
    suspension_start_date = fields.Date(readonly=True)
    suspension_end_date = fields.Date(readonly=True)
    suspension_detail = fields.Char(readonly=True)
    suspension_reason = fields.Selection([
        ('Child Protection Issue', 'Child Protection Issue'),
        ('Disaster event', 'Disaster event'),
        ('Does not comply with policies', 'Does not comply with policies'),
        ('Financial Mismanagement', 'Financial Mismanagement'),
        ('Other', 'Other'),
    ], readonly=True)

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
    extension_1_reason = fields.Text(readonly=True)
    extension_2 = fields.Boolean(
        help='Suspension is extended by additional 30 days (60 in total)',
        readonly=True)
    extension_2_reason = fields.Text(readonly=True)

    # Transition
    ############
    transition_date = fields.Date(readonly=True)
    transition_complete = fields.Boolean(readonly=True)
    details = fields.Text(readonly=True)
    reason = fields.Selection([
        ('Child Protection Issue', 'Child Protection Issue'),
        ('Disaster Event', 'Disaster Event'),
        ('Does not comply with policies', 'Does not comply with policies'),
        ('Financial Mismanagement', 'Financial Mismanagement'),
        ('Other', 'Other'),
        ('Successful Transition', 'Successful Transition'),
    ], readonly=True)
    projected_transition_date = fields.Date(readonly=True)
    future_involvement = fields.Selection([
        ('Advocacy', 'Advocacy'),
        ('Alumni', 'Alumni'),
        ('Church Mobilization', 'Church Mobilization'),
        ('Leveraged', 'Leveraged'),
        ('Mentoring', 'Mentoring'),
        ('No Future Engagement', 'No Future Engagement'),
        ('Training', 'Training'),
    ], readonly=True)
    # celebration_details = fields.Char(readonly=True)
    # relationship_strengths = fields.Char(readonly=True)

    # Translation
    ############
    translation_completed_fields = fields.Selection([
        ('Action Plan', 'Action Plan'),
        ('Suspension Details', 'Suspension Details'),
        ('Transition Details', 'Transition Details'),
    ], readonly=True)
    translation_required_fields = fields.Selection([
        ('Action Plan', 'Action Plan'),
        ('Suspension Details', 'Suspension Details'),
        ('Transition Details', 'Transition Details'),
    ], readonly=True)
    translation_status = fields.Selection([
        ('Draft', 'Draft'),
        ('Ready For Translation', 'Ready For Translation'),
        ('Translation Complete', 'Translation Complete'),
    ], readonly=True)

    name = fields.Char(readonly=True)
    reactivation_date = fields.Date(readonly=True)
    project_status = fields.Selection([
        ('Active', 'Active'),
        ('Phase Out', 'Phase Out'),
        ('Suspended', 'Suspended'),
        ('Transitioned', 'Transitioned'),
    ], readonly=True)

    @api.model
    def process_commkit(self, commkit_data):
        project_mapping = mapping.new_onramp_mapping(
            self._name,
            self.env,
            'new_project_lifecyle')

        vals = project_mapping.get_vals_from_connect(commkit_data)
        project = self.with_context(no_comm_kit=True).create(vals)

        return [project.id]
