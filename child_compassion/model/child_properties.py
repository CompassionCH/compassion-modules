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


from openerp.osv import orm, fields
from openerp.tools.translate import _


class child_property(orm.Model):
    _name = 'compassion.child.property'
    _order = 'child_id, info_date desc'
    _inherit = 'mail.thread'

    _columns = {
        'child_id': fields.many2one(
            'compassion.child', _('Concerned child'),
            required=True, ondelete='cascade'),
        'unique_id': fields.integer(_("Unique ID")),
        'info_date': fields.date(_('Date of case study')),
        'last_modification_date': fields.date(_('Last modified')),
        'name': fields.char(_('Name'), track_visibility='onchange'),
        'code': fields.char(_("Child code"), size=9,
                            track_visibility='onchange'),
        'firstname': fields.char(_('Firstname'), track_visibility='onchange'),
        'gender': fields.selection([
            ('M', 'Male'),
            ('F', 'Female')], _('Gender')),
        'birthdate': fields.date(_('Birthdate'), track_visibility='onchange'),
        'sibling_flag': fields.boolean(_('Has sibling'),
                                       track_visibility='onchange'),
        'orphan_flag': fields.boolean(_('Is orphan'),
                                      track_visibility='onchange'),
        'handicapped_flag': fields.boolean(_('Is handicapped'),
                                           track_visibility='onchange'),
        'attending_school_flag': fields.boolean(_('Is attending school'),
                                                track_visibility='onchange'),
        'not_attending_reason': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Not attending school reason'),
            domain=[('property_name', '=', 'not_attending_reason')]),
        'us_school_level': fields.char(_('US school level'),
                                       track_visibility='onchange'),
        'school_performance': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('School performances'),
            domain=[('property_name', '=', 'school_performance')],
            track_visibility='onchange'),
        'school_best_subject': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('School best subject'),
            domain=[('property_name', '=', 'school_best_subject')],
            track_visibility='onchange'),
        'marital_status_id': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Marital status of parents'),
            domain=[('property_name', '=', 'marital_status')],
            track_visibility='onchange'),
        'christian_activities_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Christian activities'),
            domain=[('property_name', '=', 'christian_activities')],
            track_visibility='onchange'),
        'family_duties_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Family duties'),
            domain=[('property_name', '=', 'family_duties')],
            track_visibility='onchange'),
        'hobbies_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Hobbies'),
            domain=[('property_name', '=', 'hobbies')],
            track_visibility='onchange'),
        'health_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Health'),
            domain=[('property_name', '=', 'health')],
            track_visibility='onchange'),
        'guardians_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Guardians'),
            domain=[('property_name', '=', 'guardians')],
            track_visibility='onchange'),
        'male_guardian_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Male guardian'),
            domain=[('property_name', '=', 'male_guardian')],
            track_visibility='onchange'),
        'female_guardian_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Female guardian'),
            domain=[('property_name', '=', 'female_guardian')],
            track_visibility='onchange'),
        'father_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Father'),
            domain=[('property_name', '=', 'father')],
            track_visibility='onchange'),
        'mother_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Mother'),
            domain=[('property_name', '=', 'mother')],
            track_visibility='onchange'),
        'nb_children_family': fields.integer(_('Children in family'),
                                             track_visibility='onchange'),
        'nb_brothers': fields.integer(_('Brothers'),
                                      track_visibility='onchange'),
        'nb_sisters': fields.integer(_('Sisters'),
                                     track_visibility='onchange'),
    }
