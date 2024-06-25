##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging
from datetime import datetime
from functools import reduce

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

from odoo.addons.sbc_compassion.models.correspondence import DEFAULT_LETTER_DPI
from odoo.addons.sbc_compassion.models.correspondence_page import (
    BOX_SEPARATOR,
    PAGE_SEPARATOR,
)

_logger = logging.getLogger(__name__)


PHYSICAL_LETTER_DPI = 300


class Correspondence(models.Model):
    _inherit = "correspondence"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    letter_delivery_preference = fields.Selection(
        related="partner_id.letter_delivery_preference"
    )
    communication_id = fields.Many2one(
        "partner.communication.job", "Communication", readonly=False
    )
    email_id = fields.Many2one(
        "mail.mail",
        "E-mail",
        related="communication_id.email_id",
        store=True,
        index=True,
        readonly=False,
    )
    communication_state = fields.Selection(related="communication_id.state")
    sent_date = fields.Datetime(
        "Communication sent",
        related="communication_id.sent_date",
        store=True,
        tracking=True,
    )
    zip_file = fields.Binary()
    has_valid_language = fields.Boolean(compute="_compute_valid_language", store=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_letter_format(self):
        """Letter is zip if it contains a zip attachment"""
        for letter in self:
            if letter.zip_file:
                letter.letter_format = "zip"
            else:
                super(Correspondence, letter)._compute_letter_format()

    @api.depends(
        "supporter_languages_ids",
        "page_ids",
        "page_ids.translated_text",
        "translation_language_id",
    )
    def _compute_valid_language(self):
        """Detect if text is written in the language corresponding to the
        language_id"""
        for letter in self:
            letter.has_valid_language = False
            if letter.translated_text and letter.translation_language_id:
                s = (
                    letter.translated_text.strip(" \t\n\r.")
                    .replace(BOX_SEPARATOR, "")
                    .replace(PAGE_SEPARATOR, "")
                )
                if s:
                    # find the language of text argument
                    lang = self.env["langdetect"].detect_language(
                        letter.translated_text
                    )
                    letter.has_valid_language = (
                        lang and lang in letter.supporter_languages_ids
                    )

    def _compute_preferred_dpi(self):
        """Compute DPI based on letter delivery preference"""
        for letter in self:
            letter.preferred_dpi = (
                DEFAULT_LETTER_DPI
                if "digital" in letter.letter_delivery_preference and letter.email
                else PHYSICAL_LETTER_DPI
            )

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    def get_image(self):
        """Method for retrieving the image"""
        self.ensure_one()
        if self.zip_file:
            data = base64.b64decode(self.zip_file)
        else:
            data = super().get_image()
        return data

    def attach_zip(self):
        """
        When a partner gets multiple letters, we make a zip and attach it
        to the first letter, so that he can only download this zip.
        :return: True
        """
        if len(self) > 5:
            _zip = (
                self.env["correspondence.download.wizard"]
                .with_context(active_model=self._name, active_ids=self.ids)
                .create({})
            )
            _zip.get_letters()
            self.write({"zip_file": False})
            letter_attach = self[:1]
            letter_attach.write(
                {"zip_file": _zip.download_data, "letter_format": "zip"}
            )
            base_url = (
                self.env["ir.config_parameter"].sudo().get_param("web.external.url")
            )
            self.write({"read_url": f"{base_url}/b2s_image?id={letter_attach.uuid}"})
        return True

    def compose_letter_image(self):
        """
        Regenerate communication if already existing
        """
        res = super().compose_letter_image()
        if self.communication_id:
            self.communication_id.refresh_text()
        return res

    def process_letter(self):
        # Prepare the communication when a letter is published
        res = super().process_letter()
        intro_letter = self.env.ref("sbc_compassion.correspondence_type_new_sponsor")
        skip = self.filtered(
            lambda letter: not letter.letter_image
            or (
                intro_letter in letter.communication_type_ids
                and not letter.sponsorship_id.send_introduction_letter
            )
        )
        (self - skip).send_communication()
        return res

    def send_communication(self):
        """
        Sends the communication to the partner. By default it won't do
        anything if a communication is already attached to the letter.
        Context can contain following settings :
            - comm_vals : dictionary for communication values
            - force_send : will send the communication regardless of the
                           settings.
            - overwrite : will force the communication creation even if one
                          already exists.
        :return: True
        """
        # We shouldn't send communication to terminated contracts
        # We should also delete pending communication for those terminated contracts
        final_letter = self.env.ref("sbc_compassion.correspondence_type_final")
        if self.env.context.get("force_send"):
            eligible_letters = self
        else:
            eligible_letters = self.filtered(
                lambda letter: letter.sponsorship_id.state == "active"
                or final_letter in letter.communication_type_ids
            )
            (self - eligible_letters).mapped("communication_id").filtered(
                lambda c: c.state != "done"
            ).unlink()

        partners = eligible_letters.mapped("partner_id")
        module = "partner_communication_compassion."
        first_letter_template = self.env.ref(module + "config_onboarding_first_letter")
        final_template = self.env.ref(module + "child_letter_final_config")
        new_template = self.env.ref(module + "child_letter_config")
        old_template = self.env.ref(module + "child_letter_old_config")
        old_limit = datetime.today() - relativedelta(months=2)

        for partner in partners:
            letters = eligible_letters.filtered(
                lambda letter, partner=partner: letter.partner_id == partner
            )
            is_first = eligible_letters.filtered(
                lambda letter: letter.communication_type_ids
                == self.env.ref("sbc_compassion.correspondence_type_new_sponsor")
            )
            no_comm = letters.filtered(lambda letter: not letter.communication_id)
            to_generate = letters if self.env.context.get("overwrite") else no_comm

            final_letters = to_generate.filtered(
                lambda letter: final_letter in letter.communication_type_ids
            )
            new_letters = to_generate - final_letters
            old_letters = new_letters.filtered(
                lambda letter: letter.create_date < old_limit
            )
            new_letters -= old_letters

            final_letters._generate_communication(final_template)
            new_letters._generate_communication(
                first_letter_template if is_first else new_template
            )
            old_letters._generate_communication(
                first_letter_template if is_first else old_template
            )
        if self.env.context.get("force_send"):
            eligible_letters.mapped("communication_id").filtered(
                lambda c: c.state != "done"
            ).send()
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _generate_communication(self, config):
        """
        Generates the communication for given letters.
        :param config_id: partner.communication.config id
        :return: True
        """
        if not self or not config.active:
            return True

        partner = self.mapped("partner_id")
        auto_send = [letter._can_auto_send() for letter in self]
        auto_send = reduce(lambda l1, l2: l1 and l2, auto_send) and (
            "auto" in config.send_mode
            or config.send_mode in ["partner_preference", "both"]
        )
        comm_vals = {
            "partner_id": partner.id,
            "config_id": config.id,
            "object_ids": self.ids,
            "auto_send": auto_send and partner.email,  # Don't print auto
        }

        if "comm_vals" in self.env.context:
            comm_vals.update(self.env.context["comm_vals"])

        comm_obj = self.env["partner.communication.job"]
        return self.write({"communication_id": comm_obj.create(comm_vals).id})

    def _can_auto_send(self):
        """Tells if we can automatically send the letter by e-mail or should
        require manual validation before.
        """
        self.ensure_one()
        partner_langs = self.supporter_languages_ids
        types = self.communication_type_ids.mapped("name")
        valid = (
            self.sponsorship_id.state == "active"
            and "Final Letter" not in types
            and "auto" in self.partner_id.letter_delivery_preference
        )
        if not (partner_langs & self.beneficiary_language_ids):
            valid &= self.has_valid_language

        return valid
