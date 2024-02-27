##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    import regex as re
    from bs4 import BeautifulSoup
    from pyquery import PyQuery
except ImportError:
    _logger.warning("Please install python pyquery, regex and bs4")


def safe_replace(original, to_replace, replacement):
    """
    Utility that will replace the string except in the HTML tag attributes
    :param original: original string
    :param to_replace: string to replace
    :param replacement: replacement string
    :return: new string with the replacement done
    """

    def _replace(match):
        if match.group(1):
            return match.group(0)
        else:
            return replacement

    replace_regex = re.escape(to_replace.replace("\\", ""))
    in_attr = r'((?:<[^<>]*?"[^<>]*?){1}' + replace_regex + r'(?:[^<>]*?"[^<>]*?>){1})'
    regex = in_attr + r"|(" + replace_regex + r")"
    return re.sub(regex, _replace, original)


class CommunicationRevision(models.Model):
    _name = "partner.communication.revision"
    _inherit = "mail.thread"
    _rec_name = "config_id"
    _description = "Communication template revision"
    _order = "config_id asc,revision_number desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    config_id = fields.Many2one(
        "partner.communication.config",
        "Communication type",
        required=True,
        ondelete="cascade",
        readonly=False,
    )
    model = fields.Char(related="config_id.model_id.model", readonly=True)
    lang = fields.Selection("select_lang", required=True)
    revision_number = fields.Float(default=0.0)
    revision_date = fields.Date(default=fields.Date.today())
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("submit", "Submitted"),
            ("corrected", "Corrected"),
            ("approved", "Approved"),
            ("active", "Active"),
        ],
        default="active",
    )
    is_master_version = fields.Boolean()
    subject = fields.Char()
    subject_correction = fields.Char()
    raw_subject = fields.Char(
        compute="_compute_raw_subject", inverse="_inverse_raw_subject"
    )
    body_html = fields.Html(
        compute="_compute_body_html", inverse="_inverse_body_html", sanitize=False
    )
    raw_template_edit_mode = fields.Boolean()
    simplified_text = fields.Html(sanitize=False)
    user_id = fields.Many2one(
        "res.users",
        "Responsible",
        domain=[("share", "=", False)],
        tracking=True,
        readonly=False,
    )
    correction_user_id = fields.Many2one(
        "res.users",
        "Corrector",
        domain=[("share", "=", False)],
        tracking=True,
        readonly=False,
    )
    update_user_id = fields.Many2one("res.users", "Modified by", readonly=False)
    proposition_text = fields.Html()
    proposition_correction = fields.Html()
    compare_lang = fields.Selection("select_lang")
    compare_text = fields.Html()
    compare_subject = fields.Char()
    preview_text = fields.Html()
    keyword_ids = fields.One2many(
        "partner.communication.keyword", "revision_id", "Keywords", readonly=False
    )
    show_all_keywords = fields.Boolean(default=True)
    edit_keyword_ids = fields.One2many(
        "partner.communication.keyword",
        compute="_compute_keyword_ids",
        inverse="_inverse_keyword_ids",
        string="Keywords",
        readonly=False,
    )
    if_keyword_ids = fields.One2many(
        "partner.communication.keyword",
        compute="_compute_keyword_ids",
        inverse="_inverse_keyword_ids",
        string="Conditional text",
        readonly=False,
    )
    for_keyword_ids = fields.One2many(
        "partner.communication.keyword",
        compute="_compute_keyword_ids",
        inverse="_inverse_keyword_ids",
        string="Loops",
        readonly=False,
    )
    is_proposer = fields.Boolean(compute="_compute_allowed")
    is_corrector = fields.Boolean(compute="_compute_allowed")
    display_name = fields.Char(compute="_compute_display_name")
    active_revision_id = fields.Many2one(
        comodel_name="partner.communication.revision.history",
        string="Active version",
        domain="[('linked_revision_id.id', '=', id), "
        "('linked_revision_id.lang', '=', lang)]",
    )
    is_old_version = fields.Boolean(compute="_compute_old_version")

    _sql_constraints = [
        (
            "unique_revision",
            "unique(config_id,lang)",
            "You can only have one revision per language",
        ),
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def select_lang(self):
        langs = self.env["res.lang"].search([])
        config_id = self.env.context.get("config_id")
        valid_langs = None
        if config_id:
            revisions = self.config_id.browse(config_id).revision_ids.filtered(
                lambda r: r.state in ("approved", "active")
            )
            valid_langs = revisions.mapped("lang")
        return [
            (lang.code, lang.name)
            for lang in langs
            if not config_id or lang.code in valid_langs
        ]

    def _compute_keyword_ids(self):
        for revision in self:
            revision.edit_keyword_ids = revision.keyword_ids.filtered(
                lambda k, revision=revision: (
                    (revision.show_all_keywords and k.type in ("code", "var"))
                    or k.type == "code"
                )
                and (revision.show_all_keywords or k.is_visible)
            )
            revision.if_keyword_ids = revision.keyword_ids.filtered(
                lambda k, revision=revision: k.type == "if"
                and (revision.show_all_keywords or k.is_visible)
            )
            revision.for_keyword_ids = revision.keyword_ids.filtered(
                lambda k, revision=revision: "for" in k.type
                and (revision.show_all_keywords or k.is_visible)
            )

    def _inverse_keyword_ids(self):
        return True

    @api.constrains("correction_user_id")
    def _check_corrector(self):
        for rev in self:
            if rev.correction_user_id and rev.correction_user_id == rev.user_id:
                raise ValidationError(
                    _(
                        "Corrector cannot be the same person as the one making "
                        "the new version."
                    )
                )
        return True

    def _compute_allowed(self):
        user = self.env.user
        admin = self.env.ref("base.group_erp_manager") in user.groups_id
        for rev in self:
            rev.is_proposer = user == rev.user_id or admin
            rev.is_corrector = user == rev.correction_user_id or admin

    def _compute_display_name(self):
        for rev in self:
            rev.display_name = rev.config_id.name + " - " + rev.lang.upper()[:2]

    def _compute_raw_subject(self):
        for revision in self:
            revision.raw_subject = revision.config_id.email_template_id.with_context(
                lang=revision.lang
            ).subject

    def _inverse_raw_subject(self):
        for revision in self:
            if revision.raw_subject:
                revision.config_id.email_template_id.with_context(
                    lang=revision.lang
                ).subject = revision.raw_subject

    def _compute_body_html(self):
        for revision in self:
            revision.body_html = revision.config_id.email_template_id.with_context(
                lang=revision.lang
            ).body_html

    def _inverse_body_html(self):
        for revision in self:
            if revision.body_html:
                revision.config_id.email_template_id.with_context(
                    lang=revision.lang
                ).body_html = revision.body_html

    def _compute_old_version(self):
        for revision in self:
            latest_version = revision.get_latest_revision()
            revision.is_old_version = revision.active_revision_id != latest_version

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    def write(self, vals):
        """
        Push back the enhanced text in translation of the mail.template.
        Update revision date and number depending on edit mode.
        """
        if "active_revision_id" in vals:
            # Change the revision (only one at a time is possible)
            self.ensure_one()
            if self.active_revision_id and not self.env.context.get(
                "skip_revision_backup"
            ):
                self.save_current_revision()
            backup = self.env["partner.communication.revision.history"].browse(
                vals["active_revision_id"]
            )
            if backup:
                # Restore all fields from the backup
                vals.update(backup.get_vals())
            super().write(vals)
            return True

        if "correction_user_id" in vals:
            user = self.env["res.users"].browse(vals["correction_user_id"])
            self.message_subscribe(user.partner_id.ids)

        if "simplified_text" not in vals or self.env.context.get("no_update"):
            return super().write(vals)

        for revision in self.filtered("simplified_text"):
            vals["update_user_id"] = self.env.uid
            super(CommunicationRevision, revision).write(vals)

            # 2. Push back the template text
            # Set the conditionals texts
            revision.save_text()
            revision.body_html = revision._enhance_text()
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def start_single_revision(self):
        """
        Useful to just edit one language regardless of other translations
        """
        # Enable revision editing mode
        self.write(
            {
                "state": "pending",
                "user_id": self.env.uid,
                "correction_user_id": False,
                "is_master_version": False,
            }
        )
        return True

    def edit_revision(self):
        """
        View helper to open a revision in edit mode.
        This will increment a small step in the
        revision number and change the revision date.
        :return: action window
        """
        self.ensure_one()
        new_revision_number = self.revision_number + 0.01
        self._create_backup(new_revision_number)
        self.revision_number = new_revision_number
        self.revision_date = fields.Date.today()
        return self._open_revision()

    def new_revision(self):
        """
        View helper to open a revision in edit mode.
        This will increase the revision number and the date meaning we will
        modify the text model more than just a few corrections.
        :return: action window
        """
        self.ensure_one()
        this_revision_number = int(self.revision_number + 1.0)
        current_revision_number = self.config_id.revision_number
        new_revision_number = max([this_revision_number, current_revision_number])

        self._create_backup(new_revision_number)

        revision_vals = {
            "revision_number": new_revision_number,
            "revision_date": fields.Date.today(),
            "state": "active",
        }
        if new_revision_number > current_revision_number:
            self.config_id.write(revision_vals)
        self.write(revision_vals)
        return self._open_revision()

    def edit_proposition(self):
        """This is used to open the revision proposition text."""
        self.ensure_one()
        return self._open_revision(form_view_mode="proposition")

    def show_revision(self):
        self.ensure_one()
        return self._open_revision(form_view_mode="readonly")

    def get_latest_revision(self):
        self.ensure_one()
        return self.env["partner.communication.revision.history"].search(
            [("linked_revision_id", "=", self.id)],
            order="revision_number desc",
            limit=1,
        )

    def duplicate_revision(self):
        """
        Duplicate the current revision by creating a new revision with an incremented revision number.

        This function ensures that only one revision is duplicated at a time. It calculates the new revision number
        by incrementing the current revision number by 1. It then checks if a revision with the same revision number
        already exists. If so, it increments the revision number until a unique revision number is found.

        After creating the new revision, it sets the active_revision_id of the current revision to the newly created
        revision.
        """
        self.ensure_one()

        new_revision_number = self.revision_number + 1

        # Vérifier si le nouveau numéro de révision existe déjà
        while self.env["partner.communication.revision.history"].search_count([
            ("revision_number", "=", new_revision_number),
        ]):
            new_revision_number += 1

        self.active_revision_id = (
            self.env["partner.communication.revision.history"]
            .create(
                {
                    "revision_number": new_revision_number,
                    "revision_date": fields.Date.today(),
                    "subject": self.subject,
                    "body_html": self.body_html,
                    "linked_revision_id": self.id,
                    "proposition_text": self.proposition_text,
                    "raw_subject": self.raw_subject,
                }
            )
        )

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def save_text(self):
        """
        Save the current text in the clauses
        """
        text = PyQuery(self.simplified_text)
        for key in self.keyword_ids.filtered(
            lambda k: k.type in ("if", "for", "for_ul")
        ):
            text_selector = text("#" + key.html_id)
            current_text = text_selector.html()
            if current_text is not None:
                key.set_text(current_text, key.edit_value)
        self.with_context(no_update=True).write({"simplified_text": text.html()})
        return True

    def keyword_toggle_value(self, keyword):
        """
            Switch the text in the 'if' clause between 'true_text' and 'false_text'
            Save the modified text for the correct clause
        :param keyword:
        :return:
        """
        if keyword in self.keyword_ids:
            text = PyQuery(self.simplified_text)
            text_selector = text("#" + keyword.html_id)
            current_text = text_selector.html()
            if current_text is not None:
                keyword.set_text(current_text, not keyword.edit_value)
            text_selector.html(keyword.get_text())
            self.with_context(no_update=True).write({"simplified_text": text.html()})

    def open_preview(self):
        preview_model = "partner.communication.revision.preview"
        working_mode = self._context.get("working_revision")
        context = {
            "revision_id": self.id,
            "lang": self.lang,
        }
        if working_mode:
            # The preview is from the revision edition mode, we fetch the
            # working texts.
            context["working_text"] = self.proposition_text
            context["working_subject"] = self.subject

            if self.state == "submit":
                context["working_text"] = self.proposition_correction
                context["working_subject"] = self.subject_correction
        preview = (
            self.env[preview_model]
            .with_context(context)
            .create(
                {
                    "revision_id": self.id,
                    "state": "working_revision" if working_mode else "active_revision",
                }
            )
        )
        preview.preview()
        return {
            "name": "Preview",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": preview_model,
            "res_id": preview.id,
            "context": self.with_context(context).env.context,
            "target": "new",
        }

    # Revision proposition buttons
    def submit_proposition(self):
        return self._open_submit_text_wizard()

    def validate_proposition(self):
        subject = f"[{self.display_name}] Revision approved"
        body = f"The text for {self.display_name} was approved."
        if not self.is_master_version:
            self.approve(subject, body)
        return self.with_context(body=body, subject=subject)._open_validation()

    def submit_correction(self):
        return self._open_submit_text_wizard()

    def _open_submit_text_wizard(self):
        return {
            "name": "Submit text",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "partner.communication.submit.revision",
            "context": self.with_context(
                active_id=self.id, form_view_ref=False, config_id=False
            ).env.context,
            "target": "new",
        }

    def validate_correction(self):
        self.write(
            {
                "proposition_text": self.proposition_correction,
                "subject": self.subject_correction,
            }
        )
        body = f"The text for {self.display_name} was approved."
        subject = f"[{self.display_name}] Corrections approved"
        if not self.is_master_version:
            self.approve(subject, body)

        return self.with_context(body=body, subject=subject)._open_validation()

    def edit_correction(self):
        return self.write(
            {
                "state": "pending",
                "proposition_text": self.proposition_correction,
                "proposition_correction": False,
            }
        )

    def discard_correction(self):
        return self.write({"state": "pending", "proposition_correction": False})

    def approve(self, subject=None, body=None):
        self.write(
            {
                "proposition_correction": False,
                "subject_correction": False,
                "state": "approved",
                "compare_text": False,
                "compare_subject": False,
            }
        )
        subject = self._context.get("subject", subject)
        body = self._context.get("body", body)
        self.notify_proposition(subject, body)

    def notify_proposition(self, subject, body):
        # Post a message that is sent to watchers
        self.message_post(
            body=body,
            subject=subject,
            subtype_xmlid="mail.mt_comment",
            content_subtype="html",
        )

    def cancel_approve(self):
        """Set back a text approved in revision mode."""
        return {
            "name": "Cancel proposition",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "partner.communication.cancel.proposition",
            "context": self.with_context(
                active_id=self.id, form_view_ref=False, config_id=False
            ).env.context,
            "target": "new",
        }

    @api.onchange("compare_lang")
    def onchange_compare_lang(self):
        master = self.search(
            [
                ("config_id", "=", self.config_id.id),
                ("lang", "=", self.compare_lang),
                ("state", "in", ("approved", "active")),
            ]
        )
        self.compare_text = master.proposition_text
        self.compare_subject = master.subject
        self._origin.write(
            {"compare_text": master.proposition_text, "compare_subject": master.subject}
        )

    def reload_text(self):
        self.keyword_ids.unlink()
        self.raw_template_edit_mode = False
        if self.body_html:
            self.with_context(no_update=True).simplified_text = self._simplify_text()

    def toggle_all_keywords(self):
        for record in self:
            record.show_all_keywords = not record.show_all_keywords
        return True

    @api.model
    def send_revision_reminders(self):
        pending_revisions = self.search([("state", "not in", ["approved", "active"])])
        users = pending_revisions.mapped("user_id") | pending_revisions.mapped(
            "correction_user_id"
        )
        reminder_config = self.env.ref(
            "partner_communication_revision.revision_reminder_config"
        )
        for user in users:
            self.env["partner.communication.job"].create(
                {
                    "config_id": reminder_config.id,
                    "partner_id": user.partner_id.id,
                    "object_ids": user.id,
                }
            )
        return True

    def save_current_revision(self):
        for revision in self:
            if not revision.active_revision_id:
                revision._create_backup(revision.revision_number)
            else:
                revision.active_revision_id.save_revision_state()
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _open_validation(self):
        # After master version is approved, we must setup the translations
        if self.is_master_version:
            return {
                "name": "Validate proposition",
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "partner.communication.validate.proposition",
                "context": self.with_context(
                    active_id=self.id, form_view_ref=False, config_id=False
                ).env.context,
                "target": "new",
            }
        return True

    def _open_revision(self, form_view_mode=None):
        """
        Fetches the text from the mail.template and open the revision view
        :param form_view_mode: Specify a form view.
        :return: action for opening the revision view
        """
        if form_view_mode == "readonly":
            self.reload_text()
        form_view = "partner_communication_revision.revision_form"
        if form_view_mode:
            form_view += "_" + form_view_mode
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref(form_view).id,
            "res_id": self.id,
            "res_model": self._name,
            "target": "current",
        }

    def _simplify_text(self):
        """
        Converts the mail_template raw text to a simplified version,
        readable to any user.
        :return: the simplified text
        """
        self.ensure_one()
        previous_keywords = self.keyword_ids
        found_keywords = self.env["partner.communication.keyword"]
        simplified_text, keywords = self._replace_setters(self.body_html)
        found_keywords |= keywords
        simplified_text, keywords = self._replace_inline_code(simplified_text)
        found_keywords |= keywords
        nested_position = 1
        if_keyword_index = 1
        for_keyword_index = 1
        while "% if" in simplified_text:
            simplified_text, keywords = self._replace_if(
                simplified_text, nested_position, if_keyword_index
            )
            if not keywords:
                # Trouble finding the if
                break
            found_keywords |= keywords
            if_keywords = keywords.filtered(lambda k: k.type == "if")
            if_keyword_index += len(if_keywords)
            for_keyword_index += len(keywords - if_keywords)
            nested_position += 1
        nested_position = 1
        while "% for" in simplified_text:
            simplified_text, keywords = self._replace_for(
                simplified_text, nested_position, for_keyword_index
            )
            if not keywords:
                # Trouble finding the for
                break
            found_keywords |= keywords
            for_keyword_index += len(keywords)
            nested_position += 1
        if self._context.get("unstore_keywords"):
            # Remove found keywords
            (found_keywords - previous_keywords).unlink()
        else:
            # Remove invalid keywords that are no more in the template
            (previous_keywords - found_keywords).unlink()
        return simplified_text

    def _replace_inline_code(self, text):
        """
        Finds and replace the ${} portions of the mail.template.
        It will create keyword records
        :param text: mail.template text
        :return: simplified text
        """
        code_regex = r"\$\{.+?\}"
        simple_text = self._replace_keywords(text, "code", code_regex)
        return simple_text

    def _replace_setters(self, text):
        """
        Finds and replace the % set var = object
        of the mail.template text. It will create keyword records.
        :param text: mail.template text
        :return: simplified text without the setters code, found keywords
        """
        return self._replace_keywords(text, "var", r"% set (.+?)=(.*)", True)

    def _replace_keywords(self, text, kw_type, pattern, is_black=False):
        """
        Finds and replace keywords
        :param text: mail.template text
        :param kw_type: keyword type
        :param pattern: pattern used for finding the keywords in the template
        :param is_black: set to true to force the color black for the keyword
        :return: simplified text without the keywords code, found keywords
        """
        setter_pattern = re.compile(pattern)
        simple_text = text
        keywords = self.env["partner.communication.keyword"]
        keyword_number = 1
        # Find first match
        for match in setter_pattern.finditer(text):
            raw_code = match.group(0).strip()
            if not raw_code:
                continue
            keyword = self.keyword_ids.filtered(
                lambda k, raw_code=raw_code, keyword_number=keyword_number: k.raw_code
                == raw_code
                and (k.index == keyword_number if kw_type == "var" else 1)
            )
            if not keyword:
                vals = {
                    "raw_code": raw_code,
                    "type": kw_type,
                    "revision_id": self.id,
                    "position": match.start(),
                }
                if is_black:
                    vals["color"] = "black"
                keyword = keywords.create(vals)
                # Recompute replacement html
                self.env.clear()
            keywords += keyword
            keyword_number += 1
            simple_text = safe_replace(simple_text, raw_code, keyword.replacement)
        return simple_text, keywords

    def _replace_if(self, text, nested_position, keyword_number=1):
        """
        Finds and replace the % if: ... % endif
        of the mail.template. It will create keyword records for
        each if found.
        :param text: mail.template text
        :param nested_position: counts how nested if the current pass
        :param keyword_number: counts how many if we found
        :return: simplified text without the if code, keywords found
        """
        # Scan for non-nested % if, % else codes
        if_pattern = re.compile(
            r"(% if .*?:$)(.*?)(% endif)", flags=re.DOTALL | re.MULTILINE
        )
        simple_text = text
        keywords = self.env["partner.communication.keyword"]
        for match in if_pattern.finditer(text, overlapped=True):
            raw_code = match.group(1).strip()
            if_text = match.group(2)
            start_if = match.start()
            end_if = match.end()
            # Nested ifs : we first convert the sub-ifs and then finish
            # with the root if
            number_nested = if_text.count("% if")
            if number_nested > 0:
                continue
            keyword = self.keyword_ids.filtered(
                lambda k, raw_code=raw_code, keyword_number=keyword_number: k.raw_code
                == raw_code
                and k.index == keyword_number
            )

            # Convert nested for loops in if text
            if_text, for_keywords = self._replace_for(if_text, 1)
            keywords += for_keywords

            if_parts = if_text.split("% else:")
            true_text = if_parts[0]
            false_text = if_parts[1].strip() if len(if_parts) > 1 else False
            if not keyword:
                # Create a new keyword object by extracting the text
                keyword = self.keyword_ids.create(
                    {
                        "raw_code": raw_code,
                        "revision_id": self.id,
                        "true_text": true_text.strip(),
                        "false_text": false_text,
                        "type": "if",
                        "position": start_if,
                        "nested_position": nested_position,
                    }
                )
            else:
                keyword.write(
                    {
                        "true_text": true_text,
                        "false_text": false_text,
                        "position": start_if,
                        "nested_position": nested_position,
                    }
                )
            keywords += keyword
            keyword_number += 1
            simple_text = simple_text.replace(
                text[start_if:end_if], keyword.replacement
            )
        return simple_text, keywords

    def _replace_for(self, text, nested_position, keyword_number=1):
        """
        Finds and replace the % for: ... % endfor loops
        of the mail.template. It will create keyword records for
        each loop found.
        :param text: mail.template text
        :param nested_position: counts how nested if the current pass
        :param keyword_number: counts how many for we found
        :return: simplified text without the if code, keywords found
        """
        # Regex for finding text wrapped in loops
        loop_regex = r"(% for .*?:$)(.*?)(% endfor)"
        ul_loop_regex = r"(?:<ul[^<]*?)(% for .*?:$)(.*?)(% endfor)(.*?</ul>)"

        # First scan for ul_loops
        for_pattern = re.compile(ul_loop_regex, flags=re.DOTALL | re.MULTILINE)
        simple_text, found_keywords = self._replace_for_type(
            text, nested_position, keyword_number, "for_ul", for_pattern
        )
        keyword_number += len(found_keywords)

        # Then scan for regular loops
        for_pattern = re.compile(loop_regex, flags=re.DOTALL | re.MULTILINE)
        simple_text, keywords = self._replace_for_type(
            simple_text, nested_position, keyword_number, "for", for_pattern
        )
        found_keywords |= keywords

        return simple_text, found_keywords

    def _replace_for_type(
        self, text, nested_position, keyword_number, for_type, for_pattern
    ):
        simple_text = text
        keywords = self.env["partner.communication.keyword"]
        for match in for_pattern.finditer(text, overlapped=True):
            raw_code = match.group(1).strip()
            for_text = match.group(2)
            start_for = match.start()
            end_for = match.end()
            # Nested for : skip to next for loop which is not encapsulating
            # another loop. The while loop will take care of it later.
            number_nested = for_text.count("% for")
            if number_nested > 0:
                continue
            keyword = self.keyword_ids.filtered(
                lambda k, raw_code=raw_code, keyword_number=keyword_number: k.raw_code
                == raw_code
                and k.index == keyword_number
                and k.type == for_type
            )
            if not keyword:
                # Create a new keyword object by extracting the text
                keyword = self.keyword_ids.create(
                    {
                        "raw_code": raw_code,
                        "revision_id": self.id,
                        "true_text": for_text.strip(),
                        "type": for_type,
                        "position": start_for,
                        "nested_position": nested_position,
                    }
                )
            else:
                keyword.write(
                    {
                        "true_text": for_text,
                        "position": start_for,
                        "nested_position": nested_position,
                    }
                )
            keywords += keyword
            keyword_number += 1
            simple_text = simple_text.replace(
                text[start_for:end_for], keyword.replacement
            )
        return simple_text, keywords

    def _enhance_text(self):
        """
        Transforms a simplified text into a valid mail.template text.
        :return: mail.template text
        """
        self.ensure_one()
        # Parse and set back the keywords into raw template code
        html_text = PyQuery(self.simplified_text.replace("\n", ""))

        def sort_keywords(kw):
            # Replace first if/for-clauses, then var, then code
            index = kw.position
            if kw.type == "if" or "for" in kw.type:
                index += 2 * len(self.body_html) * kw.nested_position
                # Take if and for in the appearing order in the text
                index -= kw.position
            elif kw.type == "var":
                index += len(self.body_html)
            return index

        keywords = self.keyword_ids.sorted(sort_keywords, reverse=True)
        # Replace automatic-generated keywords
        for keyword in keywords:
            keyword_text = html_text("#" + keyword.html_id)
            keyword_text.replace_with(keyword.final_text)

        # Replace user added keywords
        template_text = html_text.html()
        for keyword in keywords.filtered(lambda k: k.type == "code"):
            to_replace = f"[{keyword.short_code}]"
            template_text = template_text.replace(to_replace, keyword.raw_code)
        final_text = PyQuery(BeautifulSoup(template_text).prettify())
        return final_text("body").html()

    def _get_backup(self, revision_number):
        self.ensure_one()
        return self.env["partner.communication.revision.history"].search(
            [
                ("revision_number", "=", revision_number),
                ("linked_revision_id", "=", self.id),
            ]
        )

    def _create_backup(self, backup_revision_number):
        self.ensure_one()
        self.active_revision_id = (
            self.env["partner.communication.revision.history"]
            .with_context(skip_revision_backup=True)
            .create(
                {
                    "revision_number": backup_revision_number,
                    "revision_date": self.revision_date,
                    "subject": self.subject,
                    "body_html": self.body_html,
                    "linked_revision_id": self.id,
                    "proposition_text": self.proposition_text,
                    "raw_subject": self.raw_subject,
                }
            )
        )
