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

from openerp import models, fields, api


class translated_value(models.Model):
    _name = 'compassion.translated.value'
    _rec_name = 'value_en'
    _order = 'property_name asc'

    is_tag = fields.Boolean('Tag')
    child_property_ids = fields.Many2many(
        'compassion.child.property', 'child_property_to_value',
        'value_id', 'property_id', 'Properties')
    project_property_ids = fields.Many2many(
        'compassion.project', 'project_property_to_value',
        'value_id', 'project_id', 'Properties')
    property_name = fields.Char('Is value for', required=True, readonly=True)
    value_en = fields.Char('English value', required=True, readonly=True)
    value_fr = fields.Char('French translation')
    value_de = fields.Char('German translation')
    value_it = fields.Char('Italian translation')

    def get_translated_value(self, lang):
        self.ensure_one()
        html_id = self.value_en
        translated_value = getattr(self, "value_"+lang) or self.value_en
        color = 'red' if not getattr(self, "value_"+lang) else 'blue'
        return u'<span id="{0}" style="color:{1}">{2}</span>'.format(
            html_id, color, translated_value)

    @api.model
    def get_value_ids(self, eng_values, property_name):
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
                value_ids.append(self._get_value_id(elem, property_name))
        elif isinstance(eng_values, basestring):
            value_ids = self._get_value_id(eng_values, property_name)
        return value_ids

    @api.model
    def _get_value_id(self, value, property_name):
        """ Find or create a translated_value for a given property.
        Returns the translated_value id."""
        value = value.lower().strip()
        property_vals = {
            'property_name': property_name,
            'value_en': value}
        if not value:
            return False

        val_ids = self.search([('value_en', '=like', value),
                               ('property_name', '=', property_name)])
        if val_ids:
            return val_ids[0].id

        return self.create(property_vals).id
