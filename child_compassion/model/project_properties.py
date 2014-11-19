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
    _name = 'compassion.project.property'

    _columns = {
        'project_id': fields.many2one(
            'compassion.project', _('Concerned project'),
            required=True, ondelete='cascade'),
        'name': fields.char(_("Name")),
        'code': fields.char(_("Project code")),
        'country_id': fields.many2one('compassion.country', _('Country')),
        'type': fields.selection([
            ('CDSP', 'CDSP'),
            ('CSP', 'CSP')], _('Program type')),
        'start_date': fields.date(_('Partnership begining')),
        'stop_date': fields.date(_('Partnership ending')),
        'last_update_date': fields.date(_('Last update')),
        'suspension': fields.selection([
            ('suspended', _('Suspended')),
            ('fund-suspended', _('Suspended & fund retained'))],
            _('Suspension')),
        'status_date': fields.date(_('Last status change')),
        'status_comment': fields.char(_('Status comment')),
        'local_church_name': fields.char(_('Local church name')),
        'hiv_category': fields.selection([
            ('AFFCTD', _('Affected')),
            ('NOTAFF', _('Not affected'))],
            _('HIV/Aids category for project area')),
        'month_school_year_begins': fields.selection([
            ('1', _('January')), ('2', _('February')), ('3', _('March')),
            ('4', _('April')), ('5', _('May')), ('6', _('June')),
            ('7', _('July')), ('8', _('August')), ('9', _('September')),
            ('10', _('October')), ('11', _('November')), ('12', _('December'))
            ], _('Month school begins each year')),
        'country_denomination': fields.char(_('Local denomination')),
        'western_denomination': fields.char(_('Western denomination')),
        'community_name': fields.char(_('Community name')),
        'country_common_name': fields.text(_('Country common name')),
        'floor_material_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'property_id', 'value_id', _('Floor material'),
            domain=[('property_name', '=', 'floor_material')]),
        'wall_material_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'property_id', 'value_id', _('Wall material'),
            domain=[('property_name', '=', 'wall_material')]),
        'roof_material_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'property_id', 'value_id', _('Roof material'),
            domain=[('property_name', '=', 'roof_material')]),
        'spoken_languages_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'property_id', 'value_id', _('Spoken languages'),
            domain=[('property_name', '=', 'spoken_languages')]),
        'primary_diet_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'property_id', 'value_id', _('Primary diet'),
            domain=[('property_name', '=', 'primary_diet')]),
        'health_problems_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'property_id', 'value_id', _('Health problems'),
            domain=[('property_name', '=', 'health_problems')]),
        'primary_occupation_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'property_id', 'value_id', _('Primary occupation'),
            domain=[('property_name', '=', 'primary_occupation')]),
        'terrain_description_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'property_id', 'value_id', _('Terrain description'),
            domain=[('property_name', '=', 'terrain_description')]),
        'unemployment_rate': fields.float(_('Unemployment rate')),
        'closest_city': fields.char(_('Closest city')),
        'community_population': fields.integer(_('Community population')),
        'monthly_income': fields.float(_('Monthly income')),
        'distance_from_closest_city': fields.text(_('Distance from closest '
                                                    'city')),
    }
