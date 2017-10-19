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
from collections import OrderedDict

from .base_mapping import OnrampMapping, new_onramp_mapping


class AdvancedQueryMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.query.filter'

    CONNECT_MAPPING = {
        'Field': ('field_id.id', 'ir.model.fields'),
        'Operator': 'operator',
        'Value': 'value',
    }

    FIELDS_TO_SUBMIT = {
        'Field': None,
        'Operator': None,
        'Value': lambda v: v.split(';')
    }

    def get_connect_data(self, odoo_object, fields_to_submit=None):
        """ Dictionary order is important, so we change it here. """
        connect_data = super(AdvancedQueryMapping, self).get_connect_data(
            odoo_object, fields_to_submit)
        res = OrderedDict(sorted(connect_data.items(), key=lambda i: i[0]))
        return res

    def _process_connect_data(self, connect_data):
        # Replace odoo field id by connect field name
        if 'Field' in connect_data:
            field = self.env['ir.model.fields'].browse(connect_data['Field'])
            # Works only if field is defined in the mapping defined in context
            # (or default mapping)
            mapping_name = self.env.context.get('default_mapping_name',
                                                'default')
            model_mapping = new_onramp_mapping(
                field.model, self.env, mapping_name)
            for connect_name, odoo_name in \
                    model_mapping.CONNECT_MAPPING.iteritems():
                if odoo_name == field.name:
                    connect_data['Field'] = connect_name
                    break
