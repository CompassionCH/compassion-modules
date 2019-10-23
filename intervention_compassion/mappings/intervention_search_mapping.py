##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class InterventionSearchMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.intervention.search'

    CONNECT_MAPPING = {
        'InterventionFilter': ('search_filter_ids', 'compassion.query.filter'),
        'InterventionQueryResponseList': (
            'intervention_ids', 'compassion.global.intervention')
    }

    FIELDS_TO_SUBMIT = {
        'InterventionFilter': None,
    }

    def _process_connect_data(self, connect_data):
        """ Put data in outgoing wrapper. """
        data = connect_data.copy()
        connect_data.clear()
        connect_data['InterventionQuery'] = data

    def _process_odoo_data(self, odoo_data):
        """ Convert Intervention Response List into ORM records creation. """
        if 'intervention_ids' in odoo_data:
            intervention_obj = self.env['compassion.global.intervention']
            interventions = list()
            for intervention_vals in odoo_data['intervention_ids']:
                intervention_id = intervention_vals['intervention_id']
                intervention = intervention_obj.search([
                    ('intervention_id', '=', intervention_id)])
                if intervention:
                    intervention.write(intervention_vals)
                else:
                    intervention = intervention_obj.create(intervention_vals)
                interventions.append((4, intervention.id))

            odoo_data['intervention_ids'] = interventions or False
