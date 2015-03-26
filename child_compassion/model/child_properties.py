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
    _description = "Case Study"

    _columns = {
        'child_id': fields.many2one(
            'compassion.child', _('Concerned child'),
            required=True, ondelete='cascade', readonly=True),
        'unique_id': fields.integer(_("Unique ID"), readonly=True),
        'info_date': fields.date(_('Date of case study'), readonly=True),
        'last_modification_date': fields.date(_('Last modified'),
                                              readonly=True),
        'name': fields.char(_('Name'), readonly=True,
                            track_visibility='onchange'),
        'code': fields.char(_("Child code"), size=9,
                            readonly=True, track_visibility='onchange'),
        'firstname': fields.char(_('Firstname'), readonly=True,
                                 track_visibility='onchange'),
        'gender': fields.selection([
            ('M', 'Male'),
            ('F', 'Female')], _('Gender'), readonly=True),
        'birthdate': fields.date(_('Birthdate'), readonly=True,
                                 track_visibility='onchange'),
        'comments': fields.text(_('Comments'), readonly=True,
                                track_visibility='onchange'),
        'orphan_flag': fields.boolean(_('Is orphan'), readonly=True,
                                      track_visibility='onchange'),
        'handicapped_flag': fields.boolean(_('Is handicapped'), readonly=True,
                                           track_visibility='onchange'),
        'attending_school_flag': fields.boolean(_('Is attending school'),
                                                readonly=True,
                                                track_visibility='onchange'),
        'not_attending_reason': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Not attending school reason'),
            domain=[('property_name', '=', 'not_attending_reason')],
            readonly=True),
        'us_school_level': fields.char(_('US school level'),
                                       readonly=True,
                                       track_visibility='onchange'),
        'school_performance': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('School performances'),
            domain=[('property_name', '=', 'school_performance')],
            readonly=True, track_visibility='onchange'),
        'school_best_subject': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('School best subject'),
            domain=[('property_name', '=', 'school_best_subject')],
            readonly=True, track_visibility='onchange'),
        'marital_status_id': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Marital status of parents'),
            domain=[('property_name', '=', 'marital_status')],
            readonly=True, track_visibility='onchange'),
        'christian_activities_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Christian activities'),
            domain=[('property_name', '=', 'christian_activities')],
            readonly=True, track_visibility='onchange'),
        'family_duties_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Family duties'),
            domain=[('property_name', '=', 'family_duties')], readonly=True,
            track_visibility='onchange'),
        'hobbies_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Hobbies'),
            domain=[('property_name', '=', 'hobbies')], readonly=True,
            track_visibility='onchange'),
        'health_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Health'),
            domain=[('property_name', '=', 'health')], readonly=True,
            track_visibility='onchange'),
        'guardians_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Guardians'),
            domain=[('property_name', '=', 'guardians')], readonly=True,
            track_visibility='onchange'),
        'male_guardian_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Male guardian'),
            domain=[('property_name', '=', 'male_guardian')], readonly=True,
            track_visibility='onchange'),
        'female_guardian_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Female guardian'),
            domain=[('property_name', '=', 'female_guardian')], readonly=True,
            track_visibility='onchange'),
        'father_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Father'),
            domain=[('property_name', '=', 'father')], readonly=True,
            track_visibility='onchange'),
        'mother_ids': fields.many2many(
            'compassion.translated.value', 'child_property_to_value',
            'property_id', 'value_id', _('Mother'),
            domain=[('property_name', '=', 'mother')], readonly=True,
            track_visibility='onchange'),
        'nb_brothers': fields.integer(_('Brothers'), readonly=True,
                                      track_visibility='onchange'),
        'nb_sisters': fields.integer(_('Sisters'), readonly=True,
                                     track_visibility='onchange'),
        'sibling_project_1': fields.char(_('First sibling in project'),
                                         readonly=True),
        'sibling_project_2': fields.char(_('Second sibling in project'),
                                         readonly=True),
        'desc_en': fields.text(_('English description'), readonly=True),
        'desc_fr': fields.text(_('French description'), readonly=True),
        'desc_de': fields.text(_('German description'), readonly=True),
        'desc_it': fields.text(_('Italian description'), readonly=True),
        'pictures_id': fields.many2one(
            'compassion.child.pictures', _('Child images'), readonly=True),
    }

    def attach_pictures(self, cr, uid, ids, pictures_id, context=None):
        if len(ids) != 1:
            raise orm.except_orm(
                _('Picture error'),
                _('You cannot attach a picture to more than one '
                  'case study.'))
        self.write(cr, uid, ids, {'pictures_id': pictures_id}, context)
        return True
