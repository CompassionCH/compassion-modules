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
    country_id = fields.Many2one('res.country', 'Country')
    country_code = fields.Char(related='country_id.code')
    street = fields.Char()
    city = fields.Char()
    province = fields.Char()
    zip_code = fields.Char()
    currency = fields.Char()

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

    disaster_alert_ids = fields.Many2many(
        'fo.disaster.alert', string='Disaster alerts'
    )

    _sql_constraints = [
        ('field_office_id', 'unique(field_office_id)',
         'The field already exists in database.'),
    ]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        field_office = super(FieldOffice, self).create(vals)
        field_office.with_context(async_mode=True).update_informations()
        return field_office

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


class FieldOfficeHighRisks(models.Model):
    _name = 'fo.high.risk'
    _inherit = 'connect.multipicklist'
    _description = 'FO high risk'
    res_model = 'compassion.field.office'
    res_field = 'high_risk_ids'

    value = fields.Char(translate=True)
