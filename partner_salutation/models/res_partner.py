##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' namenoupdate="1"
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = ["res.partner", "translatable.model"]
    _name = "res.partner"

    salutation = fields.Char(compute="_compute_salutation")
    gender = fields.Selection(related="title.gender", store=True, readonly=False)

    def _compute_salutation(self):
        """ Define a method _get_salutation_<lang_code> for using a specific salutation based on partner language
            or salutation_language if defined in context
        """
        for partner in self:
            language = self.env.context.get("salutation_language", partner.lang)
            lang_partner = partner.with_context(lang=language)
            if hasattr(lang_partner, "_get_salutation_" + partner.lang):
                partner.salutation = getattr(
                    lang_partner, "_get_salutation_" + language)()
            else:
                partner.salutation = lang_partner._get_salutation_en_US()

    def _get_salutation_en_US(self):
        self.ensure_one()
        if self.firstname:
            return "Dear " + self.firstname
        else:
            return "Dear friends of Compassion"
