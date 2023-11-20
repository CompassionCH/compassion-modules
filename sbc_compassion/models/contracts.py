##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import date

from odoo import _, api, fields, models


class Contracts(models.Model):
    """Add correspondence information in contracts"""

    _inherit = "recurring.contract"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    child_letter_ids = fields.Many2many(
        "correspondence",
        string="Child letters",
        compute="_compute_get_letters",
        readonly=False,
    )
    sponsor_letter_ids = fields.Many2many(
        "correspondence",
        string="Sponsor letters",
        compute="_compute_get_letters",
        readonly=False,
    )
    nb_letters = fields.Integer(compute="_compute_get_letters")
    last_letter = fields.Integer(
        "Days since sponsor wrote", compute="_compute_last_letter"
    )
    last_sponsor_letter = fields.Date("Date of last sponsor letter")
    write_for_birthday_alert = fields.Boolean(
        help="True when child will have birthday in less than 3 months and"
        "sponsor has not written in this period.",
        compute="_compute_write_for_birthday_alert",
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_get_letters(self):
        """Retrieve correspondence of sponsorship contracts."""
        for sponsorship in self:
            letters_obj = self.env["correspondence"]
            letters = letters_obj.search([("sponsorship_id", "=", sponsorship.id)])
            sponsorship.child_letter_ids = letters.filtered(
                lambda letter: letter.direction == "Beneficiary To Supporter"
            )
            sponsorship.sponsor_letter_ids = letters.filtered(
                lambda letter: letter.direction == "Supporter To Beneficiary"
            )
            sponsorship.nb_letters = len(letters)

    def _compute_last_letter(self):
        """
        Get the date of the last letter sent to the child by the sponsor and
        compute since how many days he didn't write him any letter.
        If sponsor never wrote him, return -1
        :return: int value
        """
        for contract in self:
            try:
                # Try to get days difference between today and last letter
                contract.last_letter = (
                    date.today() - contract.sponsor_letter_ids[:1].scanned_date
                ).days
            except TypeError:
                contract.last_letter = -1

    def _compute_write_for_birthday_alert(self):
        today = date.today()
        for contract in self:
            if not contract.child_id.birthdate:
                contract.write_for_birthday_alert = False
                continue
            next_birthday = contract.child_id.birthdate.replace(year=today.year)

            # take next year birthday
            # if birthday already pass for this year
            if next_birthday < today:
                next_birthday = next_birthday.replace(year=next_birthday.year + 1)

            days_until_birthday = (next_birthday - today).days
            contract.write_for_birthday_alert = days_until_birthday <= 90 and (
                contract.last_letter == -1
                or contract.last_letter > 90 - days_until_birthday
            )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################

    @api.model
    def create(self, vals):
        if (
            "child_id" in vals
            and "correspondent_id" in vals
            and "reading_language" not in vals
        ):
            child = self.env["compassion.child"].browse(vals["child_id"])
            correspondent = self.env["res.partner"].browse(vals["correspondent_id"])
            english = self.env.ref("advanced_translation.lang_compassion_english")
            spoken_langs = correspondent.spoken_lang_ids
            reading_language = (
                (spoken_langs & child.correspondence_language_id)
                or (spoken_langs & english)
                or spoken_langs.filtered(
                    lambda lang: lang.lang_id.code == correspondent.lang
                )
            )
            vals["reading_language"] = reading_language.id
        return super().create(vals)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange("correspondent_id", "child_id")
    def onchange_relationship(self):
        """Define the preferred reading language for the correspondent.
        1. Sponsor main language if child speaks that language
        2. Any language spoken by both sponsor and child other than
           English
        3. English
        """
        for sponsorship in self:
            if sponsorship.correspondent_id and sponsorship.child_id:
                sponsor = sponsorship.correspondent_id
                child_languages = (
                    sponsorship.child_id.field_office_id.spoken_language_ids
                )
                sponsor_languages = sponsor.spoken_lang_ids
                lang_obj = self.env["res.lang.compassion"]
                sponsor_main_lang = lang_obj.search(
                    [("lang_id.code", "=", sponsor.lang)]
                )
                if sponsor_main_lang in child_languages:
                    sponsorship.reading_language = sponsor_main_lang
                else:
                    english = self.env.ref(
                        "advanced_translation.lang_compassion_english"
                    )
                    common_langs = (child_languages & sponsor_languages) - english
                    if common_langs:
                        sponsorship.reading_language = common_langs[0]
                    else:
                        sponsorship.reading_language = english

    def open_letters(self):
        return {
            "name": _("Letters"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "correspondence",
            "context": self.with_context(
                group_by=False, search_default_sponsorship_id=self.id
            ).env.context,
            "target": "current",
        }

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    def contract_active(self):
        """Send letters that were on hold."""
        super().contract_active()
        for contract in self.filtered(
            lambda c: "S" in c.type and not c.project_id.hold_s2b_letters
        ):
            contract.sponsor_letter_ids.filtered(
                lambda c: not c.kit_identifier
            ).reactivate_letters("Sponsorship activated")
