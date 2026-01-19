##############################################################################
#
#    Copyright (C) 2014-2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import datetime
import json
import logging
import shutil
import subprocess
import uuid
from collections import defaultdict

from dateutil.relativedelta import relativedelta
from PyPDF2 import PdfFileReader

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext
from odoo.tools.image import image_process
from odoo.tools.pdf import to_pdf_stream

from ..tools.onramp_connector import SBCConnector
from .correspondence_page import BOX_SEPARATOR, PAGE_SEPARATOR

_logger = logging.getLogger(__name__)


class CorrespondenceType(models.Model):
    _name = "correspondence.type"
    _description = "Type of correspondence"
    _inherit = "connect.multipicklist"
    res_model = "correspondence"
    res_field = "communication_type_ids"


class Correspondence(models.Model):
    """This class holds the data of a Communication Kit between
    a child and a sponsor.
    """

    _name = "correspondence"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "correspondence.metadata",
        "translatable.model",
        "compassion.mapped.model",
        "utm.mixin",
    ]
    _description = "Letter"
    _order = "status_date desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # 1. Mandatory and basic fields
    ###############################
    sponsorship_id = fields.Many2one(
        "recurring.contract",
        "Sponsorship",
        required=True,
        domain=[("state", "not in", ["draft", "cancelled"]), ("child_id", "!=", False)],
        tracking=True,
        readonly=False,
    )
    company_id = fields.Many2one(
        related="sponsorship_id.company_id",
    )
    name = fields.Char(compute="_compute_name", store=True)
    partner_id = fields.Many2one(
        "res.partner", "Partner", readonly=False, ondelete="restrict"
    )
    child_id = fields.Many2one(related="sponsorship_id.child_id", readonly=True)
    avatar_128 = fields.Image(compute="_compute_avatar")
    # Field used for identifying correspondence by GMC
    kit_identifier = fields.Char("Kit id", copy=False, tracking=True)
    direction = fields.Selection(
        selection=[
            ("Supporter To Beneficiary", "Supporter to participant"),
            ("Beneficiary To Supporter", "Participant to supporter"),
        ],
        required=True,
        default="Supporter To Beneficiary",
    )
    communication_type_ids = fields.Many2many(
        "correspondence.type",
        "correspondence_type_relation",
        "correspondence_id",
        "type_id",
        "Communication type",
    )
    s2b_state = fields.Selection(
        [
            ("Draft", "Draft"),
            ("Received in the system", "Scanned in"),
            ("Global Partner translation queue", "To Translate"),
            ("Global Partner translation process", "Translating"),
            ("Quality check queue", "Quality Check Queue"),
            ("Quality check process", "Quality Check Process"),
            ("Translation and quality check complete", "Quality Check Done"),
            ("Field Office translation queue", "National Office Translation Queue"),
            ("Composition process", "Composition Process"),
            ("Printed and sent to ICP", "Sent to FCP"),
            ("Exception", "Exception"),
            ("Quality check unsuccessful", "Quality check failed"),
            ("Translation check unsuccessful", "Translation check unsuccessful"),
        ],
        compute="_compute_states",
    )
    b2s_state = fields.Selection(
        [
            ("Ready to be printed", "Ready to be printed"),
            (
                "Field Office transcribing translation and content check process",
                "National Office content check",
            ),
            ("Field Office translation queue", "National Office Translation Queue"),
            ("In Translation", "SDL FO Translation"),
            ("Quality check queue", "Quality Check Queue"),
            ("Quality check process", "Quality Check Process"),
            ("Translation and quality check complete", "Quality Check Done"),
            ("Global Partner translation queue", "To Translate"),
            ("Global Partner translation process", "Translating"),
            ("Composition process", "Composition Process"),
            ("Published to Global Partner", "Published"),
            ("Quality check unsuccessful", "Quality check unsuccessful"),
            ("Translation check unsuccessful", "Translation check unsuccessful"),
            ("Exception", "Exception"),
        ],
        compute="_compute_states",
    )
    state = fields.Selection("get_states", default="Draft", tracking=True)
    email_read = fields.Datetime()

    # 2. Attachments and scans
    ##########################
    sponsor_letter_scan = fields.Binary()
    file_name = fields.Char()
    letter_format = fields.Selection(
        [("pdf", "pdf"), ("zip", "zip")],
        compute="_compute_letter_format",
        store=True,
    )
    preview = fields.Html(
        "Preview of the letter", compute="_compute_preview", sanitize=False
    )

    # 3. Letter language, text information, attached images
    #######################################################
    supporter_languages_ids = fields.Many2many(
        "res.lang.compassion",
        related="partner_id.spoken_lang_ids",
    )
    beneficiary_language_ids = fields.Many2many(
        "res.lang.compassion",
        compute="_compute_beneficiary_language_ids",
    )
    original_language_id = fields.Many2one(
        "res.lang.compassion",
        "Original language",
    )
    translation_language_id = fields.Many2one(
        "res.lang.compassion",
        "Translation language",
        tracking=True,
    )
    original_text = fields.Text(
        compute="_compute_original_text", inverse="_inverse_original"
    )
    english_text = fields.Text(
        compute="_compute_english_text", inverse="_inverse_english"
    )
    translated_text = fields.Text(
        compute="_compute_translated_text", inverse="_inverse_translated"
    )
    original_attachment_ids = fields.One2many(
        "ir.attachment",
        "res_id",
        domain=[("res_model", "=", _name)],
        string="Attached images",
        copy=True,
    )
    page_ids = fields.One2many(
        "correspondence.page", "correspondence_id", readonly=False, copy=True
    )
    nbr_pages = fields.Integer(
        string="Number of pages", compute="_compute_nbr_pages", store=True
    )
    template_id = fields.Many2one("correspondence.template", "Template")

    # 4. Additional information
    ###########################
    status_date = fields.Datetime(default=fields.Datetime.now)
    scanned_date = fields.Date(default=fields.Date.today)
    relationship = fields.Selection(
        [
            ("Sponsor", "Sponsor"),
            ("Encourager", "Encourager"),
            ("Correspondent", "Correspondent"),
        ],
        default="Sponsor",
    )
    is_first_letter = fields.Boolean(
        compute="_compute_is_first",
        store=True,
        readonly=True,
        string="First letter from Participant",
    )
    marked_for_rework = fields.Boolean()
    rework_reason = fields.Char()
    rework_comments = fields.Text()
    original_letter_url = fields.Char()
    cloudinary_original_letter_url = fields.Char()
    final_letter_url = fields.Char()
    cloudinary_final_letter_url = fields.Char()
    import_id = fields.Many2one("import.letters.history", readonly=False)
    translator = fields.Char()
    email = fields.Char(related="partner_id.email")
    sponsorship_state = fields.Selection(
        related="sponsorship_id.state", string="Sponsorship state", readonly=True
    )
    is_final_letter = fields.Boolean(compute="_compute_is_final_letter")
    generator_id = fields.Many2one(
        "correspondence.s2b.generator", readonly=False, copy=False
    )
    resubmit_id = fields.Integer(default=1)
    sponsor_needs_final_letter = fields.Boolean(
        compute="_compute_sponsor_needs_final_letter"
    )
    report_needs_overlay = fields.Char(compute="_compute_report_needs_overlay")
    report_needs_original_text = fields.Char(
        compute="_compute_report_needs_original_text"
    )
    report_needs_final_text = fields.Char(compute="_compute_report_needs_final_text")
    report_needs_english_text = fields.Char(
        compute="_compute_report_needs_english_text"
    )

    # Letter remote access
    ######################
    uuid = fields.Char(
        required=True, default=lambda self: self._get_uuid(), copy=False, index=True
    )
    read_url = fields.Char(compute="_compute_read_url", store=True)

    # 5. SQL Constraints
    ####################
    _sql_constraints = [
        (
            "kit_identifier",
            "unique(kit_identifier)",
            "The kit id already exists in database.",
        ),
        (
            "uuid",
            "unique(uuid)",
            "The uuid already exists in database.",
        ),
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def get_states(self):
        """Returns all the possible states."""
        return list(
            set(self._fields["s2b_state"].selection)
            | set(self._fields["b2s_state"].selection)
        )

    def _compute_states(self):
        """Sets the internal states (s2b and b2s)."""
        for letter in self:
            if letter.direction == "Supporter To Beneficiary":
                letter.s2b_state = letter.state
                letter.b2s_state = False
            else:
                letter.b2s_state = letter.state
                letter.s2b_state = False

    @api.onchange("sponsorship_id")
    def onchange_sponsorship(self):
        for letter in self:
            if letter.sponsorship_id:
                letter.child_id = letter.sponsorship_id.child_id
                letter.partner_id = letter.sponsorship_id.correspondent_id

    @api.depends("sponsorship_id")
    def _compute_is_first(self):
        """ Sets the value at true if is the first letter\
                from the beneficiary. """
        for letter in self:
            if letter.sponsorship_id:
                count = self.search_count(
                    [
                        ("sponsorship_id", "=", letter.sponsorship_id.id),
                        ("direction", "=", "Beneficiary To Supporter"),
                    ]
                )
                if count == 1:
                    letter.is_first_letter = True
                else:
                    letter.is_first_letter = False

    @api.model
    def get_communication_types(self):
        return [
            ("Beneficiary Initiated Letter", _("Participant Initiated")),
            ("Final Letter", _("Final Letter")),
            ("Large Gift Thank You Letter", _("Large Gift Thank You")),
            ("Small Gift Thank You Letter", _("Small Gift Thank You")),
            ("New Sponsor Letter", _("New Sponsor Letter")),
            ("Reciprocal Letter", _("Reciprocal Letter")),
            ("Scheduled Letter", _("Scheduled")),
            ("Supporter Letter", _("Supporter Letter")),
        ]

    @api.depends("sponsorship_id", "communication_type_ids")
    def _compute_name(self):
        for letter in self:
            if letter.sponsorship_id and letter.communication_type_ids:
                letter.name = (
                    (letter.communication_type_ids[0].name or "")
                    + " ("
                    + (letter.sponsorship_id.partner_id.ref or "")
                    + " - "
                    + (letter.child_id.local_id or "")
                    + ")"
                )
            else:
                letter.name = (
                    f"{letter.scanned_date}"
                    f"_Supporter_Letter_{letter.sponsorship_id.display_name}"
                )

    def _compute_avatar(self):
        for correspondence in self:
            if correspondence.direction == "Supporter To Beneficiary":
                correspondence.avatar_128 = correspondence.partner_id.avatar_128
            else:
                correspondence.avatar_128 = correspondence.child_id.avatar_128

    @api.depends(
        "page_ids", "page_ids.paragraph_ids", "page_ids.paragraph_ids.original_text"
    )
    def _compute_original_text(self):
        for letter in self:
            letter.original_text = letter._get_text("original_text")

    @api.depends(
        "page_ids", "page_ids.paragraph_ids", "page_ids.paragraph_ids.translated_text"
    )
    def _compute_translated_text(self):
        for letter in self:
            letter.translated_text = letter._get_text("translated_text")

    @api.depends(
        "page_ids", "page_ids.paragraph_ids", "page_ids.paragraph_ids.english_text"
    )
    def _compute_english_text(self):
        for letter in self:
            letter.english_text = letter._get_text("english_text")

    @api.depends("page_ids")
    def _compute_nbr_pages(self):
        for letter in self:
            letter.nbr_pages = len(letter.page_ids)

    def _inverse_original(self):
        self._set_text("original_text", self.original_text)

    def _inverse_english(self):
        self._set_text("english_text", self.english_text)

    def _inverse_translated(self):
        self._set_text("translated_text", self.translated_text)

    def _set_text(self, field, text):
        # Try to put text in correct pages (the text should contain
        # separators).
        if not text:
            return
        for letter in self:
            pages_text = text.split(PAGE_SEPARATOR)
            if letter.page_ids:
                if len(pages_text) <= len(letter.page_ids):
                    for i in range(0, len(pages_text)):
                        letter.page_ids[i].set_text(field, pages_text[i].strip("\n"))
                else:
                    for i in range(0, len(letter.page_ids)):
                        letter.page_ids[i].set_text(field, pages_text[i].strip("\n"))
                    last_page_text = getattr(letter.page_ids[i], field)
                    last_page_text += "\n\n" + "\n\n".join(pages_text[i + 1 :])
                    letter.page_ids[i].set_text(field, last_page_text)
            else:
                for i in range(0, len(pages_text)):
                    page_text = pages_text[i].strip("\n")
                    letter.page_ids.create(
                        {
                            field: page_text,
                            "correspondence_id": letter.id,
                            "paragraph_ids": [
                                (0, 0, {"sequence": index, field: text})
                                for index, text in enumerate(
                                    page_text.split(BOX_SEPARATOR)
                                )
                            ],
                        }
                    )

    def _get_text(self, source_text):
        """Gets the desired text (original/translated) from the pages."""
        txt = (
            self.page_ids.mapped("paragraph_ids")
            .filtered(source_text)
            .mapped(source_text)
        )
        return ("\n" + PAGE_SEPARATOR + "\n").join(txt)

    @api.depends("sponsor_letter_scan")
    def _compute_letter_format(self):
        for letter in self:
            if letter.sponsor_letter_scan:
                file_signature = base64.b64decode(
                    letter.with_context(bin_size=False).sponsor_letter_scan[:12]
                )[:4]
                if file_signature == b"%PDF":
                    letter.letter_format = "pdf"
                elif file_signature == b"PK\x03\x04":
                    letter.letter_format = "zip"
                else:
                    letter.letter_format = False
            else:
                letter.letter_format = False

    def _get_uuid(self):
        return str(uuid.uuid4())

    def _compute_is_final_letter(self):
        for letter in self:
            letter.is_final_letter = (
                "Final Letter" in letter.communication_type_ids.mapped("name")
                or letter.sponsorship_state != "active"
            )

    def _compute_beneficiary_language_ids(self):
        for letter in self:
            letter.beneficiary_language_ids = (
                letter.child_id.project_id.field_office_id.spoken_language_ids
                + letter.child_id.project_id.field_office_id.translated_language_ids
            )

    def _check_translation_language(self):
        """Detects and corrects the translation language of a letter."""
        if self.env.context.get("skip_lang_detect"):
            return

        english = self.env.ref("advanced_translation.lang_compassion_english")
        lang_detector = self.env["langdetect"]

        for letter in self.with_context(skip_lang_detect=True):
            letter_text = (
                letter.translated_text or letter.english_text or letter.original_text
            )
            # Clean text for accurate detection
            clean_text = (
                letter_text.strip(" \t\n\r.")
                .replace(BOX_SEPARATOR, "")
                .replace(PAGE_SEPARATOR, "")
                .strip()
            )

            if not clean_text:
                # T2495 Default to English for empty B2S letters
                # to ensure they are translated if needed.
                if (
                    letter.direction == "Beneficiary To Supporter"
                    and letter.translation_language_id != english
                ):
                    letter.translation_language_id = english
                continue

            detected_lang = lang_detector.detect_language(clean_text)
            if detected_lang and detected_lang != letter.translation_language_id:
                letter.translation_language_id = detected_lang

    @api.depends("uuid")
    def _compute_read_url(self):
        for letter in self:
            letter.read_url = (
                f"{letter.get_base_url()}/b2s_image?letter_uuid={letter.uuid}"
            )

    def _compute_sponsor_needs_final_letter(self):
        """
        Check if the sponsor can read the original letter or needs the final letter
        in order to read the translation.
        """
        for letter in self:
            letter.sponsor_needs_final_letter = (
                letter.direction == "Beneficiary To Supporter"
                and letter.original_language_id not in letter.supporter_languages_ids
            )

    def _compute_report_needs_overlay(self):
        for letter in self:
            letter.report_needs_overlay = (
                letter.report_needs_original_text
                or letter.report_needs_final_text
                or letter.report_needs_english_text
            )

    def _compute_report_needs_original_text(self):
        """
        Used by the PDF report of the correspondence in order to get the text
        to overlay on the image of the page. In case of a Supporter letter that is not
        yet sent to GMC, we need to overlay the original text.
        Otherwise, it will be blank.
        """
        for letter in self:
            letter.report_needs_original_text = (
                letter.direction == "Supporter To Beneficiary"
                and not letter.kit_identifier
                and not letter.sponsor_letter_scan
            )

    def _compute_report_needs_final_text(self):
        """
        By default, this is always False, because GMC will overlay the translated text
        in the final letter image when needed. However,
        it can be overridden by a submodule in case we want to do
        the composition ourselves using the original image.
        """
        for letter in self:
            letter.report_needs_final_text = False

    def _compute_report_needs_english_text(self):
        """
        By default, this is always False, because GMC will overlay the translated text
        in the final letter image when needed. However,
        it can be overridden by a submodule in case we want to do
        the composition ourselves using the original image.
        """
        for letter in self:
            letter.report_needs_english_text = False

    def _compute_preview(self):
        for letter in self:
            # Replace w-100 by w-50 to make the preview smaller
            letter.preview = (
                self.env["ir.actions.report"]
                .with_context(bin_size=False)
                ._render_qweb_html("sbc_compassion.report_correspondence", letter.ids)[
                    0
                ]
            )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            contract = self.env["recurring.contract"].browse(vals["sponsorship_id"])
            if vals["direction"] == "Supporter To Beneficiary":
                vals["communication_type_ids"] = [
                    (4, self.env.ref("sbc_compassion.correspondence_type_supporter").id)
                ]
                if not vals.get("translation_language_id"):
                    vals["translation_language_id"] = vals.get("original_language_id")
                contract.last_sponsor_letter = fields.Date.today()
            else:
                vals["status_date"] = fields.Datetime.now()
                if "communication_type_ids" not in vals:
                    vals["communication_type_ids"] = [
                        (
                            4,
                            self.env.ref(
                                "sbc_compassion.correspondence_type_scheduled"
                            ).id,
                        )
                    ]
                # Allows manually creating a B2S letter
                if vals.get("state", "Draft") == "Draft":
                    vals["state"] = "Published to Global Partner"

            if "partner_id" not in vals:
                vals["partner_id"] = contract.correspondent_id.id

            if vals.get("sponsor_letter_scan"):
                letter_data = base64.b64decode(vals["sponsor_letter_scan"])
                vals["sponsor_letter_scan"] = base64.b64encode(
                    self._compress_pdf(letter_data)
                )

        letters = super().create(vals_list)
        # T1676 : Each page should contain at least one textbox (paragraph)
        letters.create_text_boxes()
        # Make sure the translation language is set correctly.
        letters._check_translation_language()
        for letter in letters:
            letter.file_name = letter._get_file_name()
            attachment = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "correspondence"),
                    ("res_field", "=", "sponsor_letter_scan"),
                    ("res_id", "=", letter.id),
                ]
            )
            if attachment:
                # Set the correct number of pages
                image_pdf = PdfFileReader(to_pdf_stream(attachment))
                if letter.nbr_pages < image_pdf.numPages:
                    for _i in range(letter.nbr_pages, image_pdf.numPages):
                        letter.page_ids.create({"correspondence_id": letter.id})
            if letter.state == "Received in the system" and not self.env.context.get(
                "no_comm_kit"
            ):
                letter.create_commkit()

        return letters

    def write(self, vals):
        """Keep track of state changes."""
        if "state" in vals:
            if vals["state"] == "Translation check unsuccessful":
                responsible = self.env["res.config.settings"].get_param(
                    "letter_responsible"
                )
                if responsible:
                    for c in self.filtered(
                        lambda c: c.direction == "Supporter To Beneficiary"
                    ):
                        c._make_activity(vals["state"], responsible)

            elif "state" in vals:
                for c in self.filtered(
                    lambda o: o.state == "Translation check unsuccessful"
                ):
                    c.activity_ids.unlink()
            vals["status_date"] = fields.Datetime.now()
        if vals.get("sponsor_letter_scan"):
            # Compress the PDF if it is a PDF
            vals["sponsor_letter_scan"] = base64.b64encode(
                self._compress_pdf(base64.b64decode(vals["sponsor_letter_scan"]))
            )

        super().write(vals)
        if "translation_language_id" in vals or "page_ids" in vals:
            if not self.mapped("page_ids.paragraph_ids"):
                self.create_text_boxes()
                self._check_translation_language()
        return True

    def unlink(self):
        # Remove unsent messages
        gmc_action = self.env.ref("sbc_compassion.create_letter")
        gmc_messages = self.env["gmc.message"].search(
            [
                ("action_id", "=", gmc_action.id),
                ("object_id", "in", self.ids),
                ("state", "in", ["new", "failure", "odoo_failure", "postponed"]),
            ]
        )
        gmc_messages.unlink()
        return super().unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def validate(self):
        for letter in self:
            if letter.state == "Draft":
                if not letter.sponsor_letter_scan and not letter.original_text:
                    raise UserError(_("Please attach a scan or fill in the text."))
                letter.write({"state": "Received in the system"})
                if not self.env.context.get("no_comm_kit"):
                    letter.create_commkit()
        return True

    def create_commkit(self):
        valid_christmas_period = self.env["res.config.settings"].is_in_christmas_period(
            datetime.date.today()
        )
        messages = self.env["gmc.message"]
        for letter in self:
            action_id = self.env.ref("sbc_compassion.create_letter").id
            message_vals = {
                "action_id": action_id,
                "object_id": letter.id,
                "child_id": letter.child_id.id,
                "partner_id": letter.partner_id.id,
            }
            if (
                letter.sponsorship_id.state not in ("active", "terminated")
                or letter.child_id.project_id.hold_s2b_letters
            ):
                message_vals["state"] = "postponed"
                if letter.child_id.project_id.hold_s2b_letters:
                    letter.state = "Exception"
                    letter.message_post(
                        body=_(
                            "Letter was put on hold because the project is suspended"
                        ),
                        subject=_("Project suspended"),
                    )
            if letter.template_id.is_christmas_letter and not valid_christmas_period:
                message_vals["state"] = "postponed"
                letter.state = "Exception"
                letter.message_post(
                    body=_("Christmas Letter put on hold outside of Christmas Period."),
                    subject=_("Christmas Hold"),
                )
            messages += messages.create(message_vals)
        return messages

    @api.model
    def process_commkit(self, commkit_data):
        """Update or Create the letter with given values."""
        letter_ids = list()
        process_letters = self
        for commkit in commkit_data.get("Responses", [commkit_data]):
            vals = self.json_to_data(commkit)
            published_state = "Published to Global Partner"
            is_published = vals.get("state") == published_state

            # Write/update letter
            kit_identifier = vals.get("kit_identifier")
            letter = self.search([("kit_identifier", "=", kit_identifier)])
            if letter:
                # Avoid to publish twice a same letter
                is_published = is_published and letter.state != published_state
                if is_published or letter.state != published_state:
                    letter._process_gmc_text(vals)
                    letter.write(vals)
            else:
                if "id" in vals:
                    del vals["id"]
                letter = self.create(vals)

            if is_published:
                process_letters += letter

            letter_ids.append(letter.id)

        process_letters.create_text_boxes()
        process_letters.publish_b2s_letter()
        return letter_ids

    def on_send_to_connect(self):
        """
        Method called before Letter is sent to GMC.
        Upload the image to Persistence if not already done.
        """
        onramp = SBCConnector(self.env)
        for letter in self.filtered(lambda letter: not letter.original_letter_url):
            letter.original_letter_url = onramp.send_letter_image(
                letter.get_pdf(), letter.letter_format, base64encoded=False
            )

    def enrich_letter(self, vals):
        """
        Enrich correspondence data with GMC data after CommKit Submission.
        Check that we received a valid kit identifier.
        """
        if vals.get("kit_identifier", "null") == "null":
            raise UserError(
                _(
                    "No valid kit id was returned. This is most "
                    "probably because the sponsorship is not known."
                )
            )
        # Avoid overriding the template of the letter
        if "template_id" in vals:
            del vals["template_id"]
        return self.write(vals)

    def publish_b2s_letter(self):
        """Method called when new B2S letter is Published."""
        _logger.info(
            "New B2S letter published for children %s",
            ", ".join(self.mapped("child_id.local_id")),
        )

    def get_pdf(self):
        """
        Retrieves the PDF of the letter, trying different sources in order.
        1. Returns the already stored PDF if available.
        2. Generates a new PDF from pages if they exist.
        3. Downloads the PDF from a remote service as a last resort.
        """
        self.ensure_one()
        if self.sponsor_letter_scan:
            return base64.b64decode(self.sponsor_letter_scan)

        if self.page_ids:
            return self.env["ir.actions.report"]._render_qweb_pdf(
                "sbc_compassion.report_correspondence", self.ids
            )[0]

        self.attach_b2s_pdf()
        return base64.b64decode(self.sponsor_letter_scan or b"")

    def hold_letters(self, message="Project suspended"):
        """Prevents to send S2B letters to GMC."""
        self.write({"state": "Exception"})
        for letter in self:
            letter.message_post(body=_("Letter was put on hold"), subject=message)
        gmc_action = self.env.ref("sbc_compassion.create_letter")
        gmc_messages = self.env["gmc.message"].search(
            [
                ("action_id", "=", gmc_action.id),
                ("object_id", "in", self.ids),
                ("state", "in", ["new", "failure", "odoo_failure"]),
            ]
        )
        gmc_messages.write({"state": "postponed"})

    def reactivate_letters(self, message="Project reactivated"):
        """Release the hold on S2B letters."""
        self.write({"state": "Received in the system"})
        for letter in self:
            letter.message_post(body=_("The letter can now be sent."), subject=message)
        gmc_action = self.env.ref("sbc_compassion.create_letter")
        gmc_messages = self.env["gmc.message"].search(
            [
                ("action_id", "=", gmc_action.id),
                ("object_id", "in", self.ids),
                ("state", "=", "postponed"),
            ]
        )
        gmc_messages.write({"state": "new"})
        gmc_messages.process_messages()

    def _get_file_name(self):
        self.ensure_one()
        name = ""
        if self.communication_type_ids.ids:
            name = (
                self.communication_type_ids[0]
                .with_context(lang=self.partner_id.lang)
                .name
                + " "
            )
        name += self.child_id.local_id
        if self.kit_identifier:
            name += " " + self.kit_identifier
        name += "." + (self.letter_format or "pdf")
        return name

    def data_to_json(self, mapping_name=None):
        json_data = super().data_to_json(mapping_name)

        # Remove unnecessary fields
        for key in ["Status", "SBCTypes", "MarkedForRework", "TranslationLanguage"]:
            json_data.pop(key, None)

        # Convert GlobalPartner to dict if present
        if "GlobalPartner" in json_data:
            json_data["GlobalPartner"] = {"Id": json_data["GlobalPartner"]}

        pages = json_data.get("Pages", [])
        if not isinstance(pages, list):
            pages = [pages]

        # Aggregate page texts
        english_text = "".join(
            "".join(page.get("EnglishTranslatedText", "")) for page in pages
        )
        translated_text = "".join(
            "".join(page.get("TranslatedText", "")) for page in pages
        )
        original_text = "".join("".join(page.get("OriginalText", "")) for page in pages)

        # Assign EnglishTranslatedText if missing
        if not english_text:
            if translated_text:
                for page in pages:
                    page["EnglishTranslatedText"] = page.get("TranslatedText", "")
            elif original_text and self.original_language_id.code_iso == "eng":
                for page in pages:
                    page["EnglishTranslatedText"] = page.get("OriginalText", "")

        # Update GlobalPartnerSBCId if present
        if "GlobalPartnerSBCId" in json_data:
            json_data["GlobalPartnerSBCId"] += str(self.resubmit_id)

        return json_data

    @api.model
    def json_to_data(self, json, mapping_name=None):
        template_name = json.pop("Template", "CH-A-6S11-1")
        odoo_data = super().json_to_data(json, mapping_name)

        if not template_name.startswith("CH"):
            template = self.env["correspondence.template"].search(
                [("name", "like", "L" + template_name[5]), ("name", "like", "B2S")],
                limit=1,
            )
            odoo_data["template_id"] = template.id

        if "child_id" in odoo_data and "partner_id" in odoo_data:
            partner = odoo_data.get("partner_id")
            child = odoo_data.pop("child_id")
            sponsorship = self.env["recurring.contract"].search(
                [
                    ("correspondent_id", "=", partner),
                    ("child_id", "=", child),
                ],
                limit=1,
            )
            if sponsorship:
                odoo_data["sponsorship_id"] = sponsorship.id

        if odoo_data.get("direction") == "Supporter To Beneficiary":
            # Remove empty texts to ensure we don't delete any local content
            all_page_vals = odoo_data.get("page_ids", [])
            to_remove = []
            for page_vals in all_page_vals:
                if isinstance(page_vals, tuple) and len(page_vals) == 3:
                    page_data = page_vals[2]
                    if isinstance(page_data, dict):
                        for field in [
                            "original_text",
                            "english_text",
                            "translated_text",
                        ]:
                            if field in page_data and not page_data[field]:
                                del page_data[field]
                        if not page_data:
                            to_remove.append(page_vals)
            for page_vals in to_remove:
                all_page_vals.remove(page_vals)

        return odoo_data

    def resubmit_letter(self):
        for letter in self:
            letter.write(
                {
                    "kit_identifier": False,
                    "resubmit_id": letter.resubmit_id + 1,
                    "state": "Received in the system",
                }
            )
        self.create_commkit().process_messages()

    def quality_check_failed(self):
        return self.write(
            {
                "state": "Quality check unsuccessful",
            }
        )

    def create_text_boxes(self):
        paragraphs = self.env["correspondence.paragraph"].with_context(
            from_correspondence_text=True
        )

        for page in self.mapped("page_ids"):
            # Check if there is any non-empty text
            if page.original_text or page.english_text or page.translated_text:
                # Split the text boxes
                original_boxes = (page.original_text or "").split(BOX_SEPARATOR)
                english_boxes = (page.english_text or "").split(BOX_SEPARATOR)
                translated_boxes = (page.translated_text or "").split(BOX_SEPARATOR)
                nb_paragraphs = max(
                    len(original_boxes), len(english_boxes), len(translated_boxes)
                )

                # Initialize a flag to check if there are changes
                data_changed = False

                # Compare existing paragraphs with new data
                for i in range(nb_paragraphs):
                    original_text = original_boxes[i] if len(original_boxes) > i else ""
                    english_text = english_boxes[i] if len(english_boxes) > i else ""
                    translated_text = (
                        translated_boxes[i] if len(translated_boxes) > i else ""
                    )

                    # Compare new data with existing data
                    if i < len(page.paragraph_ids):
                        para = page.paragraph_ids[i]
                        if (
                            para.original_text != original_text
                            or para.english_text != english_text
                            or para.translated_text != translated_text
                        ):
                            data_changed = True
                            break
                    else:
                        if original_text or english_text or translated_text:
                            data_changed = True
                            break

                if data_changed:
                    # Unlink existing paragraphs if new data is different
                    page.paragraph_ids.unlink()

                    # Create new paragraphs
                    for i in range(nb_paragraphs):
                        paragraphs.create(
                            {
                                "page_id": page.id,
                                "original_text": original_boxes[i]
                                if len(original_boxes) > i
                                else "",
                                "english_text": english_boxes[i]
                                if len(english_boxes) > i
                                else "",
                                "translated_text": translated_boxes[i]
                                if len(translated_boxes) > i
                                else "",
                                "sequence": i,
                            }
                        )
            # T1676 : Each page should contains at least one textbox (paragraph)
            if len(page.paragraph_ids) == 0:
                paragraphs.create(
                    {
                        "page_id": page.id,
                        "sequence": 0,
                    }
                )

        return paragraphs

    def get_base_url(self):
        # Use external URL for letter access
        return self.env["ir.config_parameter"].sudo().get_param("web.external.url", "")

    def _make_activity(self, state, user_id):
        self.ensure_one()
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=state,
            user_id=user_id,
            note=f"Letter has {state}",
        )

    def _process_gmc_text(self, letter_vals):
        """T1602 T2162 Checks if the text will be erased when saving the letter.
        GMC sends back the text content but with incorrect formatting or empty content.
        We always keep the text that is already stored in the database and only look
        for new text to be added (mostly translations made by Field Offices).

        Args:
            letter_vals: A dictionary containing correspondence values like
            {'page_ids': [(0, 0, {'english_text': 'example'}]}.

        Returns:
            None. The letter_vals dictionary is modified in place, like this:
            {'english_text': 'example'}.
        """
        self.ensure_one()
        page_commands = letter_vals.get("page_ids")
        if (
            not page_commands
            or not isinstance(page_commands, list)
            or not any((self.english_text, self.original_text, self.translated_text))
        ):
            return

        # Remove the clear command (5, 0, 0)
        page_commands.remove((5, 0, 0))
        text_fields = ["original_text", "english_text", "translated_text"]
        merged_text = defaultdict(str)

        for page_index, command in enumerate(page_commands.copy()):
            if isinstance(command, tuple) and len(command) == 3:
                page_vals = command[2]
                if not isinstance(page_vals, dict):
                    continue
                for field in text_fields:
                    if page_vals.get(field):
                        merged_text[field] += page_vals.pop(field) + PAGE_SEPARATOR
                if not page_vals:
                    page_commands.remove(command)
                else:
                    page_id = self.page_ids[page_index : page_index + 1].id
                    if page_id:
                        page_commands[page_index] = (1, page_id, page_vals)

        for field, text in merged_text.items():
            strip_text = html2plaintext(text.rstrip(PAGE_SEPARATOR))
            if strip_text and not getattr(self, field, False):
                letter_vals[field] = strip_text

        if not page_commands:
            letter_vals.pop("page_ids", None)

    def get_attachments_per_page(self, flatten=False):
        """
        Used for the S2B report generation
        We group 4 attachements per page, 2 per row.
        We also convert them on the fly to jpg small size image.
        :param flatten: If True, we return a flat list of images
        """
        self.ensure_one()
        attachments = self.original_attachment_ids.filtered(
            lambda a: a.mimetype.startswith("image")
        )
        images = {0: {0: []}}
        page, row = 0, 0

        for attachment in attachments:
            img_data = image_process(
                base64.b64decode(attachment.datas), size=(400, 400), quality=75
            )
            images[page][row].append(base64.b64encode(img_data))
            if len(images[page][row]) == 2:
                row += 1
                images[page][row] = []

            if row == 2:
                page += 1
                row = 0
                images[page] = {row: []}

        if flatten:
            flat_images = []
            for page in images.values():
                for row in page.values():
                    flat_images.extend(row)
            return flat_images
        return images

    def spread_text_to_pages(self):
        """
        Used for the report generation.
        We spread the text to the pages to be used in the report
        depending on the text box sizes.
        """
        self.ensure_one()
        fields_to_check = ["original_text", "english_text", "translated_text"]
        new_page = self.env["correspondence.page"]

        for field in fields_to_check:
            overflow = ""
            for page in self.page_ids:
                overflow = self._process_page_text(page, field, overflow)

            if overflow:
                new_page = self._create_new_page(new_page, field, overflow)

        if new_page:
            self.spread_text_to_pages()

        return True

    def _process_page_text(self, page, field, overflow):
        for paragraph in page.paragraph_ids:
            if overflow:
                overflow = self._handle_overflow(paragraph, field, overflow)
            else:
                text, overflow = paragraph.check_overflow(field)
                if overflow:
                    paragraph[field] = text
        return overflow

    def _handle_overflow(self, paragraph, field, overflow):
        text_box = paragraph.get_text_box(field)
        total_length = len(overflow) + len(paragraph[field]) + (text_box.line_size or 0)

        if total_length <= (text_box.max_chars or 0):
            paragraph[field] = f"{overflow}\n\n{paragraph[field]}"
            overflow = ""
        else:
            next_box_text = paragraph[field]
            paragraph[field] = overflow
            text, overflow = paragraph.check_overflow(field)
            if overflow:
                overflow = f"{overflow}\n\n{next_box_text}"
                paragraph[field] = text
            else:
                overflow = next_box_text
        return overflow

    def _create_new_page(self, new_page, field, overflow):
        if new_page:
            new_page.paragraph_ids[0][field] = overflow
        else:
            new_page = self.env["correspondence.page"].create(
                {
                    "correspondence_id": self.id,
                    "paragraph_ids": [(0, 0, {field: overflow})],
                }
            )
        return new_page

    @api.model
    def check_postponed_christmas_letters(self):
        if self.env["res.config.settings"].is_in_christmas_period(
            datetime.date.today()
        ):
            correspondences = self.env["correspondence"].search(
                [
                    ("template_id.is_christmas_letter", "=", True),
                    ("kit_identifier", "=", False),
                    ("state", "=", "Exception"),
                ]
            )
            correspondences.reactivate_letters(_("Christmas period started"))

    @api.model
    def _compress_pdf(self, letter_data):
        """Compress PDF data to reduce size using Ghostscript.

        If the PDF size is larger than 1MB, a compression is applied.
        :param letter_data: binary (b64decoded) PDF data
        :return: compressed PDF data if needed
        """
        if len(letter_data) <= 1024 * 1024:  # 1MB
            return letter_data

        if not shutil.which("gs"):
            _logger.warning("Ghostscript ('gs') not found, skipping PDF compression.")
            return letter_data

        command = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/ebook",  # Preset for good quality and size.
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-sOutputFile=-",  # Write to stdout
            "-",  # Read from stdin
        ]

        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            compressed_blob, stderr = process.communicate(input=letter_data)

            if process.returncode != 0:
                _logger.error(f"Ghostscript failed with error: {stderr.decode()}")
                return letter_data  # Return original data on failure

            if len(compressed_blob) < len(letter_data):
                _logger.info(
                    f"PDF compressed with Ghostscript from "
                    f"{len(letter_data)} to {len(compressed_blob)} bytes."
                )
                return compressed_blob
            else:
                _logger.info(
                    "Ghostscript compression did not reduce file size. "
                    "Returning original."
                )
                return letter_data

        except (OSError, subprocess.SubprocessError) as e:
            _logger.error(f"Failed to run Ghostscript for PDF compression: {e}")
            return letter_data

    def attach_b2s_pdf(self):
        """Download letter image from US service and attach to letter."""
        for letter in self:
            # Download and store letter
            letter_url = letter.final_letter_url or letter.original_letter_url
            if letter_url:
                image_data = SBCConnector(self.env).get_letter_image(
                    letter_url, {"dpi": 96, "format": "pdf", "pg": 0}
                )
                if image_data:
                    letter.sponsor_letter_scan = image_data

    @api.model
    def cron_download_old_correspondence(self):
        """Make sure letters older than 9 years are downloaded locally
        if the sponsorship is still active (GMC retention policy is 10 years)"""
        nine_years_ago = fields.Date.today() - relativedelta(years=9)
        correspondences = self.search(
            [
                ("state", "=", "Published to Global Partner"),
                ("sponsorship_id.state", "=", "active"),
                ("scanned_date", "<=", nine_years_ago),
                ("sponsor_letter_scan", "=", False),
            ],
        )
        _logger.info("Downloading %d old letters", len(correspondences))
        correspondences.delayable()._download_old_correspondence().set(
            priority=500,
            channel="root.sbc_compassion",
        ).split(10).delay()

    def _download_old_correspondence(self):
        for correspondence in self:
            letter_data = correspondence.get_pdf()
            if letter_data:
                correspondence.sponsor_letter_scan = base64.b64encode(letter_data)
                _logger.info(f"Downloaded letter {correspondence.kit_identifier}")
            else:
                _logger.warning(
                    f"Failed to download letter {correspondence.kit_identifier}"
                )

    def _fix_missing_pages(self):
        if not self:
            return

        update_letter_action = self.env.ref("sbc_compassion.update_letter")
        letter_ids_str = [str(lid) for lid in self.ids]

        # Perform a single, more efficient search for all letters in self
        messages = self.env["gmc.message"].search(
            [
                ("action_id", "=", update_letter_action.id),
                ("state", "=", "success"),
                ("object_ids", "in", letter_ids_str),
                ("content", "like", "Published to Global Partner"),
            ]
        )

        # Group messages by letter ID for quick lookup
        messages_by_letter_id = {}
        for msg in messages:
            try:
                letter_id = int(msg.object_ids)
                if letter_id not in messages_by_letter_id:
                    messages_by_letter_id[letter_id] = msg
            except (ValueError, TypeError):
                continue

        for letter in self:
            content = {}
            number_pages = 0
            try:
                message = messages_by_letter_id[letter.id]
                content = json.loads(message.content)
                number_pages = len(content.get("Pages", []))
                if not number_pages:
                    raise ValueError("No pages found in GMC content")

                _logger.info(
                    "Restoring %s pages for letter %s from message %s",
                    number_pages,
                    letter.id,
                    message.id,
                )
                page_vals = letter.json_to_data(content).get("page_ids")
                write_vals = {
                    "page_ids": page_vals,
                    "cloudinary_final_letter_url": content.get("CloudinaryFinalURL"),
                    "cloudinary_original_letter_url": content.get(
                        "CloudinaryOriginalURL"
                    ),
                }
                letter.write(write_vals)

            except (json.JSONDecodeError, ValueError, KeyError, UserError):
                cloudinary_final = content.get("CloudinaryFinalURL")
                if not cloudinary_final or not number_pages:
                    letter.attach_b2s_pdf()
                if cloudinary_final:
                    letter._create_missing_pages(number_pages)
                    letter.cloudinary_final_letter_url = cloudinary_final
                    letter.sponsor_letter_scan = False

    def _create_missing_pages(self, number_pages=0):
        self.ensure_one()
        if self.page_ids:
            return
        if self.sponsor_letter_scan and not number_pages:
            attachment = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "correspondence"),
                    ("res_field", "=", "sponsor_letter_scan"),
                    ("res_id", "=", self.id),
                ]
            )
            image_pdf = PdfFileReader(to_pdf_stream(attachment))
            number_pages = image_pdf.numPages
        for _i in range(number_pages):
            self.page_ids.create({"correspondence_id": self.id})
