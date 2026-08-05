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

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Correspondence(models.Model):
    """This class intercepts a letter before it is sent to GMC.
    Letters are pushed to local translation platform if needed.
    """

    _inherit = "correspondence"

    new_translator_id = fields.Many2one(
        "translation.user", "Local translator", tracking=True
    )
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
        tracking=True,
    )
    translate_date = fields.Datetime(tracking=True)
    translate_done = fields.Datetime(tracking=True)
    translation_status = fields.Selection(
        [
            ("to do", "To do"),
            ("in progress", "In progress"),
            ("to validate", "To validate"),
            ("done", "Done"),
        ],
        index=True,
        group_expand="_read_group_translation_status",
        tracking=True,
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
        tracking=True,
    )
    translation_priority_name = fields.Char(
        compute="_compute_translation_priority_name", store=True
    )
    translation_issue = fields.Selection(
        "get_translation_issue_list",
        help="Issue about the letter reported by the translator",
        tracking=True,
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

    @api.model
    def _read_group_translation_status(self, statuses, domain, order):
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
                        "You cannot change the translation language of a letter that is"
                        " being or already translated."
                    )
                )
            competence = letter.translation_competence_id
            letter.with_context(skip_lang_detect=True).write(
                {
                    "src_translation_lang_id": competence.source_language_id.id,
                    "translation_language_id": competence.dest_language_id.id,
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
        """Build the link translators click to open this letter in
        the webapp.

        The base URL is read from the system parameter
        `sbc_translation.webapp_base_url`. If unset, the webapp is
        assumed to be served by Odoo itself at `/translation-platform`
        (see `controllers/main.py`), and the link falls back to
        `<web.base.url>/translation-platform`.

        Set the parameter to point at an external host
        (e.g. `http://localhost:5173` for `npm run dev`) when the
        webapp is not served by Odoo.
        """
        icp = self.env["ir.config_parameter"].sudo()
        webapp_url = icp.get_param("sbc_translation.webapp_base_url")
        if not webapp_url:
            base_url = icp.get_param("web.base.url", "").rstrip("/")
            webapp_url = f"{base_url}/translation-platform"
        webapp_url = webapp_url.rstrip("/")
        for letter in self:
            letter.translation_url = f"{webapp_url}/letters/letter-edit/{letter.id}"

    def _compute_paragraph_ids(self):
        for correspondence in self:
            correspondence.paragraph_ids = correspondence.mapped(
                "page_ids.paragraph_ids"
            )

    def _inverse_paragraph_ids(self):
        # If both deletion and creation is made, creation is not working.
        # I couldn't figure it out...
        for correspondence in self:
            # Propagate deletions
            (
                correspondence.page_ids.mapped("paragraph_ids")
                - correspondence.paragraph_ids
            ).unlink()
            # Propagate paragraph creation, we must associate it to a page.
            # We take the last page by default
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
        When a translator is set, the letter should always be on "in progress"
        status to ensure that the letter can
        be found under the translator's saved letters in the Translation Platform.
        """
        if self.new_translator_id:
            self.translation_status = "in progress"

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model_create_multi
    def create(self, vals_list):
        """Create a message for sending the CommKit after be translated on
        the local translate platform.
        """
        b2s_vals = []
        s2b_vals = []
        for vals in vals_list:
            if vals.get("direction") == "Beneficiary To Supporter":
                b2s_vals.append(vals)
            else:
                s2b_vals.append(vals)

        res = self.env["correspondence"]

        if b2s_vals:
            res += super().create(b2s_vals)

        if s2b_vals:
            # create letter first and let super.create()
            # run the language detection first
            s2b_records = super(
                Correspondence, self.with_context(no_comm_kit=True)
            ).create(s2b_vals)
            res += s2b_records

            for correspondence in s2b_records:
                sponsorship = correspondence.sponsorship_id
                original_lang = correspondence.original_language_id

                # Languages the office/region understand
                office = sponsorship.child_id.project_id.field_office_id
                language_ids = (
                    office.spoken_language_ids + office.translated_language_ids
                )

                if original_lang.translatable and original_lang not in language_ids:
                    correspondence.action_send_local_translate()
                else:
                    # if no translation is needed, resume GMC dispatch
                    correspondence.create_commkit()

        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def action_open_full_view(self):
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
            force_publish = letter.env.context.get("force_publish")

            # Update language detection if not forced
            if not force_publish:
                letter._check_translation_language()

            # Can sponser read the letter? Decide from the letter's ACTUAL
            # content language, not the field-office TranslationLanguage stamp.
            # If it can't be determined, fail safe to translation.
            detected_lang = letter._detect_letter_language()
            langs_match = (
                bool(detected_lang) and detected_lang in letter.supporter_languages_ids
            )

            # Is the letter still in the translation process?
            translation_hold = (
                letter.translation_status in ["to do", "in progress", "to validate"]
                or letter.translation_issue
            )

            if (langs_match and not translation_hold) or force_publish:
                super(Correspondence, letter).process_letter()
            else:
                try:
                    letter.download_attach_letter_image()
                except UserError:
                    _logger.warning(
                        f"Could not download image for letter {letter.id}, "
                        f"but proceeding to translation queue."
                    )
                # (re)send to translation queue ONLY if not on hold
                if not translation_hold:
                    letter.action_send_local_translate()
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

        # Calculate the difference in weeks between
        # the current date and the scanned date.
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

    def action_send_local_translate(self, resubmit=False):
        """
        Sends the letter to the local translation platform.
        :return: None
        """
        self.ensure_one()
        # Check if resubmit is passed through the context.
        if not resubmit:
            resubmit = self.env.context.get("resubmit")

        # Specify the src and dst language
        src_lang, dst_lang = self._get_translation_langs()

        self.with_context(skip_lang_detect=True).write(
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
                "new_translator_id": False,
            }
        )
        if not resubmit:
            self.mapped("page_ids.paragraph_ids").with_context(
                skip_lang_detect=True
            ).write({"translated_text": ""})

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
        for letter in self.filtered(
            lambda _letter: not _letter.translation_supervisor_id
        ):
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
        self.message_post_with_source(
            reply_template,
            partner_ids=[self.new_translator_id.partner_id.id],
            render_values={"reply": body_html},
            subtype_xmlid="mail.mt_note",
        )
        return self.write({"unread_comments": False})

    def reply_to_issue(self, body_html):
        """
        TP API for sending to the translator a message regarding his issue.
        """
        self.ensure_one()
        reply_template = self.env.ref("sbc_translation.issue_reply").sudo()
        translator_group = self.env.ref("sbc_translation.group_user")
        partner = self.mapped("message_ids.author_id").filtered(
            lambda p: any(p.user_ids.mapped("share"))
            and translator_group in p.user_ids.mapped("groups_id")
        )
        if partner:
            self.message_post_with_source(
                reply_template,
                partner_ids=[partner[0].id],
                render_values={
                    "reply": body_html,
                },
                subtype_xmlid="mail.mt_note",
            )
        return self.write(
            {"translation_issue": False, "translation_issue_comments": False}
        )

    def mark_comments_read(self):
        return self.write({"unread_comments": False})

    def action_remove_local_translate(self):
        """
        Remove a letter from local translation platform and change state of
        letter in Odoo without triggering automated publishing or emails.
        :return: bool
        """
        self.ensure_one()

        # Reset both B2S and S2B to a clean neutral state and clear translation metadata
        self.write(
            {
                "state": "Received in the system",
                "translator": False,
                "new_translator_id": False,
                "translation_status": False,
            }
        )

        # Only S2B requires internal kit bundling
        if self.direction == "Supporter To Beneficiary":
            self.create_commkit()

        return True

    def save_translation(self, letter_elements, translator_id=None, submit=False):
        """
        TP API for saving a translation
        :param letter_elements: list of dict containing paragraphs or pagebreak data
        :param translator_id: optional translator assigned
        :param submit: if True, the translation will be submitted after saving
        """
        _logger.info(
            "Saving translation for letter %s and translator %s", self.id, translator_id
        )
        self.ensure_one()
        if self.translation_status == "to validate":
            _logger.warning(
                "Invalid save translation call on letter."
                "The letter is already submitted."
            )
            return True
        page_index = 0
        paragraph_index = 0
        current_page = self.page_ids[page_index].with_context(skip_lang_detect=True)
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
        }
        if not submit:
            letter_vals["translation_status"] = "in progress"

        for element in letter_elements:
            if element.get("type") == "pageBreak":
                page_index += 1
                paragraph_index = 0
                current_page = self.page_ids[page_index].with_context(
                    skip_lang_detect=True
                )
            elif element.get("type") == "paragraph":
                paragraph_vals = {
                    "page_id": current_page.id,
                    "sequence": paragraph_index,
                    "translated_text": element.get("content"),
                    "comments": element.get("comments"),
                }
                if self.translation_language_id.code_iso == "eng":
                    # Move translation text into english text field
                    paragraph_vals["english_text"] = paragraph_vals.pop(
                        "translated_text"
                    )

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
            html = self.env["ir.qweb"]._render(
                "sbc_translation.translation_comments_update",
                {"comments": comments_updates},
            )

            self._message_log(body=html)

        self.write(letter_vals)
        _logger.info("Translation saved.")
        return True

    def submit_translation(self, letter_elements, translator_id=None) -> bool:
        """
        TP API for saving a translation
        :param letter_elements: list of dict containing paragraphs or pagebreak data
        :param translator_id: optional translator assigned
        """
        _logger.info(
            "Submitting translation for letter %s and translator %s",
            self.id,
            translator_id,
        )
        self.ensure_one()
        self.save_translation(letter_elements, translator_id, submit=True)
        user_skill = self.new_translator_id.translation_skills.filtered(
            lambda s: s.competence_id == self.translation_competence_id
        )

        validation_needed: bool = (
            not user_skill.verified  # user skill not verified
            or self.unread_comments  # there are unread comments
            or self.new_translator_id.force_validation  # validation is forced
        )

        if validation_needed:
            self.translation_status = "to validate"
        else:
            self._post_process_translation()
        _logger.info("Translation submitted.")
        return True

    def action_approve_translation(self):
        """Manager-side approval of a letter in `to validate` status.

        Marks the translator's skill for this letter's competence as
        verified (if not already), clears any reported translation
        issue, records the current user as supervisor, and runs the
        post-processing step that ships the letter on.
        """
        for letter in self:
            skill_to_validate = letter.new_translator_id.translation_skills.filtered(
                lambda s, _letter=letter: s.competence_id
                == _letter.translation_competence_id
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

    def action_resubmit_to_translation(self):
        for letter in self:
            if letter.direction == "Supporter To Beneficiary" and letter.kit_identifier:
                letter.write(
                    {
                        "kit_identifier": False,
                        "resubmit_id": letter.resubmit_id + 1,
                    }
                )
            letter.action_send_local_translate(resubmit=True)

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
            self.with_user(SUPERUSER_ID).with_delay_sh(
                "create_commkit",
                channel="root.sbc_compassion",
                priority=100,
                description="Create Commkit",
                identity_key=f"sbc.create_commkit.{self.ids}",
            )

    def list_letters(self):
        """API call to fetch letters to translate"""
        return [letter.get_letter_info() for letter in self.sorted("scanned_date")]

    # Webapp-facing aliases for the action_* methods.
    # translation-platform-web calls these by their unprefixed names;
    # the action_* names stay for backend button bindings (Odoo
    # convention).
    def remove_local_translate(self):
        return self.action_remove_local_translate()

    def resubmit_to_translation(self):
        return self.action_resubmit_to_translation()

    def get_letter_info(self):
        """Translation Platform API for fetching letter data."""
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        base_url = base_url.rstrip("/") + "/"
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
            "pdfUrl": f"/b2s_image?letter_uuid={self.uuid}&disposition=inline",
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
        Update the priority of letters to translate if the letter is not already at the
        highest priority.
        When the letter is already at the highest priority, it moves it to another
        suitable pool. :return: None
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

            # If the letter is already at the highest priority and
            # has a fallback competence, move it to another pool
            elif letter.translation_competence_id.fallback_competence_id:
                letter.move_pool()

    def move_pool(self):
        """
        Move letter to another common translation pool.
        This is helpful when a letter is stuck for too long inside a pool,
        and we want to move it to another one that has more translator resources.
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
