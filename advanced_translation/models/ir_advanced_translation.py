##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api, _


class IrAdvancedTranslation(models.Model):
    """ Used to translate terms in context of a subject that can be
    male / female and singular / plural.
    """

    _name = "ir.advanced.translation"
    _description = "Advanced translation terms"
    _order = "src asc"

    src = fields.Text("Source", required=True, translate=False, index=True)
    lang = fields.Selection("_get_lang", required=True)
    group = fields.Char()
    male_singular = fields.Text(translate=False)
    male_plural = fields.Text(translate=False)
    female_singular = fields.Text(translate=False)
    female_plural = fields.Text(translate=False)

    _sql_constraints = [("unique_term", "unique(src, lang)", "The term already exists")]

    @api.model
    def _get_lang(self):
        langs = self.env["res.lang"].search([])
        return [(l.code, l.name) for l in langs]

    @api.model
    def get(self, src, female=False, plural=False):
        """ Returns the translation term. """
        lang = self.env.context.get("lang") or self.env.lang or "en_US"
        term = self.search([("src", "=", src), ("lang", "=", lang)])
        if not term:
            return _(src)
        if female and plural:
            return term.female_plural or ""
        if female:
            return term.female_singular or ""
        if plural:
            return term.male_plural or ""
        return term.male_singular or ""
