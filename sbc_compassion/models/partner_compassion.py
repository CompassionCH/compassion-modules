##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models, api


class ResPartner(models.Model):
    """ Add correspondence preferences to Partners """

    _inherit = "res.partner"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    spoken_lang_ids = fields.Many2many(
        "res.lang.compassion",
        string="Spoken languages",
        groups="child_compassion.group_sponsorship",
        readonly=False,
    )
    translator_email = fields.Char(
        help="e-mail address used in SDL", groups="child_compassion.group_sponsorship"
    )
    nb_letters = fields.Integer(
        compute="_compute_nb_letters", groups="child_compassion.group_sponsorship"
    )
    translated_letter_ids = fields.One2many(
        "correspondence", "translator_id", "Translated letters", readonly=False
    )
    last_writing_date = fields.Date(compute="_compute_last_writing_date")

    @api.multi
    def _compute_nb_letters(self):
        for partner in self:
            partner.nb_letters = self.env["correspondence"].search_count(
                [("partner_id", "=", partner.id)]
            )

    @api.multi
    def _compute_last_writing_date(self):
        for partner in self:
            last_letter = self.env["correspondence.last.writing.report"].search(
                [("partner_id", "=", partner.id), ("last_write_date", "!=", False)],
                order="last_write_date desc",
                limit=1,
            )
            partner.last_writing_date = last_letter.last_write_date

    @api.model
    def create(self, vals):
        lang_id = (
            self.env["res.lang.compassion"]
            .search([("lang_id.code", "=", vals.get("lang", self.env.lang))])
            .ids
        )
        if "spoken_lang_ids" not in vals:
            vals["spoken_lang_ids"] = [(6, 0, lang_id)]
        elif lang_id:
            base_language = (4, lang_id[0])
            spoken_languages = vals["spoken_lang_ids"]
            # If the base language is not in the list of the spoken languages,
            # we have to add it
            if base_language not in spoken_languages:
                spoken_languages.append(base_language)
                vals["spoken_lang_ids"] = spoken_languages
        return super().create(vals)

    @api.multi
    def open_letters(self):
        """ Open the tree view correspondence of partner """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Letters",
            "res_model": "correspondence",
            "view_type": "form",
            "view_mode": "tree,form",
            "context": self.with_context(
                group_by=False, search_default_partner_id=self.id
            ).env.context,
        }

    @api.onchange("lang")
    def onchange_main_language(self):
        lang = self.env["res.lang"].search([("code", "=", self.lang)])
        spoken_lang = self.env["res.lang.compassion"].search(
            [("lang_id", "=", lang.id)]
        )
        if spoken_lang:
            self.spoken_lang_ids += spoken_lang

    @api.multi
    def forget_me(self):
        super().forget_me()
        # Delete correspondence
        self.env["correspondence"].with_context(force_delete=True).search(
            [("partner_id", "=", self.id)]
        ).unlink()
        return True
