# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Kevin Cristi
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp.osv import orm, fields
from openerp.tools.translate import _


class project_age_group(orm.Model):
    """ This section provides the school schedule of children
        according to their age.
        It will display the school days and school months. """

    _name = 'compassion.project.age.group'

    _columns = {
        'project_id': fields.many2one(
            'compassion.project', _('Project'),
            required=True, ondelete='cascade'),
        'low_age': fields.integer(_('Low age')),
        'high_age': fields.integer(_('High age')),
        'school_hours': fields.integer(_('School hours')),
        'school_months_ids': fields.many2many(
            'compassion.translated.value', 'project_age_group_to_value',
            'project_age_group_id', 'value_id', _('School months'),
            domain=[('property_name', '=', 'school_months')]),
        'school_days_ids': fields.many2many(
            'compassion.translated.value', 'project_age_group_to_value',
            'project_age_group_id', 'value_id', _('School days'),
            domain=[('property_name', '=', 'school_days')]),
    }
