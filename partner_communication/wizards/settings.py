##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class Settings(models.TransientModel):
    """ Settings configuration."""
    _inherit = "res.config.settings"

    module_partner_communication_omr = fields.Boolean(
        "Add OMR marks", help="Add marks to printed communications for using folding machines."
    )
    module_partner_communication_crm_phone = fields.Boolean(
        "Use CRM phone features", help="Link communications with CRM phonecalls"
    )
