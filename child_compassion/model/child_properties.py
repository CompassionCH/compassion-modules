# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime


class child_property(models.Model):
    _name = 'compassion.child.property'
    _order = 'child_id, info_date desc'
    _inherit = 'mail.thread'
    _description = "Case Study"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # General Information
    #####################
    child_id = fields.Many2one(
        'compassion.child', 'Child', required=True, readonly=True,
        ondelete='cascade')
    unique_id = fields.Integer('Unique ID', readonly=True)
    info_date = fields.Date('Date of case study', readonly=True)
    last_modification_date = fields.Date('Last modified', readonly=True)
    name = fields.Char(readonly=True, track_visibility='onchange')
    code = fields.Char(
        'Child code', size=9, readonly=True, track_visibility='onchange')
    firstname = fields.Char(readonly=True, track_visibility='onchange')
    gender = fields.Selection([
        ('M', 'Male'), ('F', 'Female')], readonly=True)
    birthdate = fields.Date(readonly=True, track_visibility='onchange')
    comments = fields.Text(readonly=True, track_visibility='onchange')
    orphan_flag = fields.Boolean(
        'Is orphan', readonly=True, track_visibility='onchange')
    handicapped_flag = fields.Boolean(
        'Is handicapped', readonly=True, track_visibility='onchange')
    health_ids = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'Health',
        readonly=True, track_visibility='onchange',
        domain=[('property_name', '=', 'health')])

    # Schooling
    ###########
    attending_school_flag = fields.Boolean(
        'Is attending school', readonly=True, track_visibility='onchange')
    not_attending_reason = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'Not attending school reason',
        readonly=True,
        domain=[('property_name', '=', 'not_attending_reason')])
    us_school_level = fields.Char(
        'US school level', readonly=True, track_visibility='onchange')
    school_performance = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'School performances',
        readonly=True, track_visibility='onchange',
        domain=[('property_name', '=', 'school_performance')])
    school_best_subject = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'School best subject',
        readonly=True, track_visibility='onchange',
        domain=[('property_name', '=', 'school_best_subject')])

    # Activities
    ############
    christian_activities_ids = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'Christian activities',
        readonly=True, track_visibility='onchange',
        domain=[('property_name', '=', 'christian_activities')])
    family_duties_ids = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'Family duties',
        readonly=True, track_visibility='onchange',
        domain=[('property_name', '=', 'family_duties')])
    hobbies_ids = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'Hobbies',
        readonly=True, track_visibility='onchange',
        domain=[('property_name', '=', 'hobbies')])

    # Home
    ######
    marital_status_id = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'Marital status of parents',
        readonly=True, track_visibility='onchange',
        domain=[('property_name', '=', 'marital_status')])
    guardians_ids = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'Guardians',
        readonly=True, track_visibility='onchange',
        domain=[('property_name', '=', 'guardians')])
    male_guardian_ids = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'Male guardian',
        domain=[('property_name', '=', 'male_guardian')], readonly=True,
        track_visibility='onchange')
    female_guardian_ids = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'Female guardian',
        domain=[('property_name', '=', 'female_guardian')], readonly=True,
        track_visibility='onchange')
    father_ids = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', 'Father',
        domain=[('property_name', '=', 'father')], readonly=True,
        track_visibility='onchange')
    mother_ids = fields.Many2many(
        'compassion.translated.value', 'child_property_to_value',
        'property_id', 'value_id', _('Mother'),
        domain=[('property_name', '=', 'mother')], readonly=True,
        track_visibility='onchange')
    nb_brothers = fields.Integer(
        'Brothers', readonly=True, track_visibility='onchange')
    nb_sisters = fields.Integer(
        'Sisters', readonly=True, track_visibility='onchange')
    sibling_project_1 = fields.Char(
        'First sibling in project', readonly=True)
    sibling_project_2 = fields.Char(
        'Second sibling in project', readonly=True)

    # Descriptions and pictures
    ###########################
    desc_en = fields.Text('English description', readonly=True)
    desc_fr = fields.Text('French description', readonly=True)
    desc_de = fields.Text('German description', readonly=True)
    desc_it = fields.Text('Italian description', readonly=True)
    pictures_id = fields.Many2one(
        'compassion.child.pictures', 'Child images', readonly=True)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ When creating a new Case Study, check if a recent picture exists
        and link to it if necessary. """
        case_study = super(child_property, self).create(vals)

        pictures_obj = self.env['compassion.child.pictures']
        pictures = pictures_obj.search(
            [('child_id', '=', case_study.child_id.id)],
            order='date desc')
        last_pictures = pictures and pictures[0]
        if last_pictures and not last_pictures.case_study_id:
            six_months = 180
            case_study_date = datetime.strptime(case_study.info_date, DF)
            picture_date = datetime.strptime(last_pictures.date, DF)

            date_diff = abs((case_study_date - picture_date).days)

            if (date_diff <= six_months or case_study.child_id.type == 'LDP'):
                case_study.attach_pictures(last_pictures.id)
                last_pictures.write({'case_study_id': case_study.id})

        return case_study

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def attach_pictures(self, pictures_id):
        self.ensure_one()
        return self.write({'pictures_id': pictures_id})
