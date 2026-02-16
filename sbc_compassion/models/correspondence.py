##############################################################################
#
#    Copyright (C) 2014-2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Emmanuel Mathier
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import datetime
import logging
import shutil
import subprocess
import threading
import uuid
from collections import defaultdict
from io import BytesIO

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

from ..tools.onramp_connector import SBCConnector
from .correspondence_page import BOX_SEPARATOR, PAGE_SEPARATOR

_logger = logging.getLogger(__name__)

try:
    import magic
    from PyPDF2 import PdfFileReader
    from wand.image import Image
except ImportError:
    _logger.error("Please install magic, PyPDF2 and wand in order to use SBC module")

DEFAULT_LETTER_DPI = 100


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
        domain=[("state", "not in", ["draft", "cancelled"])],
        tracking=True,
        readonly=False,
    )
    name = fields.Char(compute="_compute_name", store=True)
    partner_id = fields.Many2one(
        "res.partner", "Partner", readonly=False, ondelete="restrict"
    )
    child_id = fields.Many2one(
        related="sponsorship_id.child_id", store=True, readonly=False
    )
    # Field used for identifying correspondence by GMC
    kit_identifier = fields.Char("Kit id", copy=False, readonly=True, tracking=True)
    direction = fields.Selection(
        selection=[
            ("Supporter To Beneficiary", _("Supporter to participant")),
            ("Beneficiary To Supporter", _("Participant to supporter")),
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
        readonly=True,
    )
    s2b_state = fields.Selection(
        [
            ("Received in the system", _("Scanned in")),
            ("Global Partner translation queue", _("To Translate")),
            ("Global Partner translation process", _("Translating")),
            ("Quality check queue", _("Quality Check Queue")),
            ("Quality check process", _("Quality Check Process")),
            ("Translation and quality check complete", _("Quality Check Done")),
            ("Field Office translation queue", _("National Office Translation Queue")),
            ("Composition process", _("Composition Process")),
            ("Printed and sent to ICP", _("Sent to FCP")),
            ("Exception", _("Exception")),
            ("Quality check unsuccessful", _("Quality check failed")),
            ("Translation check unsuccessful", _("Translation check unsuccessful")),
        ],
        compute="_compute_states",
    )
    b2s_state = fields.Selection(
        [
            ("Ready to be printed", _("Ready to be printed")),  # *
            (
                "Field Office transcribing translation and content check process",
                _("National Office content check"),
            ),  # *
            ("Field Office translation queue", _("National Office Translation Queue")),
            ("In Translation", _("SDL FO Translation")),  # *
            ("Quality check queue", _("Quality Check Queue")),
            ("Quality check process", _("Quality Check Process")),
            ("Translation and quality check complete", _("Quality Check Done")),  # *
            ("Global Partner translation queue", _("To Translate")),
            ("Global Partner translation process", _("Translating")),
            ("Composition process", _("Composition Process")),
            ("Published to Global Partner", _("Published")),
            ("Quality check unsuccessful", _("Quality check unsuccessful")),
            ("Translation check unsuccessful", _("Translation check unsuccessful")),
            ("Exception", _("Exception")),
        ],
        compute="_compute_states",
    )
    state = fields.Selection(
        "get_states", default="Received in the system", tracking=True
    )
    email_read = fields.Datetime()

    # 2. Attachments and scans
    ##########################
    # Whether the pdf should be stored on creation or generated when needed
    store_letter_image = fields.Boolean("Store PDF letter", default=True)
    letter_image = fields.Binary()
    file_name = fields.Char()
    letter_format = fields.Selection(
        [("pdf", "pdf"), ("tiff", "tiff"), ("zip", "zip")],
        compute="_compute_letter_format",
        store=True,
    )
    preferred_dpi = fields.Integer(
        compute="_compute_preferred_dpi", help="Resolution of fetched PDF"
    )

    # 3. Letter language, text information, attached images
    #######################################################
    supporter_languages_ids = fields.Many2many(
        "res.lang.compassion", related="partner_id.spoken_lang_ids", readonly=True
    )
    beneficiary_language_ids = fields.Many2many(
        "res.lang.compassion",
        compute="_compute_beneficiary_language_ids",
        readonly=True,
    )
    # First spoken lang of partner
    original_language_id = fields.Many2one(
        "res.lang.compassion", "Original language", readonly=False
    )
    translation_language_id = fields.Many2one(
        "res.lang.compassion", "Translation language", readonly=False, tracking=True
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
        readonly=True,
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
    template_id = fields.Many2one("correspondence.template", "Template", readonly=False)

    # 4. Additional information
    ###########################
    status_date = fields.Datetime(default=fields.Datetime.now)
    scanned_date = fields.Date(default=fields.Date.today)
    relationship = fields.Selection(
        [
            ("Sponsor", _("Sponsor")),
            ("Encourager", _("Encourager")),
            ("Correspondent", _("Correspondent")),
        ],
        default="Sponsor",
    )
    is_first_letter = fields.Boolean(
        compute="_compute_is_first",
        store=True,
        readonly=True,
        string="First letter from Participant",
    )
    marked_for_rework = fields.Boolean(readonly=True)
    rework_reason = fields.Char()
    rework_comments = fields.Text()
    original_letter_url = fields.Char()
    final_letter_url = fields.Char()
    import_id = fields.Many2one("import.letters.history", readonly=False)
    translator = fields.Char()
    email = fields.Char(related="partner_id.email")
    sponsorship_state = fields.Selection(
        related="sponsorship_id.state", string="Sponsorship state", readonly=True
    )
    is_final_letter = fields.Boolean(compute="_compute_is_final_letter")
    generator_id = fields.Many2one("correspondence.s2b.generator", readonly=False)
    resubmit_id = fields.Integer(default=1)

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
            _("The kit id already exists in database."),
        ),
        (
            "uuid",
            "unique(uuid)",
            _("The uuid already exists in database."),
        ),
    ]
    # Lock
    #######
    process_lock = threading.Lock()

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
                letter.name = _("New correspondence")

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

    @api.depends("letter_image")
    def _compute_letter_format(self):
        for letter in self.filtered("letter_image"):
            if self.store_letter_image:
                ftype = magic.from_buffer(base64.b64decode(letter.letter_image), True)
                if "pdf" in ftype:
                    letter.letter_format = "pdf"
                elif "tiff" in ftype:
                    letter.letter_format = "tiff"
                elif "zip" in ftype:
                    letter.letter_format = "zip"
            else:
                letter.letter_format = "pdf"

    def _get_uuid(self):
        return str(uuid.uuid4())

    def _compute_is_final_letter(self):
        for letter in self:
            letter.is_final_letter = (
                "Final Letter" in letter.communication_type_ids.mapped("name")
                or letter.sponsorship_state != "active"
            )

    def _compute_preferred_dpi(self):
        for letter in self:
            letter.preferred_dpi = DEFAULT_LETTER_DPI

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
            letter.read_url = f"{letter.get_base_url()}/b2s_image?id={letter.uuid}"

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """Fill missing fields.
        The field `letter_image` is a binary and will be stored in an ir.attachment
        If `stored_letter_image` is set to False, `letter_image` is dropped and PDFs
        will be generated when requested using the template and
        """
        if (
            vals.get("direction", "Supporter To Beneficiary")
            == "Supporter To Beneficiary"
        ):
            vals["communication_type_ids"] = [
                (4, self.env.ref("sbc_compassion.correspondence_type_supporter").id)
            ]
            if not vals.get("translation_language_id"):
                vals["translation_language_id"] = vals.get("original_language_id")
        else:
            vals["status_date"] = fields.Datetime.now()
            if "communication_type_ids" not in vals:
                vals["communication_type_ids"] = [
                    (4, self.env.ref("sbc_compassion.correspondence_type_scheduled").id)
                ]
            # Allows manually creating a B2S letter
            if vals.get("state", "Received in the system") == "Received in the system":
                vals["state"] = "Published to Global Partner"

        if vals.get("store_letter_image", True) is False:
            vals["letter_image"] = False

        contract = self.env["recurring.contract"].browse(vals["sponsorship_id"])
        if vals.get("direction") == "Supporter To Beneficiary":
            contract.last_sponsor_letter = fields.Date.today()

        if "partner_id" not in vals:
            vals["partner_id"] = contract.correspondent_id.id

        type_ = ".pdf"
        letter_data = False
        if vals.get("letter_image"):
            letter_data = base64.b64decode(vals["letter_image"])
            vals["letter_image"] = base64.b64encode(self._compress_pdf(letter_data))
            ftype = magic.from_buffer(letter_data, True).lower()
            if "pdf" in ftype:
                type_ = ".pdf"
            elif "tiff" in ftype:
                type_ = ".tiff"
            else:
                raise UserError(_("You can only attach tiff or pdf files"))

        letter = super().create(vals)
        letter.file_name = letter._get_file_name()
        # Set the correct number of pages
        if letter_data and type_ == ".pdf":
            image_pdf = PdfFileReader(BytesIO(letter_data))
            if letter.nbr_pages < image_pdf.numPages:
                for _i in range(letter.nbr_pages, image_pdf.numPages):
                    letter.page_ids.create({"correspondence_id": letter.id})

        # T1676 : Each page should contains at least one textbox (paragraph)
        letter.create_text_boxes()
        # Make sure the translation language is set correctly.
        letter._check_translation_language()
        if not self.env.context.get("no_comm_kit"):
            letter.create_commkit()

        return letter

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
        if "letter_image" in vals and self.store_letter_image is False:
            vals["letter_image"] = False
        if vals.get("letter_image"):
            # Compress the PDF if it is a PDF
            vals["letter_image"] = base64.b64encode(
                self._compress_pdf(base64.b64decode(vals["letter_image"]))
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
    def create_commkit(self):
        valid_christmas_period = self.env["res.config.settings"].is_in_christmas_period(
            datetime.date.today()
        )
        messages = self.env["gmc.message"]
        for letter in self:
            action = self.env.ref("sbc_compassion.create_letter")
            message_vals = {
                "action_id": action.id,
                "object_id": letter.id,
                "child_id": letter.child_id.id,
                "partner_id": letter.partner_id.id,
                "direction": action.direction
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

    def compose_letter_button(self):
        """Remove old images, download original and compose translation."""
        self.ensure_one()

        try:
            self.attach_original()
            compose_success = self.compose_letter_image()

        except Exception:
            # Manage error if an exception is raised during compose_letter_image process
            self.with_user(SUPERUSER_ID).with_delay(
                channel="root.sbc_compassion",
                description="Handle failure after technical exception",
            )._handle_compose_letter_failure()

            # Rerun the exception so that the job is marked as “Failed” in the queue
            raise

        if compose_success is True:
            # Everything went well, we'll send the email.
            self.with_user(SUPERUSER_ID).with_delay(
                channel="root.partner_communication",
                priority=100,
                description="Send B2S letter communication",
            ).send_communication()

        else:
            # Logical failure during compose_letter_image process
            # (template or image missing)
            # Manage error because something failed in
            # compose_letter_image process (function returned false)
            self.with_user(SUPERUSER_ID).with_delay(
                channel="root.sbc_compassion",
                priority=10,
                description="Handle failure after logical failure (returned False)",
            )._handle_compose_letter_failure()

        # Return True so that Job 1 is marked “Done” in the queue
        # in case of success or logical failure.
        return True

    def send_communication(self):
        """Sends the letter to the sponsor via email.
        Can be implemented by modules inheriting from this one."""
        pass

    def compose_letter_image(self):
        """
        Puts the translated text of a letter inside the original image given
        the child letter layout.
        :return: True if the composition succeeded, False otherwise
        """
        self.ensure_one()

        template = self.template_id.with_context(lang=self.partner_id.lang)
        image_data = self.get_image()
        if not template or not image_data:
            return False
        source_text, text_boxes = self._get_translation_boxes()
        # Extract pages and additional images
        pages = []
        images = []
        with Image(blob=image_data, resolution=self.preferred_dpi) as page_image:
            for i in page_image.sequence:
                pages.append(base64.b64encode(Image(i).make_blob("jpg")))
                # For additional pages, check if the page contains text.
                # If not, it is considered as a picture attachment.
                if i.index > 1:
                    text = ""
                    if len(self.page_ids) >= i.index + 1:
                        text = getattr(self.page_ids[i.index], source_text, "")
                    if len(text.strip()) < 5:
                        images.append(pages.pop(i.index - len(images)))

        pdf_out = template.generate_pdf(
            self.name, {}, {"Translation": text_boxes}, images, pages
        )
        if pdf_out:
            self.letter_image = base64.b64encode(pdf_out)

        return True

    def _handle_compose_letter_failure(self):
        # Mark as exception while keeping translation_status on ‘done’
        self.ensure_one()
        self.write({"state": "Exception"})

        config_settings = self.env["res.config.settings"].sudo()
        sds_partner_id = config_settings.get_param("letter_responsible", 0)
        sds_user = self.env.ref("base.user_admin")  # Fallback on admin user

        if sds_partner_id:
            # Find the right odoo user
            sds_user = (
                self.env["res.users"]
                .sudo()
                .search([("partner_id", "=", int(sds_partner_id))], limit=1)
            )

        self.activity_schedule(
            "mail.mail_activity_data_todo",
            date_deadline=fields.Date.today(),
            summary=f"Failure to generate B2S letter (PDF) ({self.name})",
            note=(
                f"The generation of the B2S letter **{self.name}** for the supporter "
                f"**{self.partner_id.name}** has failed. "
                "The PDF could not be generated and therefore the email was not sent."
            ),
            user_id=sds_user.id,
        )

    def _get_translation_boxes(self):
        """
         Used to fetch the translation of a letter and spread it into
        the translation boxes to be used in the composition of the letter
        done with FPDF.
        :return: field name used to fetch translation
                 (english_text/translated_text),
                 list of translation boxes (containing the translation text)
        """
        text_boxes = []
        paragraphs = self.page_ids.mapped("paragraph_ids")
        if self.translated_text:
            source = "translated_text"
            # In case the translated text is not the same as the english text
            # we want to filter page translations that are equal as the
            # english version, because the translator may have put all
            # translation in the same box. We want to avoid composing
            # English text when it's not expected
            if (
                "".join(self.translated_text.split())
                != "".join(self.english_text.split())
                and self.translation_language_id.code_iso != "eng"
            ):
                # Avoid capturing english text that hasn't been translated
                paragraphs = paragraphs.filtered(source).filtered(
                    lambda p: "".join((p.translated_text or "").split())
                    != "".join((p.english_text or "").split())
                )
        else:
            source = "english_text"
            # Avoid capturing translations that are the same text as the
            # original text.
            paragraphs = paragraphs.filtered(source).filtered(
                lambda p: "".join((p.english_text or "").split())
                != "".join((p.original_text or "").split())
            )
        if not getattr(self, source):
            return source, text_boxes

        # Get the text boxes separately
        text_pages = paragraphs.mapped(source)
        for index, text in enumerate(text_pages):
            # Skip pages that should not contain anything
            page_layout = self.template_id.page_ids.filtered(
                lambda p, index=index: p.page_index == index + 1
            )
            if not text.strip() and not page_layout.text_box_ids:
                continue
            text_boxes.append(text.strip())

        return source, text_boxes

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
                letter = self.with_context(no_comm_kit=True).create(vals)

            if is_published:
                process_letters += letter

            letter_ids.append(letter.id)

        process_letters.create_text_boxes()
        process_letters.process_letter()
        return letter_ids

    def on_send_to_connect(self):
        """
        Method called before Letter is sent to GMC.
        Upload the image to Persistence if not already done.
        """
        onramp = SBCConnector(self.env)
        for letter in self.filtered(lambda letter: not letter.original_letter_url):
            letter.original_letter_url = onramp.send_letter_image(
                letter.get_image(), letter.letter_format, base64encoded=False
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

    def process_letter(self):
        """Method called when new B2S letter is Published."""
        # If the letter's source language is known by the sponsor,
        # send the original letter without any translation
        letter_type = "final_letter_url"
        if self.original_language_id in self.supporter_languages_ids:
            letter_type = "original_letter_url"
        self.download_attach_letter_image(letter_type=letter_type)
        return True

    def download_attach_letter_image(self, letter_type="final_letter_url"):
        """Download letter image from US service and attach to letter."""
        for letter in self:
            # Download and store letter
            letter_url = getattr(letter, letter_type)
            image_data = None
            if letter_url:
                image_data = SBCConnector(self.env).get_letter_image(
                    letter_url, "pdf", dpi=letter.preferred_dpi
                )
            if image_data is None:
                raise UserError(
                    _("Image of letter %s was not found remotely.")
                    % letter.kit_identifier
                )
            letter.write(
                {"file_name": letter._get_file_name(), "letter_image": image_data}
            )

    def attach_original(self):
        self.download_attach_letter_image(letter_type="original_letter_url")
        return True

    def attach_final(self):
        self.download_attach_letter_image(letter_type="final_letter_url")
        return True

    def get_image(self):
        """Method for retrieving the image"""
        self.ensure_one()

        if not self.store_letter_image or not self.letter_image:
            return self.generate_original_pdf()

        return base64.b64decode(self.letter_image)

    def generate_original_pdf(self):
        """
        For S2B
        Generate a PDF with `template_id`, `original_attachment_ids` and `original_text`
        """
        self.ensure_one()
        sponsor = self.sponsorship_id.correspondent_id
        child = self.sponsorship_id.child_id
        pdf_name = self.name or _("Letter")

        header = (
            f"{sponsor.global_id} - {sponsor.preferred_name}\n"
            f"{child.local_id} - {child.preferred_name} - "
            f"{child.gender == 'F' and 'Female' or 'Male'} - {child.age}"
        )

        image_data = (
            self.mapped("original_attachment_ids").sorted("id").mapped("datas") or []
        )
        text_data = {"Original": [self.original_text]}
        if self.kit_identifier:
            # Only compose translation if the letter was already transmitted
            # to GMC (to avoid transmitting PDF with translation boxes filled)
            text_data["Translation"] = self._get_translation_boxes()[1]
        return self.template_id.generate_pdf(
            pdf_name, (header, ""), text_data, image_data
        )

    def download_pdf(self):
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/pdf/correspondence?object_id={self.id}",
            "target": "self",
        }

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

        for page in self.page_ids:
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

    ##########################################################################
    #                            PRIVATE METHODS                             #
    ##########################################################################

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
