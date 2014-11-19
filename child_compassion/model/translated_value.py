# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _


class translated_value(orm.Model):
    _name = 'compassion.translated.value'
    _rec_name = 'value_en'

    _columns = {
        'is_tag': fields.boolean(_('Tag')),
        'child_property_ids': fields.many2many(
            'compassion.child.property', 'child_property_to_value',
            'value_id', 'property_id', _('Properties')),
        'project_property_ids': fields.many2many(
            'compassion.project.property', 'project_property_to_value',
            'value_id', 'property_id', _('Properties')),
        'property_name': fields.char(_('Is value for'), required=True,
                                     readonly=True),
        'value_en': fields.char(_('English value'), required=True,
                                readonly=True),
        'value_fr': fields.char(_('French translation')),
        'value_de': fields.char(_('German translation')),
        'value_it': fields.char(_('Italian translation')),
    }

    _defaults = {
        'is_tag': False,
    }

    def get_value_ids(self, cr, uid, eng_values, property_name, context):
        """ Utility method that finds already existing translated values
        or create them if necessary.
        Args:
            - eng_values (list or string): One or several english values for
                                           a given property.
            - property_name (string): The name of the property for which
                                      we are searching the given values.
        Returns:
            A list of translated_ids corresponding to each value given
            in eng_values, or a single id if eng_values is not a list.
        """
        value_ids = []
        if isinstance(eng_values, list):
            for elem in eng_values:
                value_ids.append(self._get_value_id(cr, uid, elem,
                                                    property_name, context))
        elif isinstance(eng_values, basestring):
            value_ids = self._get_value_id(cr, uid, eng_values, property_name,
                                           context)
        return value_ids

    def _get_value_id(self, cr, uid, value, property_name, context=None):
        """ Find or create a translated_value for a given property.
        Returns the translated_value id."""
        value = value.lower()
        val_ids = self.search(cr, uid, [('value_en', '=like', value),
                                        ('property_name', '=', property_name)],
                              context=context)
        if val_ids:
            return val_ids[0]
        prop_id = self.create(cr, uid, {'property_name': property_name,
                                        'value_en': value})
        return prop_id
