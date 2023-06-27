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
from random import randint

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class Correspondence(models.Model):
    """ This class intercepts a letter before it is sent to GMC.
        Letters are pushed to local translation platform if needed.
        """
    _inherit = "correspondence"

    new_translator_id = fields.Many2one("translation.user", "Local translator")
    src_translation_lang_id = fields.Many2one(
        "res.lang.compassion", "Source of translation", readonly=False
    )
    translation_supervisor_id = fields.Many2one(
        "res.users", "Translation supervisor", domain=[("share", "=", False)])
    translation_competence_id = fields.Many2one(
        "translation.competence", compute="_compute_competence", store=True, inverse="_inverse_competence"
    )
    translate_date = fields.Datetime()
    translate_done = fields.Datetime()
    translation_status = fields.Selection([
        ("to do", "To do"),
        ("in progress", "In progress"),
        ("to validate", "To validate"),
        ("done", "Done")
    ], index=True, group_expand="_read_group_translation_status")
    translation_priority = fields.Selection([
        ("0", "Low"),
        ("1", "Medium"),
        ("2", "High"),
        ("3", "Very high"),
        ("4", "Urgent")
    ], default="0", index=True)
    translation_priority_name = fields.Char(compute="_compute_translation_priority_name", store=True)
    translation_issue = fields.Selection(
        "get_translation_issue_list", help="Issue about the letter reported by the translator")
    translation_issue_comments = fields.Html()
    translation_url = fields.Char(compute="_compute_translation_url")
    unread_comments = fields.Boolean()
    paragraph_ids = fields.One2many(
        "correspondence.paragraph", string="Paragraphs",
        compute="_compute_paragraph_ids", inverse="_inverse_paragraph_ids"
    )

    def _read_group_translation_status(self, values, domain, order):
        return ["to do", "in progress", "to validate", "done"]

    @api.depends("src_translation_lang_id", "translation_language_id")
    def _compute_competence(self):
        for letter in self:
            src = letter.src_translation_lang_id
            dst = letter.translation_language_id
            competence = self.env["translation.competence"].search([
                ("source_language_id", "=", src.id),
                ("dest_language_id", "=", dst.id)])
            letter.translation_competence_id = competence.id

    def _inverse_competence(self):
        for letter in self:
            if letter.translation_status and letter.translation_status != "to do":
                raise UserError(_(
                    "You cannot change the translation language of a letter that is being or already translated."))
            letter.write({
                "src_translation_lang_id": letter.translation_competence_id.source_language_id.id,
                "translation_language_id": letter.translation_competence_id.dest_language_id.id
            })

    @api.depends("translation_priority")
    def _compute_translation_priority_name(self):
        for correspondence in self:
            us_record = correspondence.with_context(lang="en_US")
            correspondence.translation_priority_name = us_record.translate("translation_priority")

    def _compute_translation_url(self):
        host = self.env.ref("sbc_translation.translation_website").sudo().domain
        for letter in self:
            letter.translation_url = f"https://{host}/letters/letter-edit/{letter.id}"

    def _compute_paragraph_ids(self):
        for correspondence in self:
            correspondence.paragraph_ids = correspondence.mapped("page_ids.paragraph_ids")

    def _inverse_paragraph_ids(self):
        # If both deletion and creation is made, creation is not working. I couldn't figure it out...
        for correspondence in self:
            # Propagate deletions
            (correspondence.page_ids.mapped("paragraph_ids") - correspondence.paragraph_ids).unlink()
            # Propagate paragraph creation, we must associate it to a page. We take the last page by default
            last_page = correspondence.page_ids[-1:]
            if not last_page:
                last_page = last_page.create({"correspondence_id": correspondence.id})
            last_sequence = max(last_page.paragraph_ids.mapped("sequence") or [0])
            for new_paragraph in correspondence.paragraph_ids.filtered(lambda p: not p.page_id):
                new_paragraph.sequence = last_sequence + 1
                last_page.paragraph_ids += new_paragraph
                last_sequence += 1

    @api.model
    def get_translation_issue_list(self):
        return [
            ("broken_pdf", _("PDF not showing")),
            ("text_unreadable", _("Cannot read properly")),
            ("wrong_language", _("Letter in wrong language queue")),
            ("child_protection", _("Child protection issue")),
            ("content_inappropriate", _("Inappropriate content")),
            ("wrong_child_name", _("Child name different than expected")),
            ("wrong_sponsor_name", _("Sponsor name different than expected")),
            ("invalid_layout", _("Wrong translation boxes layout")),
            ("other", _("Other issue"))
        ]

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
    def open_full_view(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "views": [[False, "form"]],
            "res_id": self.id,
            "context": {"form_view_ref": "sbc_compassion.view_correspondence_form"}
        }

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
                "translation_priority": str(min((fields.Date.today() - self.scanned_date).days // 7, 4)),
                "translation_status": "to do",
                "translate_date": fields.Datetime.now(),
                "translate_done": False,
                "translation_language_id": dst_lang.id,
                "translation_issue": False,
                "translation_issue_comments": False,
                "unread_comments": False,
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
    def assign_supervisor(self):
        """
        This method assigns a supervisor for a letter.
        Can be inherited to customize by whom the letters need to be checked.
        Here it picks one manager randomly.
        """
        manager_group = self.env.ref("sbc_translation.group_manager")
        admin = self.env.ref("base.user_admin")
        supervisors = self.env["res.users"].sudo().search([("groups_id", "=", manager_group.id)]) - admin
        for letter in self.filtered(lambda l: not l.translation_supervisor_id):
            letter.translation_supervisor_id = supervisors[randint(0, len(supervisors)-1)]
        return True

    @api.multi
    def raise_translation_issue(self, issue_type, body_html):
        """
        TP API for translator to raise an issue with the letter
        """
        self.ensure_one()
        self.write({
            "translation_issue": issue_type,
            "translation_issue_comments": body_html
        })
        self.assign_supervisor()
        # template = self.env.ref("sbc_translation.translation_issue_notification").sudo()
        # self.sudo().message_post_with_template(template.id, author_id=self.env.user.partner_id.id)
        return True

    @api.multi
    def reply_to_comments(self, body_html):
        """
        TP API for sending to the translator a message regarding his or her comments.
        """
        self.ensure_one()
        reply_template = self.env.ref("sbc_translation.comments_reply").sudo()
        self.message_post_with_view(reply_template, partner_ids=[(4, self.new_translator_id.partner_id.id)], values={
            "reply": body_html,
        })
        return self.write({"unread_comments": False})

    @api.multi
    def mark_comments_read(self):
        return self.write({
            "unread_comments": False
        })

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

    @api.multi
    def save_translation(self, letter_elements, translator_id=None):
        """
        TP API for saving a translation
        :param letter_elements: list of dict containing paragraphs or pagebreak data
        :param translator_id: optional translator assigned
        """
        self.ensure_one()
        page_index = 0
        paragraph_index = 0
        current_page = self.page_ids[page_index]
        if translator_id is None:
            translator_id = self.env["translation.user"].search([
                ("user_id", "=", self.env.uid)
            ]).id
        letter_vals = {
            "new_translator_id": translator_id,
            "translation_status": "in progress"
        }
        for element in letter_elements:
            if element.get("type") == "pageBreak":
                page_index += 1
                paragraph_index = 0
                current_page = self.page_ids[page_index]
            elif element.get("type") == "paragraph":
                paragraph_vals = {
                    "page_id": current_page.id,
                    "sequence": paragraph_index,
                    "translated_text": element.get("content"),
                    "comments": element.get("comments")
                }
                current_page.paragraph_ids[paragraph_index].write(paragraph_vals)
                paragraph_index += 1
            if element.get("comments"):
                letter_vals["unread_comments"] = True
        self.write(letter_vals)
        return True

    @api.multi
    def submit_translation(self, letter_elements, translator_id=None):
        """
        TP API for saving a translation
        :param letter_elements: list of dict containing paragraphs or pagebreak data
        :param translator_id: optional translator assigned
        """
        self.ensure_one()
        self.save_translation(letter_elements, translator_id)
        # Make sure the state is correct at this point we had weird issues when submiting whithout saving first
        self.env.cr.commit()
        self.env.clear()
        user_skill = self.new_translator_id.translation_skills.filtered(
            lambda s: s.competence_id == self.translation_competence_id)
        is_s2b = self.direction == "Supporter To Beneficiary"
        if user_skill.verified and not self.unread_comments:
            self.write({
                "translate_done": fields.Datetime.now(),
                "translation_status": "done",
                "state": "Received in the system" if is_s2b else "Published to Global Partner"
            })
            self._post_process_translation()
        else:
            self.translation_status = "to validate"
        return True

    @api.multi
    def approve_translation(self):
        for letter in self:
            skill_to_validate = letter.new_translator_id.translation_skills.filtered(
                lambda s: s.competence_id == letter.translation_competence_id and not s.verified)
            if skill_to_validate:
                skill_to_validate.verified = True
        self.write({
            "translation_issue": False,
            "translation_issue_comments": False,
            "translation_supervisor_id": self.env.uid,
            "translation_status": "done",
        })
        self._post_process_translation()
        return True

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

    @api.multi
    def _post_process_translation(self):
        for letter in self.filtered(lambda l: l.translation_status == "done"):
            if letter.direction == "Supporter To Beneficiary":
                if self.translation_language_id.code_iso == "eng":
                    # Copy translation text into english text field
                    letter.english_text = letter.translated_text
                # Send to GMC
                letter.sudo().create_commkit()
            else:
                # Recompose the letter image and process letter
                if super(Correspondence, letter).process_letter() and hasattr(letter, "send_communication"):
                    letter.sudo().send_communication()

    @api.multi
    def list_letters(self):
        """ API call to fetch letters to translate """
        return [letter.get_letter_info() for letter in self.sorted("scanned_date")]

    @api.multi
    def get_letter_info(self):
        """ Translation Platform API for fetching letter data. """
        self.ensure_one()
        base_url = request.httprequest.host_url or \
            f"https://{self.env.ref('sbc_translation.translation_website').domain}/"
        # Gives access to related objects
        child = self.child_id.sudo()
        partner = self.partner_id.sudo()
        return {
            "id": self.id,
            "status": self.translate("translation_issue") or self.translate("translation_status") or "None",
            "priority": self.translation_priority or "0",
            "title": self.sudo().name,
            "source": self.src_translation_lang_id.name,
            "target": self.translation_language_id.name,
            "unreadComments": self.unread_comments,
            "translatorId": self.new_translator_id.id or "None",
            "lastUpdate": fields.Datetime.to_string(self.write_date),
            "date": fields.Date.to_string(self.scanned_date),
            "translatedElements": self.get_translated_elements() or "None",
            "translationIssue": self.translation_issue,
            "child": {
                "preferredName": child.preferred_name,
                "fullName": child.name,
                "sex": child.gender,
                "age": child.age,
                "ref": child.local_id
            },
            "sponsor": {
                "preferredName": partner.preferred_name,
                "fullName": partner.name,
                "sex": partner.gmc_gender[0],
                "age": partner.age,
                "ref": partner.ref
            },
            "pdfUrl": f"{base_url}b2s_image?id={self.uuid}&disposition=inline",
        }

    @api.multi
    def get_translated_elements(self):
        res = []
        for page in self.page_ids:
            if res:
                res.append({
                    "type": "pageBreak",
                    "id": page.id,
                })
            for paragraph in page.paragraph_ids:
                res.append({
                    "type": "paragraph",
                    "id": paragraph.id,
                    "content": paragraph.translated_text,
                    "comments": paragraph.comments,
                    "source": paragraph.english_text or paragraph.original_text or "",
                })
        return res

    @api.model
    def increment_priority_cron(self):
        """
        Increment priority of letters to translate, maximum
        priority is 4.
        """
        letters_to_translate = self.search([("translation_status", "not in", [False, "done"])])

        for letter in letters_to_translate:
            old_priority = int(letter.translation_priority)
            if old_priority < 4:
                letter.translation_priority = str(old_priority + 1)
            elif letter.translation_competence_id.fallback_competence_id:
                letter.with_delay().move_pool()

    def move_pool(self):
        """
        Move letter to another common translation pool. This is helpful when a letter is stuck for too long
        inside a pool, and we want to move it to another one that has more translator resources.
        """
        self.ensure_one()
        if self.translation_competence_id.fallback_competence_id and self.translation_status == "to do":
            self.translation_competence_id = self.translation_competence_id.fallback_competence_id

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
