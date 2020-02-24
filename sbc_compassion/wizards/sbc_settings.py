##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class SBCSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""
    _inherit = 'res.config.settings'

    # Users to notify after Child Departure
    additional_b2s_translation = fields.Binary(
        string='B2S additional translation page template'
    )

    @api.multi
    def set_additional_b2s_translation(self):
        # This is stored in page template for additional B2S pages
        page_template = self.env.ref('sbc_compassion.b2s_additional_page')
        page_template.background = self.additional_b2s_translation

    @api.model
    def get_default_values(self, _fields):
        b2s_add_page = self.env.ref('sbc_compassion.b2s_additional_page')
        return {
            'additional_b2s_translation': b2s_add_page.background,
        }

    @api.model
    def get_param(self, param):
        """ Retrieve a single parameter. """
        return self.get_default_values([param])[param]
