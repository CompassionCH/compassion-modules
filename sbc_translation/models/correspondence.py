##############################################################################
#
#    Copyright (C) 2015-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <eicher31@hotmail.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging


from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.addons.sbc_compassion.models.correspondence_page import BOX_SEPARATOR

_logger = logging.getLogger(__name__)


class Correspondence(models.Model):
    """ This class intercepts a letter before it is sent to GMC.
        Letters are pushed to local translation platform if needed.
        """
    _inherit = "correspondence"

    user_id = fields.Many2one("res.users", "Local translator")
    src_translation_lang_id = fields.Many2one(
        "res.lang.compassion", "Source of translation", readonly=False
    )
    translate_date = fields.Datetime()

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Create a message for sending the CommKit after be translated on
             the local translate platform.
        """
        if vals.get("direction") == "Beneficiary To Supporter":
            correspondence = super().create(vals)
        else:
            sponsorship = self.env["recurring.contract"].browse(vals["sponsorship_id"])

            original_lang = self.env["res.lang.compassion"].browse(
                vals.get("original_language_id")
            )

            # Languages the office/region understand
            office = sponsorship.child_id.project_id.field_office_id
            language_ids = office.spoken_language_ids + office.translated_language_ids

            if original_lang.translatable and original_lang not in language_ids:
                correspondence = super(
                    Correspondence, self.with_context(no_comm_kit=True)
                ).create(vals)
                correspondence.send_local_translate()
            else:
                correspondence = super().create(vals)

        return correspondence

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def process_letter(self):
        """ Called when B2S letter is Published. Check if translation is
         needed and upload to translation platform. """
        for letter in self:
            if (letter.beneficiary_language_ids & letter.supporter_languages_ids) or \
                    letter.has_valid_language or self.env.context.get("force_publish"):
                super(Correspondence, letter).process_letter()
            else:
                letter.download_attach_letter_image()
                letter.send_local_translate()
        return True

    @api.multi
    def send_local_translate(self):
        """
        Sends the letter to the local translation platform.
        :return: None
        """
        self.ensure_one()

        # Specify the src and dst language
        src_lang, dst_lang = self._get_translation_langs()

        self.write(
            {
                "state": "Global Partner translation queue",
                "src_translation_lang_id": src_lang.id,
            }
        )

        # Remove any pending GMC message (will be recreated after translation)
        self.env["gmc.message"].search([
            ("action_id", "=", self.env.ref("sbc_compassion.create_letter").id),
            ("object_id", "=", self.id),
            ("state", "!=", "success")
        ]).unlink()
        return True

    @api.multi
    def remove_local_translate(self):
        """
        Remove a letter from local translation platform and change state of
        letter in Odoo
        :return: None
        """
        self.ensure_one()
        if self.direction == "Supporter To Beneficiary":
            self.state = "Received in the system"
            self.create_commkit()
        else:
            self.state = "Published to Global Partner"
            self.with_context(force_publish=True).process_letter()
        return True

    # TODO Pair with new platform
    @api.multi
    def submit_translation(self, translate_lang, translate_text, translator, src_lang):
        """
        Puts the translated text into the correspondence.
        :param translate_lang: code_iso of the language of the translation
        :param translate_text: text of the translation
        :param translator: reference of the translator
        :param src_lang: code_iso of the source language of translation
        :return: None
        """
        self.ensure_one()
        translate_lang_id = (
            self.env["res.lang.compassion"]
                .search([("code_iso", "=", translate_lang),
                         ("translatable", "=", True)])
                .id
        )
        src_lang_id = (
            self.env["res.lang.compassion"].search([
                ("code_iso", "=", src_lang),
                ("translatable", "=", True)
            ]).id
        )
        translator_partner = self.env["res.partner"].search([("ref", "=", translator)])

        letter_vals = {
            "translation_language_id": translate_lang_id,
            "translator_id": translator_partner.id,
            "src_translation_lang_id": src_lang_id,
            "translate_date": fields.Datetime.now()
        }
        if self.direction == "Supporter To Beneficiary":
            state = "Received in the system"

            # Compute the target text
            target_text = "english_text"
            if translate_lang != "eng":
                target_text = "translated_text"

            # Remove #BOX# in the text, as supporter letters don't have boxes
            translate_text = translate_text.replace(BOX_SEPARATOR, "\n")
        else:
            state = "Published to Global Partner"
            target_text = "translated_text"

        # Check that layout L4 translation gets on second page
        if self.template_id.layout == "CH-A-4S01-1" and not translate_text.startswith(
                "#PAGE#"
        ):
            translate_text = "#PAGE#" + translate_text
        letter_vals.update(
            {target_text: translate_text.replace("\r", ""), "state": state, }
        )
        self.write(letter_vals)

        # Send to GMC
        if self.direction == "Supporter To Beneficiary":
            self.create_commkit()
        else:
            # Recompose the letter image and process letter
            if super().process_letter():
                self.send_communication()

    @api.multi
    def resubmit_to_translation(self):
        for letter in self:
            if letter.state != "Translation check unsuccessful":
                raise UserError(
                    _("Letter must be in state 'Translation check unsuccessful'"))

            letter.write({
                "kit_identifier": False,
                "resubmit_id": letter.resubmit_id + 1,
                "state": "Received in the system"
            })
            letter.send_local_translate()

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_translation_langs(self):
        """
        Finds the source_language et destination_language suited for
        translation of the given letter.

        S2B:
            - src_lang is the original language of the letter
            - dst_lang is the lang of the child if translatable, else
              english

        B2S:
            - src_lang is the original language if translatable, else
              english
            - dst_lang is the main language of the sponsor
        :return: src_lang, dst_lang
        :rtype: res.lang.compassion, res.lang.compassion
        """
        self.ensure_one()
        src_lang = False
        dst_lang = False
        if self.direction == "Supporter To Beneficiary":
            # Check that the letter is not yet sent to GMC
            if self.kit_identifier:
                raise UserError(
                    _(
                        "Letter already sent to GMC cannot be translated! [%s]"
                    ) % self.kit_identifier
                )

            src_lang = self.original_language_id
            child_langs = self.beneficiary_language_ids.filtered("translatable")
            if child_langs:
                dst_lang = child_langs[-1]
            else:
                dst_lang = self.env.ref("advanced_translation.lang_compassion_english")

        elif self.direction == "Beneficiary To Supporter":
            if self.original_language_id and self.original_language_id.translatable:
                src_lang = self.original_language_id
            else:
                src_lang = self.env.ref("advanced_translation.lang_compassion_english")
            dst_lang = self.supporter_languages_ids.filtered(
                lambda lang: lang.lang_id and lang.lang_id.code == self.partner_id.lang
            )

        return src_lang, dst_lang
