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


from openerp import api, models, fields


class FieldOffice(models.Model):
    _name = 'compassion.field.office'

    name = fields.Char('Name')
    field_office_id = fields.Char(required=True)
    project_ids = fields.One2many(
        'compassion.project', 'field_office_id', 'Compassion projects')
    region = fields.Char()
    country_director = fields.Char()
    date_start = fields.Date('Field office start')
    issue_email = fields.Char()
    phone_number = fields.Char()
    website = fields.Char()
    social_media_site = fields.Char()
    country = fields.Char()
    country_id = fields.Many2one('res.country', 'Country',
                                 compute='_compute_country')
    country_code = fields.Char(related='country_id.code')
    street = fields.Char()
    city = fields.Char()
    province = fields.Char()
    zip_code = fields.Char()

    primary_language_id = fields.Many2one('res.lang.compassion', 'Primary '
                                                                 'language')
    spoken_language_ids = fields.Many2many('res.lang.compassion',
                                           string='Spoken languages')
    translated_language_ids = fields.Many2many('res.lang.compassion',
                                               string='Translated languages')

    staff_number = fields.Integer()
    country_information = fields.Char()
    high_risk_ids = fields.Many2many(
        'fo.high.risk', string='Beneficiary high risks'
    )

    development_plan_frequency = fields.Integer(
        help='Frequency in months at which the FO makes a development plan'
    )
    cdpr_frequency = fields.Integer(
        help='Frequency in months at which the FO makes Child Development '
             'Progress Reports'
    )
    baby_health_assessment_frequency = fields.Integer(
        help='Frequency in months at which the FO makes Health Assessments '
             'for babies (0-1)'
    )
    health_assessment_frequency = fields.Integer(
        help='Frequency for Health Assessments of children (2+)'
    )
    transition_age = fields.Integer(
        help='Age at which children transition from home-based to '
             'center-based program'
    )
    age_of_majority = fields.Integer()
    max_age_limit = fields.Integer()
    max_family_members_enrolled = fields.Integer(
        help='Maximum number of family members allowed in the program'
    )
    new_icp_min_children = fields.Integer(
        help='Minimum number of children required to start a new ICP'
    )
    icp_min_children = fields.Integer(
        help='Minimum number of children for an ICP'
    )

    @api.model
    def _compute_country(self):
        pass


class FieldOfficeHighRisks(models.Model):
    _name = 'fo.high.risk'
    _inherit = 'connect.multipicklist'
    _description = 'FO high risk'
    res_model = 'compassion.field.office'
    res_field = 'high_risk_ids'
