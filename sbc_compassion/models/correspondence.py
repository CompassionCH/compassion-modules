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
import logging
import uuid

from PyPDF2 import PdfFileReader

from odoo import _, api, fields, models
from odoo.exceptions import UserError
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
    name = fields.Char(compute="_compute_name", store=True)
    partner_id = fields.Many2one(
        "res.partner", "Partner", readonly=True, ondelete="restrict"
    )
    child_id = fields.Many2one(
        related="sponsorship_id.child_id", precompute=True, store=True, readonly=True
    )
    avatar_128 = fields.Image(compute="_compute_avatar")
    # Field used for identifying correspondence by GMC
    kit_identifier = fields.Char("Kit id", copy=False, tracking=True)
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
    )
    s2b_state = fields.Selection(
        [
            ("Draft", _("Draft")),
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
        "Preview of the letter",
        compute="_compute_preview",
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
            _("The kit id already exists in database."),
        ),
        (
            "uuid",
            "unique(uuid)",
            _("The uuid already exists in database."),
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

    def _compute_avatar(self):
        for correspondence in self:
            if correspondence.direction == "Supporter To Beneficiary":
                correspondence.avatar_128 = correspondence.partner_id.avatar_128
            else:
                correspondence.avatar_128 = correspondence.child_id.avatar_128

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
                        setattr(letter.page_ids[i], field, pages_text[i].strip("\n"))
                else:
                    for i in range(0, len(letter.page_ids)):
                        setattr(letter.page_ids[i], field, pages_text[i].strip("\n"))
                    last_page_text = getattr(letter.page_ids[i], field)
                    last_page_text += "\n\n" + "\n\n".join(pages_text[i + 1 :])
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

    @api.depends("uuid")
    def _compute_read_url(self):
        for letter in self:
            letter.read_url = f"{letter.get_base_url()}/b2s_image?uuid={letter.uuid}"

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
    @api.model
    def create(self, vals):
        """ """
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
                    (4, self.env.ref("sbc_compassion.correspondence_type_scheduled").id)
                ]
            # Allows manually creating a B2S letter
            if vals.get("state", "Draft") == "Draft":
                vals["state"] = "Published to Global Partner"

        if "partner_id" not in vals:
            vals["partner_id"] = contract.correspondent_id.id

        letter = super().create(vals)
        if letter.state == "Received in the system" and not self.env.context.get(
            "no_comm_kit"
        ):
            letter.create_commkit()
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

        return letter

    def write(self, vals):
        """Keep track of state changes."""
        if "state" in vals:
            if vals["state"] == "Translation check unsuccessful":
                responsible = self.env["res.config.settings"].get_param(
                    "letter_responsible"
                )
                if responsible:
                    for c in self:
                        c._make_activity(vals["state"], responsible)

            elif "state" in vals:
                for c in self.filtered(
                    lambda o: o.state == "Translation check unsuccessful"
                ):
                    c.activity_ids.unlink()
            vals["status_date"] = fields.Datetime.now()

        return super().write(vals)

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
                            "Letter was put on hold because the project is suspended"
                        ),
                        subject=_("Project suspended"),
                    )
        return True

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
                    if letter._will_erase_text(vals):
                        vals.pop("page_ids", False)
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
        """Method for retrieving the PDF of the letter."""
        self.ensure_one()
        if self.sponsor_letter_scan:
            return base64.b64decode(self.sponsor_letter_scan)
        return self.env["ir.actions.report"]._render_qweb_pdf(
            "sbc_compassion.report_correspondence", self.ids
        )[0]

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

        if "GlobalPartnerSBCId" in json_data:
            json_data["GlobalPartnerSBCId"] = json_data["GlobalPartnerSBCId"] + str(
                self.resubmit_id
            )

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

        return odoo_data

    def resubmit_letter(self):
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
            letter.create_commkit()

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

    def _will_erase_text(self, letter_vals):
        """T1602 Checks if the text will be erased when saving the letter.
        GMC sends back empty text content but we don't want to erase the text on
        our side.

        Args:
            letter_vals: A dictionary containing correspondence values like
            {'page_ids': [(0, 0, {'english_text': 'example'}]}.

        Returns:
            True if the text will be erased, False otherwise.
        """
        self.ensure_one()
        if any((self.english_text, self.original_text, self.translated_text)):
            return not self._has_text(letter_vals)
        return False

    @api.model
    def _has_text(self, letter_vals):
        """Checks if any text key has a non-empty value in the provided data.

        Args:
            letter_vals: A dictionary containing correspondence values like
            {'page_ids': [(0, 0, {'english_text': 'example'}]}.

        Returns:
            True if any of the text keys has a non-empty value, False otherwise.
        """
        # Check for text in top level keys
        if not isinstance(letter_vals, dict):
            return False
        if (
            letter_vals.get("original_text")
            or letter_vals.get("english_text")
            or letter_vals.get("translated_text")
        ):
            return True

        # Check for text in nested dictionaries
        for item in letter_vals.get("page_ids", []):
            if isinstance(item, tuple) and len(item) == 3 and self._has_text(item[2]):
                return True

        return False

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
