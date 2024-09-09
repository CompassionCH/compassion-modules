##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from iso639 import Lang

from odoo import fields, models


class ResLang(models.Model):

    """This class adds spoken languages to match Compassion needs."""

    _name = "res.lang.compassion"
    _description = "Compassion language"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    name = fields.Char(size=128, translate=True)
    code_iso = fields.Char(size=128)
    lang_id = fields.Many2one("res.lang", readonly=False)
    translatable = fields.Boolean(help="Can be translated by GP")

    def search_iso639(self, iso_str):
        iso_lang = Lang(iso_str)
        return self.search([("code_iso", "ilike", iso_lang.pt3)], limit=1)
