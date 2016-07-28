# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import api, models, fields, _


class ICPDisasterImpact(models.Model):
    _name = 'icp.disaster.impact'
    _description = 'ICP Disaster Impact'

    project_id = fields.Many2one(
        'compassion.project', 'Project', ondelete='cascade'
    )
    fo_disaster_alert_id = fields.Many2one(
        'fo.disaster.alert', 'Disaster Alert', ondelete='cascade'
    )

    impact_on_icp_program = fields.Char()
    disaster_impact_description = fields.Char()
    disaster_status = fields.Char()
    infrastructure = fields.Char()


class FieldOfficeDisasterUpdate(models.Model):
    _name = 'fo.disaster.update'
    _description = 'Field Office Disaster Update'

    fo_disaster_alert_id = fields.Many2one(
        'fo.disaster.alert', 'Disaster Alert', ondelete='cascade'
    )
    fo_id = fields.Many2one(
        'compassion.field.office', 'Field Office'
    )

    fodu_id = fields.Integer()
    name = fields.Char()
    summary = fields.Char()


class ChildDisasterImpact(models.Model):
    _name = 'child.disaster.impact'
    _description = 'Child Disaster Impact'

    child_id = fields.Many2one(
        'compassion.child', 'Child', ondelete='cascade'
    )
    fo_disaster_alert_id = fields.Many2one(
        'fo.disaster.alert', 'Disaster Alert', ondelete='cascade'
    )

    name = fields.Char()
    beneficiary_location = fields.Char()
    beneficiary_physical_condition = fields.Char()
    beneficiary_physical_condition_description = fields.Char()
    caregivers_died_number = fields.Integer()
    caregivers_seriously_injured_number = fields.Integer()
    disaster_status = fields.Char()
    house_condition = fields.Char()
    lost_personal_effects = fields.Selection([
        ('Lost School Supplies', 'Lost School Supplies'),
        ('Lost Clothing', 'Lost Clothing'),
        ('Lost Household Items', 'Lost Household Items')
    ])
    siblings_died_number = fields.Integer()
    siblings_seriously_injured_number = fields.Integer()
    sponsorship_status = fields.Char()

    @api.model
    def create(self, vals):
        """ Log a note in child when new disaster impact is registered. """
        impact = super(ChildDisasterImpact, self).create(vals)
        impact.child_id.message_post(
            "Child was affected by the natural disaster {}".format(
                impact.fo_disaster_alert_id.disaster_name),
            "Disaster Alert"
        )
        return impact


class FieldOfficeDisasterAlert(models.Model):
    _name = 'fo.disaster.alert'
    _description = 'FO disaster alert'
    _rec_name = 'disaster_name'

    disaster_id = fields.Char()
    area_description = fields.Char()
    close_date = fields.Date()

    disaster_name = fields.Char()
    disaster_date = fields.Datetime()
    disaster_status = fields.Char()
    disaster_type = fields.Char()

    estimated_basic_supplies_needed = fields.Char()
    estimated_homes_destroyed = fields.Char()
    estimated_loss_of_life = fields.Char()
    estimated_loss_of_livelihood = fields.Char()
    estimated_not_attending_project = fields.Char()
    estimated_rehabilitation_funds_usd = fields.Integer()
    estimated_relief_funds_usd = fields.Integer()
    estimated_serious_injuries = fields.Char()

    field_office_id = fields.Many2one(
        'compassion.field.office', string="Field Offices", ondelete='cascade'
    )
    field_office_damage = fields.Char()
    field_office_impact_description = fields.Char()

    impact_description = fields.Char()
    impact_on_icp_infrastructure_damaged = fields.Integer()
    impact_on_icp_infrastructure_destroyed = fields.Integer()
    impact_on_icp_program_temporarily_closed = fields.Integer()
    impact_to_field_office_operations = fields.Char()

    is_additional_funds_requested = fields.Boolean()
    is_communication_sensitive = fields.Boolean()
    is_estimated_damage_over_one_million_usd = fields.Boolean()

    reported_loss_of_life_beneficiaries = fields.Integer()
    reported_loss_of_life_caregivers = fields.Integer()
    reported_loss_of_life_siblings = fields.Integer()
    reported_number_beneficiaries_impacted = fields.Integer()
    reported_number_of_icps_impacted = fields.Integer()
    reported_serious_injuries_beneficaries = fields.Integer()
    reported_serious_injuries_caregivers = fields.Integer()
    reported_serious_injuries_siblings = fields.Integer()
    response_description = fields.Char()

    severity_level = fields.Char()
    source_kit_name = fields.Char()

    icp_disaster_impact_ids = fields.One2many(
        'icp.disaster.impact', 'fo_disaster_alert_id', 'ICP Disaster Impact'
    )
    fo_disaster_update_ids = fields.One2many(
        'fo.disaster.update', 'fo_disaster_alert_id', 'Field Office Update'
    )
    child_disaster_impact_ids = fields.One2many(
        'child.disaster.impact', 'fo_disaster_alert_id', 'Child Disaster '
                                                         'Impact'
    )

    @api.multi
    def view_children(self):
        return {
            'name': _('Impacted children'),
            'domain': [('id', 'in', self.child_disaster_impact_ids.mapped(
                        'child_id').ids)],
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'compassion.child',
            'target': 'current',
        }

    @api.multi
    def view_icp(self):
        return {
            'name': _('Impacted projects'),
            'domain': [('id', 'in', self.icp_disaster_impact_ids.mapped(
                'project_id').ids)],
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'compassion.project',
            'target': 'current',
        }
