# -*- encoding: utf-8 -*-
##############################################################################
#
#    Compassion children module for OpenERP
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    @author: Cyril Sester <csester@compassion.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _


class child_property(orm.Model):
    _name = 'compassion.child.property'
    _order = 'child_id, info_date desc'
    
    _columns = {
        'child_id': fields.many2one(
            'compassion.child', _('Concerned child'), required=True),
        'info_date': fields.date(_('Date of case study')),
        'sibling_flag': fields.boolean(_('Has sibling')),
        'orphan_flag': fields.boolean(_('Is orphan')),
        'handicapped_flag': fields.boolean(_('Is handicapped')),
        'attending_school_flag': fields.boolean(_('Is attending school')),
        'us_school_level': fields.char(_('US school level')),
        'school_performance': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('School performances'),
            domain=[('property_name', '=', 'school_performance')]),
        'school_best_subject': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('Marital status of parents'),
            domain=[('property_name', '=', 'school_best_subject')]),
        'marital_status_id': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('Marital status of parents'),
            domain=[('property_name', '=', 'marital_status')]),
        'christian_activities_ids': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('Christian activities'),
            domain=[('property_name', '=', 'christian_activities')]),
        'family_duties_ids': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('Family duties'),
            domain=[('property_name', '=', 'family_duties')]),
        'hobbies_ids': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('Hobbies'),
            domain=[('property_name', '=', 'hobbies')]),
        'health_ids': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('Health'),
            domain=[('property_name', '=', 'health')]),
        'guardians_ids': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('Guardians'),
            domain=[('property_name', '=', 'guardians')]),
        'male_guardian_ids': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('Male guardian'),
            domain=[('property_name', '=', 'male_guardian')]),
        'female_guardian_ids': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('Female guardian'),
            domain=[('property_name', '=', 'female_guardian')]),
        'father_ids': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('Mother'),
            domain=[('property_name', '=', 'father')]),
        'mother_ids': fields.many2many(
            'compassion.child.property.value', 'child_property_to_value',
            'property_id', 'value_id', _('Father'),
            domain=[('property_name', '=', 'mother')]),
        'family_size': fields.integer(_('Family size')),
        'fullshot_image_uri': fields.char(_('Image URI')),
    }


class child_property_value(orm.Model):
    _name = 'compassion.child.property.value'
    _rec_name = 'value_en'
    
    _columns = {
        'property_name': fields.char('Is value for', required=True, readonly=True),
        'value_en': fields.char(_('English value'), required=True, readonly=True),
        'value_fr_m': fields.char(_('French masculine translation')),
        'value_fr_f': fields.char(_('French feminine translation')),
        'value_de_m': fields.char(_('German masculine translation')),
        'value_de_f': fields.char(_('German feminine translation')),
        'value_it_m': fields.char(_('Italian masculine translation')),
        'value_it_f': fields.char(_('Italian feminine translation')),        
    }
