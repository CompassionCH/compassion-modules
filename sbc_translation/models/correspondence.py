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
import json
import datetime
from random import randint
from difflib import SequenceMatcher

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.http import request

import xml.etree.ElementTree as ET

_logger = logging.getLogger(__name__)


class Correspondence(models.Model):
    """This class intercepts a letter before it is sent to GMC.
    Letters are pushed to local translation platform if needed.
    """

    _inherit = "correspondence"

    new_translator_id = fields.Many2one("translation.user", "Local translator")
    src_translation_lang_id = fields.Many2one(
        "res.lang.compassion", "Source of translation", readonly=False
    )
    translation_supervisor_id = fields.Many2one(
        "res.users", "Translation supervisor", domain=[("share", "=", False)]
    )
    translation_competence_id = fields.Many2one(
        "translation.competence",
        compute="_compute_competence",
        store=True,
        inverse="_inverse_competence",
    )
    translate_date = fields.Datetime()
    translate_done = fields.Datetime()
    translation_status = fields.Selection(
        [
            ("to do", "To do"),
            ("in progress", "In progress"),
            ("to validate", "To validate"),
            ("done", "Done"),
        ],
        index=True,
        group_expand="_read_group_translation_status",
    )
    translation_priority = fields.Selection(
        [
            ("0", "Low"),
            ("1", "Medium"),
            ("2", "High"),
            ("3", "Very high"),
            ("4", "Urgent"),
        ],
        default="0",
        index=True,
    )
    translation_priority_name = fields.Char(
        compute="_compute_translation_priority_name", store=True
    )
    translation_issue = fields.Selection(
        "get_translation_issue_list",
        help="Issue about the letter reported by the translator",
    )
    translation_issue_comments = fields.Html()
    translation_url = fields.Char(compute="_compute_translation_url")
    unread_comments = fields.Boolean()
    paragraph_ids = fields.One2many(
        "correspondence.paragraph",
        string="Paragraphs",
        compute="_compute_paragraph_ids",
        inverse="_inverse_paragraph_ids",
    )

    def _read_group_translation_status(self, values, domain, order):
        return ["to do", "in progress", "to validate", "done"]

    @api.depends("src_translation_lang_id", "translation_language_id")
    def _compute_competence(self):
        for letter in self:
            src = letter.src_translation_lang_id
            dst = letter.translation_language_id
            competence = self.env["translation.competence"].search(
                [("source_language_id", "=", src.id), ("dest_language_id", "=", dst.id)]
            )
            letter.translation_competence_id = competence.id

    def _inverse_competence(self):
        for letter in self:
            if letter.translation_status and letter.translation_status != "to do":
                raise UserError(
                    _(
                        "You cannot change the translation language of a letter that is being or already translated."
                    )
                )
            letter.write(
                {
                    "src_translation_lang_id": letter.translation_competence_id.source_language_id.id,
                    "translation_language_id": letter.translation_competence_id.dest_language_id.id,
                }
            )

    @api.depends("translation_priority")
    def _compute_translation_priority_name(self):
        for correspondence in self:
            us_record = correspondence.with_context(lang="en_US")
            correspondence.translation_priority_name = us_record.translate(
                "translation_priority"
            )

    def _compute_translation_url(self):
        host = self.env.ref("sbc_translation.translation_website").sudo().domain
        for letter in self:
            letter.translation_url = f"https://{host}/letters/letter-edit/{letter.id}"

    def _compute_paragraph_ids(self):
        for correspondence in self:
            correspondence.paragraph_ids = correspondence.mapped(
                "page_ids.paragraph_ids"
            )

    def _inverse_paragraph_ids(self):
        # If both deletion and creation is made, creation is not working. I couldn't figure it out...
        for correspondence in self:
            # Propagate deletions
            (
                correspondence.page_ids.mapped("paragraph_ids")
                - correspondence.paragraph_ids
            ).unlink()
            # Propagate paragraph creation, we must associate it to a page. We take the last page by default
            last_page = correspondence.page_ids[-1:]
            if not last_page:
                last_page = last_page.create({"correspondence_id": correspondence.id})
            last_sequence = max(last_page.paragraph_ids.mapped("sequence") or [0])
            for new_paragraph in correspondence.paragraph_ids.filtered(
                lambda p: not p.page_id
            ):
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
            ("other", _("Other issue")),
        ]

    @api.onchange("new_translator_id")
    def onchange_new_translator_id(self):
        """
        When a translator is set, the letter should always be on "in progress" status to ensure that the letter can
        be found under the translator's saved letters in the Translation Platform.
        """
        if self.new_translator_id:
            self.translation_status = "in progress"

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """Create a message for sending the CommKit after be translated on
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
    def open_full_view(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "views": [[False, "form"]],
            "res_id": self.id,
            "context": {"form_view_ref": "sbc_compassion.view_correspondence_form"},
        }

    def process_letter(self):
        """Called when B2S letter is Published. Check if translation is
        needed and upload to translation platform."""
        for letter in self:
            if (
                (letter.beneficiary_language_ids & letter.supporter_languages_ids)
                or letter.has_valid_language
                or self.env.context.get("force_publish")
            ):
                super(Correspondence, letter).process_letter()
            else:
                letter.download_attach_letter_image()
                letter.send_local_translate()
        return True

    def calculate_translation_priority(self):
        """
        Calculate the translation priority based on the scanned date or creation date.
        :return: string
        """

        # Dynamically get the list of priority keys from the selection field definition
        priorities = [
            int(priority[0])
            for priority in self._fields["translation_priority"].selection
        ]

        # Handle the case where scanned_date is not set
        letter_date = (
            self.scanned_date if self.scanned_date else self.create_date.date()
        )

        # Calculate the difference in weeks between the current date and the scanned date.
        calculated_priority = min(
            (fields.Date.today() - letter_date).days // 7, len(priorities) - 1
        )

        # If the user had manually set a higher priority, we stick to it
        if (
            self.translation_priority
            and int(self.translation_priority) >= calculated_priority
        ):
            return self.translation_priority

        return str(calculated_priority)

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
                "translation_priority": self.calculate_translation_priority(),
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
        self.env["gmc.message"].search(
            [
                ("action_id", "=", self.env.ref("sbc_compassion.create_letter").id),
                ("object_id", "=", self.id),
                ("state", "!=", "success"),
            ]
        ).unlink()
        return True

    def assign_supervisor(self):
        """
        This method assigns a supervisor for a letter.
        Can be inherited to customize by whom the letters need to be checked.
        Here it picks one manager randomly.
        """
        manager_group = self.env.ref("sbc_translation.group_manager")
        admin = self.env.ref("base.user_admin")
        supervisors = (
            self.env["res.users"].sudo().search([("groups_id", "=", manager_group.id)])
            - admin
        )
        for letter in self.filtered(lambda l: not l.translation_supervisor_id):
            letter.translation_supervisor_id = supervisors[
                randint(0, len(supervisors) - 1)
            ]
        return True

    def raise_translation_issue(self, issue_type, body_html):
        """
        TP API for translator to raise an issue with the letter
        """
        self.ensure_one()

        self.write(
            {"translation_issue": issue_type, "translation_issue_comments": body_html}
        )
        self.assign_supervisor()

        html = self.env["ir.qweb"]._render(
            "sbc_translation.translation_issue_log", {"record": self}
        )

        self._message_log(body=html)

        return True

    def reply_to_comments(self, body_html):
        """
        TP API for sending to the translator a message regarding his or her comments.
        """
        self.ensure_one()
        reply_template = self.env.ref("sbc_translation.comments_reply").sudo()
        self.message_post_with_view(
            reply_template,
            partner_ids=[(4, self.new_translator_id.partner_id.id)],
            values={
                "reply": body_html,
            },
        )
        return self.write({"unread_comments": False})

    def reply_to_issue(self, body_html):
        """
        TP API for sending to the translator a message regarding his issue.
        """
        self.ensure_one()
        reply_template = self.env.ref("sbc_translation.issue_reply").sudo()
        self.message_post_with_view(
            reply_template,
            partner_ids=[(4, self.new_translator_id.partner_id.id)],
            values={
                "reply": body_html,
            },
        )
        return self.write(
            {"translation_issue": False, "translation_issue_comments": False}
        )

    def mark_comments_read(self):
        return self.write({"unread_comments": False})

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
        comments_updates = []
        if not translator_id:
            # Don't overwrite current translator if any.
            if self.new_translator_id:
                translator_id = self.new_translator_id
            else:
                translator_id = (
                    self.env["translation.user"]
                    .search([("user_id", "=", self.env.uid)])
                    .id
                )
        letter_vals = {
            "new_translator_id": translator_id,
            "translation_status": "in progress",
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
                    "comments": element.get("comments"),
                }
                if self.translation_language_id.code_iso == "eng":
                    # Copy translation text into english text field
                    paragraph_vals["english_text"] = element.get("content")

                if (
                    current_page.paragraph_ids[paragraph_index].comments
                    != paragraph_vals["comments"]
                ):
                    comments_updates.append(
                        {
                            "page_index": page_index + 1,
                            "paragraph_index": paragraph_index + 1,
                            "old": current_page.paragraph_ids[paragraph_index].comments,
                            "new": paragraph_vals["comments"],
                        }
                    )

                current_page.paragraph_ids[paragraph_index].write(paragraph_vals)
                paragraph_index += 1
            if element.get("comments"):
                letter_vals["unread_comments"] = True

        if len(comments_updates) > 0:
            # Don't fail the update for a chatter issue.
            try:
                self._update_or_add_chatter_comments(comments_updates)
            except Exception as e:
                _logger.error("Failed to post chatter message")

        self.write(letter_vals)
        return True

    def _update_or_add_chatter_comments(self, comments_updates):
        self.ensure_one()

        # Don't merge a message after this many hours.
        message_merge_max_elapsed_time_hours = 4
        # Force merge if the elapsed time since last update is smaller than this many
        # seconds.
        message_force_merge_max_elapsed_time_seconds = 30

        # Don't filter by user_id or time here to keep order and not merge if someone
        # else edited since last chatter update.
        last_message = self.env["mail.message"].search(
            [
                ("res_id", "=", self.id),
                ("model", "=", self._name),
            ],
            order="create_date DESC",
            limit=1,
        )

        merged_updates = None
        if (
            last_message
            and last_message.create_uid.id == self.env.user.id
            and last_message.write_date
            + datetime.timedelta(hours=message_merge_max_elapsed_time_hours)
            > datetime.datetime.now()
        ):
            last_message_data = self._get_update_message_data(last_message)
            if last_message_data is not None:
                force_merge = (
                    last_message.write_date
                    + datetime.timedelta(
                        seconds=message_force_merge_max_elapsed_time_seconds
                    )
                    > datetime.datetime.now()
                )
                merged_updates = self._merge_comment_updates(
                    last_message_data, comments_updates, force_merge
                )
                if merged_updates is not None:
                    comments_updates = merged_updates

        html = self.env["ir.qweb"]._render(
            "sbc_translation.translation_comments_update",
            {"comments": comments_updates, "json": json.dumps(comments_updates)},
        )

        if merged_updates is not None:
            last_message.update({"body": html})
        else:
            self._message_log(body=html)

    @api.model
    def _merge_comment_updates(self, last_updates, new_updates, force_merge=False):
        def are_same_paragraph(update1, update2):
            return (
                update1["page_index"] == update2["page_index"]
                and update1["paragraph_index"] == update2["paragraph_index"]
            )

        merge_min_similarity = 0.8

        merged_updates = []
        for new_update in new_updates:
            old_update = next(
                (
                    update
                    for update in last_updates
                    if are_same_paragraph(update, new_update)
                ),
                None,
            )

            # New update.
            if old_update is None:
                merged_updates.append(new_update)

            elif (
                force_merge
                or
                # Only added content, no information lost.
                old_update["new"] in new_update["new"]
                or
                # Minor insertion/deletion
                SequenceMatcher(None, old_update["new"], new_update["new"]).ratio()
                > merge_min_similarity
            ):
                merged_updates.append({**old_update, "new": new_update["new"]})

            # Merge failed. We need a new message.
            else:
                return None

        # Add old paragraph updates which weren't changed to the new message
        for old_update in last_updates:
            if not any(
                update
                for update in merged_updates
                if are_same_paragraph(old_update, update)
            ):
                merged_updates.append(old_update)

        return sorted(
            merged_updates, key=lambda u: u["page_index"] * 1000 + u["paragraph_index"]
        )

    @api.model
    def _get_update_message_data(self, update_message):
        if (
            update_message
            and update_message.body
            and update_message.message_type == "notification"
        ):
            try:
                lm_tree = ET.fromstring(update_message.body)
            except ET.ParseError as e:
                _logger.warning("Failed to parse message")
                return None

            if lm_tree.get("class") == "translation-comments-update":
                json_elem = lm_tree.find("span")
                if json_elem is not None:
                    last_update_txt = json_elem.text
                    if last_update_txt:
                        last_updates = json.loads(last_update_txt)
                        if isinstance(last_updates, list):
                            return last_updates

    def submit_translation(self, letter_elements, translator_id=None):
        """
        TP API for saving a translation
        :param letter_elements: list of dict containing paragraphs or pagebreak data
        :param translator_id: optional translator assigned
        """
        self.ensure_one()
        self.save_translation(letter_elements, translator_id)
        user_skill = self.new_translator_id.translation_skills.filtered(
            lambda s: s.competence_id == self.translation_competence_id
        )
        if user_skill.verified and not self.unread_comments:
            self._post_process_translation()
        else:
            self.translation_status = "to validate"
        return True

    def approve_translation(self):
        for letter in self:
            skill_to_validate = letter.new_translator_id.translation_skills.filtered(
                lambda s: s.competence_id == letter.translation_competence_id
                and not s.verified
            )
            if skill_to_validate:
                skill_to_validate.verified = True
        self.write(
            {
                "translation_issue": False,
                "translation_issue_comments": False,
                "translation_supervisor_id": self.env.uid,
                "unread_comments": False,
            }
        )
        self._post_process_translation()
        return True

    def resubmit_to_translation(self):
        for letter in self:
            if letter.state != "Translation check unsuccessful":
                raise UserError(
                    _("Letter must be in state 'Translation check unsuccessful'")
                )

            letter.write(
                {
                    "kit_identifier": False,
                    "resubmit_id": letter.resubmit_id + 1,
                    "state": "Received in the system",
                }
            )
            letter.send_local_translate()

    def _post_process_translation(self):
        self.ensure_one()
        is_s2b = self.direction == "Supporter To Beneficiary"
        self.write(
            {
                "translate_done": fields.Datetime.now(),
                "translation_status": "done",
                "state": "Received in the system"
                if is_s2b
                else "Published to Global Partner",
            }
        )
        if is_s2b:
            # Send to GMC
            self.sudo().create_commkit()
        else:
            # Recompose the letter image
            self.compose_letter_button()

    def list_letters(self):
        """API call to fetch letters to translate"""
        return [letter.get_letter_info() for letter in self.sorted("scanned_date")]

    def get_letter_info(self):
        """Translation Platform API for fetching letter data."""
        self.ensure_one()
        base_url = (
            request.httprequest.host_url
            or f"https://{self.env.ref('sbc_translation.translation_website').domain}/"
        )
        # Gives access to related objects
        child = self.child_id.sudo()
        partner = self.partner_id.sudo()
        return {
            "id": self.id,
            "status": self.translate("translation_issue")
            or self.translate("translation_status")
            or "None",
            "priority": self.translation_priority
            or self._fields["translation_priority"].selection[0][0],
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
                "ref": child.local_id,
            },
            "sponsor": {
                "preferredName": partner.preferred_name,
                "fullName": partner.name,
                "sex": partner.title.name,
                "age": partner.age,
                "ref": partner.ref,
            },
            "pdfUrl": f"{base_url}b2s_image?id={self.uuid}&disposition=inline",
        }

    def get_translated_elements(self):
        res = []
        for i, page in enumerate(self.page_ids):
            for paragraph in page.paragraph_ids:
                res.append(
                    {
                        "type": "paragraph",
                        "id": paragraph.id,
                        "content": paragraph.translated_text,
                        "comments": paragraph.comments,
                        "source": paragraph.english_text
                        or paragraph.original_text
                        or "",
                    }
                )
            if i < len(self.page_ids) - 1:
                res.append(
                    {
                        "type": "pageBreak",
                        "id": page.id,
                    }
                )
        return res

    @api.model
    def update_translation_priority_cron(self):
        """
        Update the priority of letters to translate if the letter is not already at the highest priority.
        When the letter is already at the highest priority, it moves it to another suitable pool.
        :return: None
        """
        letters_to_translate = self.search(
            [("translation_status", "not in", [False, "done"])]
        )

        # Update priority for each letters
        for letter in letters_to_translate:
            current_priority = letter.translation_priority
            new_priority = letter.calculate_translation_priority()

            if current_priority != new_priority:
                letter.translation_priority = new_priority

            # If the letter is already at the highest priority and has a fallback competence, move it to another pool
            elif letter.translation_competence_id.fallback_competence_id:
                letter.with_delay().move_pool()

    def move_pool(self):
        """
        Move letter to another common translation pool. This is helpful when a letter is stuck for too long
        inside a pool, and we want to move it to another one that has more translator resources.
        """
        self.ensure_one()
        if (
            self.translation_competence_id.fallback_competence_id
            and self.translation_status == "to do"
        ):
            self.translation_competence_id = (
                self.translation_competence_id.fallback_competence_id
            )

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
                    _("Letter already sent to GMC cannot be translated! [%s]")
                    % self.kit_identifier
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
