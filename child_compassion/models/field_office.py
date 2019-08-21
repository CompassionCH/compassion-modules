# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import api, models, fields
from werkzeug.exceptions import BadRequest


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
    country_id = fields.Many2one('res.country', 'Country')
    country_code = fields.Char(related='country_id.code')
    street = fields.Char()
    city = fields.Char()
    province = fields.Char()
    zip_code = fields.Char()
    currency = fields.Char()
    image_url = fields.Char()
    summary = fields.Text()
    learning_info_list = fields.One2many(
        'learning.info', 'field_office_id', string='Learning information list'
    )
    available_on_childpool = fields.Boolean(
        default=True,
        help='Uncheck to restrict child selection from this field office.'
    )

    primary_language_id = fields.Many2one('res.lang.compassion', 'Primary '
                                                                 'language')
    spoken_language_ids = fields.Many2many(
        'res.lang.compassion', 'field_office_spoken_langs',
        string='Spoken languages')
    translated_language_ids = fields.Many2many(
        'res.lang.compassion', 'field_office_translated_langs',
        string='Translated languages')

    staff_number = fields.Integer()
    country_information = fields.Char()
    high_risk_ids = fields.Many2many(
        'fo.high.risk', string='Beneficiary high risks'
    )

    disaster_alert_ids = fields.Many2many(
        'fo.disaster.alert', string='Disaster alerts'
    )
    fcp_hours_week = fields.Integer(
        'Hours/week', default=8, oldname='icp_hours_week')
    fcp_meal_week = fields.Integer(
        'Meals/week', default=1, oldname='icp_meal_week')
    fcp_medical_check = fields.Integer(
        'Medical check/year', default=1, oldname='icp_medical_check')
    fcp_ids = fields.One2many(
        'compassion.project', 'field_office_id', 'FCP', oldname='icp_ids')

    _sql_constraints = [
        ('field_office_id', 'unique(field_office_id)',
         'The field already exists in database.'),
    ]

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################

    @api.multi
    def update_informations(self):
        """ Get the most recent informations for selected field offices and
        update them accordingly. """
        message_obj = self.env['gmc.message.pool']
        action_id = self.env.ref(
            'child_compassion.field_office_details').id

        message_vals = {
            'action_id': action_id,
            'object_id': self.id,
        }
        message_obj.with_context(async_mode=False).create(message_vals)
        return True

    @api.model
    def mobile_get_learning(self, **other_params):
        if 'country' not in other_params:
            raise BadRequest()

        country = other_params['country']
        country_id = self.env['res.country'].search([
            ('name', '=', country)
        ])
        field_office = self.search([
            ('country_id', '=', country_id.id)
        ])
        res = []
        for field_id in field_office.ids:
            res.append({
                'ID': field_id,
                'PROJECT_ID': country,
                'SUMMARY': field_office.summary,
                'IMAGE': field_office.image_url,
                'SCHEDULE': field_office._get_schedules_json()
            })
        return res

    def _get_schedules_json(self):
        res = []
        for schedule in self.learning_info_list:
            res.append(schedule.get_learning_json())
        return res


class LearningInfo(models.Model):
    _name = 'learning.info'
    _description = 'Learning information'

    time = fields.Datetime()
    title = fields.Text(
        translate=True,
        help="Contains the title of the learning information."
    )
    description = fields.Text(
        translate=True,
        help="Contains the description of the learning information."
    )
    field_office_id = fields.Many2one(
        'compassion.field.office', 'learning_info_list'
    )

    def get_learning_json(self):
        return {
            'TIME': self.time,
            'DESCRIPTION': self.description,
            'TITLE': self.title
        }


class FieldOfficeHighRisks(models.Model):
    _name = 'fo.high.risk'
    _inherit = 'connect.multipicklist'
    _description = 'FO high risk'
    res_model = 'compassion.field.office'
    res_field = 'high_risk_ids'

    value = fields.Char(translate=True)
