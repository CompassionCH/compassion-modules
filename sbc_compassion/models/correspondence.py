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
import logging
import re
import threading
import uuid
from io import BytesIO

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import config
from .correspondence_page import BOX_SEPARATOR, PAGE_SEPARATOR
from ..tools.onramp_connector import SBCConnector

_logger = logging.getLogger(__name__)
test_mode = config.get("test_enable")

try:
    import magic
    from PyPDF2 import PdfFileReader
    from wand.image import Image
except ImportError:
    _logger.error("Please install magic, PyPDF2 and wand in order to use SBC module")


class CorrespondenceType(models.Model):
    _name = "correspondence.type"
    _description = "Type of correspondence"
    _inherit = "connect.multipicklist"
    res_model = "correspondence"
    res_field = "communication_type_ids"


class Correspondence(models.Model):
    """ This class holds the data of a Communication Kit between
    a child and a sponsor.
    """

    _name = "correspondence"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "correspondence.metadata",
        "translatable.model",
        "compassion.mapped.model",
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
        track_visibility="onchange",
        readonly=False,
    )
    name = fields.Char(compute="_compute_name")
    partner_id = fields.Many2one(
        "res.partner", "Partner", readonly=True, ondelete="restrict"
    )
    child_id = fields.Many2one(
        related="sponsorship_id.child_id", store=True, readonly=False
    )
    # Field used for identifying correspondence by GMC
    kit_identifier = fields.Char("Kit id", copy=False, readonly=True, track_visibility="onchange")
    direction = fields.Selection(
        selection=[
            ("Supporter To Beneficiary", _("Supporter to beneficiary")),
            ("Beneficiary To Supporter", _("Beneficiary to supporter")),
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
            ("Field Office translation queue", _("SDL FO Translation Queue")),
            ("Composition process", _("Composition Process")),
            ("Printed and sent to ICP", _("Sent to FCP")),
            ("Exception", _("Exception")),
            ("Quality check unsuccessful", _("Quality check failed")),
            ("Translation check unsuccessful", _("Translation check " "unsuccessful")),
        ],
        compute="_compute_states",
    )
    b2s_state = fields.Selection(
        [
            ("Ready to be printed", _("Ready to be printed")),  # *
            (
                "Field Office transcribing translation and content check " "process",
                _("FO content check"),
            ),  # *
            ("Field Office translation queue", _("SDL FO Translation Queue")),
            ("In Translation", _("SDL FO Translation")),  # *
            ("Quality check queue", _("Quality Check Queue")),
            ("Quality check process", _("Quality Check Process")),
            ("Translation and quality check complete", _("Quality Check Done")),  # *
            ("Global Partner translation queue", _("To Translate")),
            ("Global Partner translation process", _("Translating")),
            ("Composition process", _("Composition Process")),
            ("Published to Global Partner", _("Published")),
            ("Quality check unsuccessful", _("Quality check unsuccessful")),
            ("Translation check unsuccessful", _("Translation check " "unsuccessful")),
            ("Exception", _("Exception")),
        ],
        compute="_compute_states",
    )
    state = fields.Selection(
        "get_states", default="Received in the system", track_visibility="onchange"
    )
    email_read = fields.Datetime()

    # 2. Attachments and scans
    ##########################
    # Whether the pdf should be stored on creation or generated when needed
    store_letter_image = fields.Boolean("Store PDF letter", default=True)
    letter_image = fields.Binary(attachment=True)
    b64image = fields.Binary(compute="_compute_b64_image")
    file_name = fields.Char()
    letter_format = fields.Selection(
        [("pdf", "pdf"), ("tiff", "tiff"), ("zip", "zip")],
        compute="_compute_letter_format",
        store=True,
    )

    # 3. Letter language, text information, attached images
    #######################################################
    supporter_languages_ids = fields.Many2many(
        related="partner_id.spoken_lang_ids", readonly=True
    )
    beneficiary_language_ids = fields.Many2many(
        related="child_id.project_id.field_office_id.spoken_language_ids", readonly=True
    )
    # First spoken lang of partner
    original_language_id = fields.Many2one(
        "res.lang.compassion", "Original language", readonly=False
    )
    translation_language_id = fields.Many2one(
        "res.lang.compassion", "Translation language", readonly=False
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
        ondelete="cascade",
        string="Attached images",
    )
    page_ids = fields.One2many(
        "correspondence.page", "correspondence_id", readonly=False
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
        [("Sponsor", _("Sponsor")), ("Encourager", _("Encourager"))], default="Sponsor"
    )
    is_first_letter = fields.Boolean(
        compute="_compute_is_first",
        store=True,
        readonly=True,
        string="First letter from Beneficiary",
    )
    marked_for_rework = fields.Boolean(readonly=True)
    rework_reason = fields.Char()
    rework_comments = fields.Text()
    original_letter_url = fields.Char()
    final_letter_url = fields.Char()
    import_id = fields.Many2one("import.letters.history", readonly=False)
    translator = fields.Char()
    translator_id = fields.Many2one(
        "res.partner",
        "Local translator",
        compute="_compute_translator",
        inverse="_inverse_set_translator",
        store=True,
        readonly=False,
    )
    email = fields.Char(related="partner_id.email")
    translate_date = fields.Datetime()
    sponsorship_state = fields.Selection(
        related="sponsorship_id.state", string="Sponsorship state", readonly=True
    )
    is_final_letter = fields.Boolean(compute="_compute_is_final_letter")
    generator_id = fields.Many2one("correspondence.s2b.generator", readonly=False)
    resubmit_id = fields.Integer(default=1)

    # Letter remote access
    ######################
    uuid = fields.Char(required=True, default=lambda self: self._get_uuid())
    read_url = fields.Char()

    # 5. SQL Constraints
    ####################
    _sql_constraints = [
        (
            "kit_identifier",
            "unique(kit_identifier)",
            _("The kit id already exists in database."),
        )
    ]
    # Lock
    #######
    process_lock = threading.Lock()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def get_states(self):
        """ Returns all the possible states. """
        return list(
            set(self._fields["s2b_state"].selection)
            | set(self._fields["b2s_state"].selection)
        )

    @api.multi
    def _compute_states(self):
        """ Sets the internal states (s2b and b2s). """
        for letter in self:
            if letter.direction == "Supporter To Beneficiary":
                letter.s2b_state = letter.state
            else:
                letter.b2s_state = letter.state

    @api.multi
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
            ("Beneficiary Initiated Letter", _("Beneficiary Initiated")),
            ("Final Letter", _("Final Letter")),
            ("Large Gift Thank You Letter", _("Large Gift Thank You")),
            ("Small Gift Thank You Letter", _("Small Gift Thank You")),
            ("New Sponsor Letter", _("New Sponsor Letter")),
            ("Reciprocal Letter", _("Reciprocal Letter")),
            ("Scheduled Letter", _("Scheduled")),
            ("Supporter Letter", _("Supporter Letter")),
        ]

    @api.multi
    @api.depends("sponsorship_id")
    def _compute_name(self):
        for letter in self:
            if letter.sponsorship_id and letter.communication_type_ids:
                letter.name = (
                    letter.communication_type_ids[0].name
                    + " ("
                    + letter.sponsorship_id.partner_id.ref
                    + " - "
                    + letter.child_id.local_id
                    + ")"
                )
            else:
                letter.name = _("New correspondence")

    @api.depends("sponsorship_id")
    def _set_partner_review(self):
        for letter in self:
            if letter.partner_id.mandatory_review:
                letter.mandatory_review = True

    @api.depends("page_ids")
    def _compute_original_text(self):
        for letter in self:
            letter.original_text = letter._get_text("original_text")

    @api.depends("page_ids")
    def _compute_translated_text(self):
        for letter in self:
            letter.translated_text = letter._get_text("translated_text")

    @api.depends("page_ids")
    def _compute_english_text(self):
        for letter in self:
            letter.english_text = letter._get_text("english_text")

    @api.depends("page_ids")
    def _compute_nbr_pages(self):
        for letter in self:
            letter.nbr_pages = len(letter.page_ids)

    @api.multi
    def _inverse_original(self):
        self._set_text("original_text", self.original_text)

    @api.multi
    def _inverse_english(self):
        self._set_text("english_text", self.english_text)

    @api.multi
    def _inverse_translated(self):
        self._set_text("translated_text", self.translated_text)

    @api.multi
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
                        setattr(letter.page_ids[i], field, pages_text[i].strip("\n"))
                else:
                    for i in range(0, len(letter.page_ids)):
                        setattr(letter.page_ids[i], field, pages_text[i].strip("\n"))
                    last_page_text = getattr(letter.page_ids[i], field)
                    last_page_text += "\n\n" + "\n\n".join(pages_text[i + 1:])
                    setattr(letter.page_ids[i], field, last_page_text)
            else:
                for i in range(0, len(pages_text)):
                    letter.page_ids.create(
                        {
                            field: pages_text[i].strip("\n"),
                            "correspondence_id": letter.id,
                        }
                    )

    def _get_text(self, source_text):
        """ Gets the desired text (original/translated) from the pages. """
        txt = self.page_ids.filtered(source_text).mapped(source_text)
        return ("\n" + PAGE_SEPARATOR + "\n").join(txt)

    def _change_language(self):
        return True

    @api.multi
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

    @api.multi
    @api.depends("translator")
    def _compute_translator(self):
        partner_obj = self.env["res.partner"]
        for letter in self:
            if letter.translator:
                match = re.search(r"(.*)\[(.*)\]", letter.translator)
                if match:
                    (name, email) = match.group(1, 2)
                    # 1. Search by e-mail
                    partner = partner_obj.search(
                        ["|", ("email", "=", email), ("translator_email", "=", email)]
                    )
                    if len(partner) == 1:
                        letter.translator_id = partner
                        continue
                    # 2. Search by name
                    words = name.split()
                    partner = partner_obj.search([("name", "like", words[0])])
                    if len(words) > 1:
                        for word in words[1:]:
                            partner = partner.filtered(lambda p: word in p.name)
                            if len(partner) == 1:
                                break
                    if len(partner) == 1:
                        letter.translator_id = partner

    @api.multi
    def _inverse_set_translator(self):
        """ Sets the translator e-mail address. """
        for letter in self:
            if letter.translator:
                match = re.search(r"(.*)\[(.*)\]", letter.translator)
                if match:
                    letter.translator_id.translator_email = match.group(2)

    def _get_uuid(self):
        return str(uuid.uuid4())

    def _compute_is_final_letter(self):
        for letter in self:
            letter.is_final_letter = (
                "Final Letter" in letter.communication_type_ids.mapped("name")
                or letter.sponsorship_state != "active"
            )

    @api.multi
    def _compute_b64_image(self):
        for letter in self:
            letter.b64image = base64.b64encode(letter.get_image())

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Fill missing fields.
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

        if "partner_id" not in vals:
            sp = self.env["recurring.contract"].browse(vals["sponsorship_id"])
            vals["partner_id"] = sp.correspondent_id.id

        type_ = ".pdf"
        letter_data = False
        if vals.get("letter_image"):
            letter_data = base64.b64decode(vals["letter_image"])
            ftype = magic.from_buffer(letter_data, True).lower()
            if "pdf" in ftype:
                type_ = ".pdf"
            elif "tiff" in ftype:
                type_ = ".tiff"
            else:
                raise UserError(_("You can only attach tiff or pdf files"))

        letter = super().create(vals)
        letter.file_name = letter._get_file_name()
        if letter_data and type_ == ".pdf":
            # Set the correct number of pages
            image_pdf = PdfFileReader(BytesIO(letter_data))
            if letter.nbr_pages < image_pdf.numPages:
                for i in range(letter.nbr_pages, image_pdf.numPages):
                    letter.page_ids.create({"correspondence_id": letter.id})

        if not self.env.context.get("no_comm_kit"):
            letter.create_commkit()

        return letter

    @api.multi
    def write(self, vals):
        """ Keep track of state changes. """
        if "state" in vals:
            vals["status_date"] = fields.Datetime.now()
        if "translator_id" in vals:
            vals["translate_date"] = fields.Datetime.now()
        if "letter_image" in vals and self.store_letter_image is False:
            vals["letter_image"] = False
        return super().write(vals)

    @api.multi
    def unlink(self):
        if not self.env.context.get("force_delete"):
            for letter in self:
                if (
                        letter.kit_identifier
                        or letter.state == "Global Partner translation queue"
                ):
                    raise UserError(
                        _(
                            "You cannot delete a letter which is in "
                            "translation or already sent to GMC."
                        )
                    )
        # Remove unsent messages
        gmc_action = self.env.ref("sbc_compassion.create_letter")
        gmc_messages = self.env["gmc.message"].search(
            [
                ("action_id", "=", gmc_action.id),
                ("object_id", "in", self.ids),
                ("state", "in", ["new", "failure", "postponed"]),
            ]
        )
        gmc_messages.unlink()
        return super().unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def create_commkit(self):
        for letter in self:
            action_id = self.env.ref("sbc_compassion.create_letter").id
            message = self.env["gmc.message"].create(
                {
                    "action_id": action_id,
                    "object_id": letter.id,
                    "child_id": letter.child_id.id,
                    "partner_id": letter.partner_id.id,
                }
            )
            if (
                    letter.sponsorship_id.state not in ("active", "terminated")
                    or letter.child_id.project_id.hold_s2b_letters
            ):
                message.state = "postponed"
                if letter.child_id.project_id.hold_s2b_letters:
                    letter.state = "Exception"
                    letter.message_post(
                        body=_(
                            "Letter was put on hold because the project is suspended"),
                        subject=_("Project suspended"),
                    )
        return True

    @api.multi
    def compose_letter_button(self):
        """ Remove old images, download original and compose translation. """
        self.attach_original()
        return self.compose_letter_image()

    @api.multi
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
        with (Image(blob=image_data, resolution=150)) as page_image:
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

        self.letter_image = base64.b64encode(
            template.generate_pdf(
                self.name, {}, {"Translation": text_boxes}, images, pages
            )
        )

        return True

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
        pages = self.page_ids
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
                pages = pages.filtered(source).filtered(
                    lambda p: "".join((p.translated_text or "").split())
                              != "".join((p.english_text or "").split())
                )
        else:
            source = "english_text"
            # Avoid capturing translations that are the same text as the
            # original text.
            pages = pages.filtered(source).filtered(
                lambda p: "".join((p.english_text or "").split())
                          != "".join((p.original_text or "").split())
            )
        if not getattr(self, source):
            return source, text_boxes

        # Get the text boxes separately
        text_pages = pages.mapped(source)
        for index, text in enumerate(text_pages):
            # Skip pages that should not contain anything
            page_layout = self.template_id.page_ids.filtered(
                lambda p: p.page_index == index + 1
            )
            if not text.strip() and not page_layout.text_box_ids:
                continue
            text_boxes.extend([t.strip() for t in text.split(BOX_SEPARATOR)])

        return source, text_boxes

    @api.model
    def process_commkit(self, commkit_data):
        """ Update or Create the letter with given values. """
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
                    letter.write(vals)
            else:
                if "id" in vals:
                    del vals["id"]
                letter = self.with_context(no_comm_kit=True).create(vals)

            if is_published:
                process_letters += letter

            letter_ids.append(letter.id)

        process_letters.process_letter()
        return letter_ids

    def on_send_to_connect(self):
        """
        Method called before Letter is sent to GMC.
        Upload the image to Persistence if not already done.
        """
        onramp = SBCConnector()
        for letter in self.filtered(lambda l: not l.original_letter_url):
            letter.original_letter_url = onramp.send_letter_image(
                letter.get_image(), letter.letter_format, base64encoded=False
            )

    @api.multi
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
        return self.write(vals)

    def process_letter(self):
        """ Method called when new B2S letter is Published. """
        self.download_attach_letter_image(letter_type="original_letter_url")
        res = True
        for letter in self:
            if letter.original_language_id not in letter.supporter_languages_ids:
                res = res and letter.compose_letter_image()
            letter.read_url = f"/b2s_image?id={letter.uuid}"
        return res

    @api.multi
    def download_attach_letter_image(self, letter_type="final_letter_url"):
        """ Download letter image from US service and attach to letter. """
        for letter in self:
            # Download and store letter
            letter_url = getattr(letter, letter_type)
            image_data = None
            if letter_url:
                image_data = SBCConnector().get_letter_image(
                    letter_url, "pdf", dpi=300
                )  # resolution
            if image_data is None:
                raise UserError(
                    _(
                        "Image of letter %s was not found remotely."
                    ) % letter.kit_identifier
                )
            letter.write(
                {"file_name": letter._get_file_name(), "letter_image": image_data}
            )

    @api.multi
    def attach_original(self):
        self.download_attach_letter_image(letter_type="original_letter_url")
        return True

    def get_image(self):
        """ Method for retrieving the image """
        self.ensure_one()

        if not self.store_letter_image:
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
        pdf_name = self.name

        header = (
            f"{sponsor.global_id} - {sponsor.name}\n"
            f"{child.local_id} - {child.preferred_name} - "
            f"{child.gender == 'F' and 'Female' or 'Male'} - {child.age}"
        )

        image_data = self.mapped("original_attachment_ids.datas") or []
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
        """ Prevents to send S2B letters to GMC. """
        self.write({"state": "Exception"})
        for letter in self:
            letter.message_post(body=_("Letter was put on hold"), subject=message)
        gmc_action = self.env.ref("sbc_compassion.create_letter")
        gmc_messages = self.env["gmc.message"].search(
            [
                ("action_id", "=", gmc_action.id),
                ("object_id", "in", self.ids),
                ("state", "in", ["new", "failure"]),
            ]
        )
        gmc_messages.write({"state": "postponed"})

    def reactivate_letters(self, message="Project reactivated"):
        """ Release the hold on S2B letters. """
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

    @api.model
    def migrate_attachments(self):
        """ This method is specific for migration > 10.0.1.1.0
            so that the attachments can be correctly linked to the letters.
            It is not put inside a migration script because the method is
            very slow. Therefore we commit at each letter to avoid having to
            start all over again in case of failure.
        """
        attachment_obj = self.env["ir.attachment"]
        _logger.info("Migration of correspondence attachments started !")
        letters = self.search([("letter_image", "=", False)], order="id desc")
        total = len(letters)
        index = 1
        for letter in letters:
            _logger.info(f"... moving attachment of letter {index}/{total}")
            attachments = attachment_obj.search(
                [("res_model", "=", "correspondence"), ("res_id", "=", letter.id)],
                order="id desc",
            )
            if attachments:
                letter.write(
                    {
                        "letter_image": attachments[0].datas,
                        "file_name": attachments[0].name,
                    }
                )
                attachments.unlink()
            if not test_mode:
                self.env.cr.commit()  # pylint: disable=invalid-commit
            index += 1
        return True

    @api.multi
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

    @api.multi
    def data_to_json(self, mapping_name=None):
        json_data = super().data_to_json(mapping_name)

        if "Status" in json_data:
            del json_data["Status"]

        if "SBCTypes" in json_data:
            del json_data["SBCTypes"]

        if "MarkedForRework" in json_data:
            del json_data["MarkedForRework"]

        if "TranslationLanguage" in json_data:
            del json_data["TranslationLanguage"]

        if "GlobalPartner" in json_data:
            json_data["GlobalPartner"] = {"Id": json_data["GlobalPartner"]}

        pages = json_data.get("Pages", [])
        if not isinstance(pages, list):
            pages = [pages]
        english_text = ""
        translated_text = ""
        for page in pages:
            english_text += "".join(page["EnglishTranslatedText"])
            translated_text += "".join(page["TranslatedText"])
        if english_text == "" and translated_text != "":
            for page in pages:
                page["EnglishTranslatedText"] = page["TranslatedText"]

        if "LocalId" in json_data:
            json_data["LocalId"] = json_data["LocalId"] + self.resubmit_id

        return json_data

    @api.model
    def json_to_data(self, json, mapping_name=None):
        template_name = json.pop("Template", "CH-A-6S11-1")
        odoo_data = super().json_to_data(json, mapping_name)

        if template_name.startswith("CH"):
            template = self.env["correspondence.template"].search(
                [("layout", "like", template_name)], limit=1
            )
        else:
            template = self.env["correspondence.template"].search(
                [("name", "like", "L" + template_name[5]), ("name", "like", "B2S")],
                limit=1,
            )
        odoo_data["template_id"] = template.id

        if "child_id" in odoo_data and "partner_id" in odoo_data:
            partner = odoo_data.pop("partner_id")
            child = odoo_data.pop("child_id")
            sponsorship = self.env["recurring.contract"].search(
                [
                    ("correspondent_id.global_id", "=", partner.get("global_id")),
                    ("child_id.global_id", "=", child.get("global_id")),
                ],
                limit=1,
            )
            if sponsorship:
                odoo_data["sponsorship_id"] = sponsorship.id

        # Replace dict by a tuple for the ORM update/create
        if "page_ids" in odoo_data:
            pages = list()
            for page in odoo_data["page_ids"]:
                page_url = page.get("original_page_url")
                if not page_url:
                    # We don't need to save pages not accessible
                    continue
                page_id = (
                    self.env["correspondence.page"]
                    .search([("original_page_url", "=", page_url)], limit=1)
                    .id
                )
                # if page_url already exist update it
                if page_id:
                    orm_tuple = (1, page_id, page)
                # else create a new one
                else:
                    orm_tuple = (0, 0, page)
                pages.append(orm_tuple)
            odoo_data["page_ids"] = pages or False

        return odoo_data

    @api.multi
    def resubmit_letter(self):
        for letter in self:
            if letter.state != "Translation check unsuccessful":
                raise UserError(_("Letter must be in state 'Translation check unsuccessful'"))

            letter.kit_identifier = None
            letter.resubmit_id += 1
            letter.create_commkit()