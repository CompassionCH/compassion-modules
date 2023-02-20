##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import threading
from collections import defaultdict
from html.parser import HTMLParser
from io import BytesIO

from jinja2 import TemplateSyntaxError
from reportlab.lib.colors import white
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from odoo import api, models, fields, _, tools
from odoo.exceptions import UserError, QWebException

logger = logging.getLogger(__name__)
testing = tools.config.get("test_enable")

try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from PyPDF2.utils import PdfReadError
except ImportError:
    logger.warning(
        "Please install PyPDF2 for generating OMR codes in "
        "Printed partner communications"
    )


class MLStripper(HTMLParser):
    """ Used to remove HTML tags. """

    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return "".join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


class CommunicationJob(models.Model):
    """ Communication Jobs are task that will either generate and send
     an e-mail or print a document when executed.

     It is useful to keep a history of the communication sent to partners
     and to send again (or print again) a particular communication.

     It is also useful to batch send communications without manually looking
     for which one to send by e-mail and which one to print.
     """

    _name = "partner.communication.job"
    _description = "Communication Job"
    _rec_name = "subject"
    _order = "date desc,sent_date desc"
    _inherit = [
        "partner.communication.defaults",
        "mail.activity.mixin",
        "mail.thread",
        "partner.communication.orm.config.abstract",
        "phone.validation.mixin",
    ]
    _phone_name_fields = ["partner_phone", "partner_mobile"]

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    config_id = fields.Many2one(
        "partner.communication.config",
        "Type",
        required=True,
        default=lambda s: s.env.ref("partner_communication.default_communication"),
        readonly=False,
        index=True
    )
    model = fields.Char(related="config_id.model", store=True, index=True)
    partner_id = fields.Many2one(
        "res.partner", "Send to", required=True, ondelete="cascade", readonly=False,
        index=True
    )
    company_id = fields.Many2one(
        "res.company", related="partner_id.company_id", store=True, index=True)
    partner_phone = fields.Char(related="partner_id.phone")
    partner_mobile = fields.Char(related="partner_id.mobile")
    country_id = fields.Many2one(related="partner_id.country_id", readonly=False)
    parent_id = fields.Many2one(related="partner_id.parent_id", readonly=False)
    object_ids = fields.Char("Resource ids", required=True)
    date = fields.Datetime(default=fields.Datetime.now, index=True)
    sent_date = fields.Datetime(readonly=True, copy=False, index=True)
    state = fields.Selection(
        [
            ("pending", _("Pending")),
            ("done", _("Done")),
            ("cancel", _("Cancelled")),
            ("failure", _("Failure"))
        ],
        default="pending",
        track_visibility="onchange",
        copy=False,
    )
    need_call = fields.Selection(
        [
            ("before_sending", "Before the communication is sent"),
            ("after_sending", "After the communication is sent"),
        ],
        help="Indicates we should have a personal contact with the partner",
    )
    auto_send = fields.Boolean(
        help="Job is processed at creation if set to true", copy=False
    )
    send_mode = fields.Selection("send_mode_select", index=True)
    email_template_id = fields.Many2one(
        related="config_id.email_template_id", store=True, readonly=False
    )
    email_to = fields.Char(help="optional e-mail address to override recipient")
    email_id = fields.Many2one(
        "mail.mail", "Generated e-mail", readonly=True, index=True, copy=False
    )
    phonecall_id = fields.Many2one("crm.phonecall", "Phonecall log", readonly=True)
    body_html = fields.Html(sanitize=False)
    pdf_page_count = fields.Integer(string="PDF size", readonly=True)
    subject = fields.Char()
    attachment_ids = fields.One2many(
        "partner.communication.attachment",
        "communication_id",
        string="Attachments",
        readonly=False,
    )
    ir_attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Attachments",
        compute="_compute_ir_attachments",
        inverse="_inverse_ir_attachments",
        domain=[("report_id", "!=", False)],
        readonly=False,
    )
    ir_attachment_tmp = fields.Many2many(
        "ir.attachment",
        string="Attachments",
        compute="_compute_void",
        inverse="_inverse_ir_attachment_tmp",
        readonly=False,
    )

    printer_output_tray_id = fields.Many2one("printing.tray.output",
                                             "Printer Output Bin")

    def _compute_ir_attachments(self):
        for job in self:
            job.ir_attachment_ids = job.mapped("attachment_ids.attachment_id")

    def count_pdf_page(self):
        skip_count = self.env.context.get(
            "skip_pdf_count", getattr(threading.currentThread(), "testing", False)
        )
        if not skip_count:
            for record in self.filtered("report_id"):
                if record.send_mode == "physical":
                    try:
                        report = record.report_id.with_context(
                            lang=record.partner_id.lang, must_skip_send_to_printer=True
                        )
                        pdf_str = report.sudo().render_qweb_pdf(record.ids)
                        pdf = PdfFileReader(BytesIO(pdf_str[0]))
                        record.pdf_page_count = pdf.getNumPages()
                    except (UserError, PdfReadError, QWebException,
                            TemplateSyntaxError):
                        self.env.clear()
                        record.pdf_page_count = 0

    def _inverse_ir_attachments(self):
        attach_obj = self.env["partner.communication.attachment"]
        for job in self:
            for attachment in job.ir_attachment_ids:
                if attachment not in job.attachment_ids.mapped("attachment_id"):
                    if not attachment.report_id and not self.env.context.get(
                            "no_print"
                    ):
                        raise UserError(
                            _(
                                "Please select a printing configuration for the "
                                "attachments you add."
                            )
                        )
                    attach_obj.create(
                        {
                            "name": attachment.name,
                            "communication_id": job.id,
                            "report_name": attachment.report_id.report_name or "",
                            "attachment_id": attachment.id,
                        }
                    )
            # Remove deleted attachments
            job.attachment_ids.filtered(
                lambda a: a.attachment_id not in job.ir_attachment_ids
            ).unlink()

    def _compute_void(self):
        pass

    def _inverse_ir_attachment_tmp(self):
        for job in self:
            for attachment in job.ir_attachment_tmp:
                attachment.report_id = self.env.ref(
                    "partner_communication.report_a4_no_margin"
                )
            job.ir_attachment_ids += job.ir_attachment_tmp

    @api.model
    def send_mode_select(self):
        return [
            ("digital", _("By e-mail")),
            ("physical", _("Print report")),
            ("both", _("Both")),
        ]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ If a pending communication for same partner exists,
        add the object_ids to it. Otherwise, create a new communication.
        opt-out partners won't create any communication.
        """
        # Object ids accept lists, integer or string values. It should contain
        # a comma separated list of integers
        object_ids = vals.get("object_ids")
        if isinstance(object_ids, list):
            vals["object_ids"] = ",".join(map(str, object_ids))
        elif object_ids:
            vals["object_ids"] = str(object_ids)
        else:
            vals["object_ids"] = str(vals["partner_id"])

        same_job_search = [
            ("partner_id", "=", vals.get("partner_id")),
            ("config_id", "=", vals.get("config_id")),
            ("config_id", "!=", self.env.ref(
                "partner_communication.default_communication").id),
            ("state", "in", ["pending", "failure"]),
        ] + self.env.context.get("same_job_search", [])
        job = self.search(same_job_search, limit=1)
        if job:
            job.object_ids = job.object_ids + "," + vals["object_ids"]
            job.refresh_text()
            if job.auto_send:
                job.send()
            return job

        self._get_default_vals(vals)
        job = super().create(vals)

        # Determine send mode
        send_mode = job.config_id.get_inform_mode(job.partner_id)

        if "send_mode" not in vals and "default_send_mode" not in self.env.context:
            job.send_mode = send_mode[0]
        if "auto_send" not in vals and "default_auto_send" not in self.env.context:
            job.auto_send = send_mode[1]

        if not job.body_html or not strip_tags(job.body_html):
            job.refresh_text()
        else:
            job.set_attachments()

        if job.body_html or job.send_mode == "physical":
            job.count_pdf_page()

        # Difference between send_mode of partner and send_mode of job
        if send_mode[0] != job.send_mode:
            if "only" in job.partner_id.global_communication_delivery_preference:
                # Send_mode chosen by the employee is not compatible with the partner
                # So we remove it and an employee must set it manually afterwards
                job.send_mode = ""

        if job.auto_send:
            job.send()
        return job


    @api.multi
    def copy(self, vals=None):
        if vals is None:
            vals = {}
        vals["auto_send"] = False
        return super(CommunicationJob, self).copy(vals)

    @api.model
    def _get_default_vals(self, vals, default_vals=None):
        """
        Used at record creation to find default values given the config of the
        communication.
        :param vals: dict: record values
        :param default_vals: list of fields to copy from config to job.
        :return: config record to use in inheritances.
                 The vals dict is updated.
        """
        if default_vals is None:
            default_vals = []
        default_vals.extend(
            [
                "report_id",
                "need_call",
                "omr_enable_marks",
                "omr_should_close_envelope",
                "omr_add_attachment_tray_1",
                "omr_add_attachment_tray_2",
                "omr_top_mark_x",
                "omr_top_mark_y",
                "omr_single_sided",
            ]
        )

        partner = self.env["res.partner"].browse(vals.get("partner_id"))
        lang_of_partner = self.env["res.lang"].search(
            [("code", "like", partner.lang or self.env.lang)]
        )
        config = self.config_id.browse(vals["config_id"]).with_context(
            lang=lang_of_partner.code
        )

        # Determine user by default : take in config or employee
        omr_config, printer_config = config.get_config_for_lang(lang_of_partner)
        if not vals.get("user_id"):
            # responsible for the communication is user specified in the omr_config
            # or user specified in the config itself
            # or the current user
            user_id = self.env.uid
            if omr_config.user_id:
                user_id = omr_config.user_id.id
            elif config.user_id:
                user_id = config.user_id.id
            vals["user_id"] = user_id

        if not vals.get("printer_output_tray_id"):
            if printer_config.printer_output_tray_id:
                vals["printer_output_tray_id"] = \
                    printer_config.printer_output_tray_id.id

        # Check all default_vals fields
        for default_val in default_vals:
            if default_val not in vals:
                if default_val.startswith("omr_"):
                    value = getattr(omr_config, default_val, False)
                else:
                    value = getattr(config, default_val)
                    if default_val.endswith("_id"):
                        value = value.id
                vals[default_val] = value

        return config

    @api.multi
    def write(self, vals):
        object_ids = vals.get("object_ids")
        if isinstance(object_ids, list):
            vals["object_ids"] = ",".join(map(str, object_ids))
        elif object_ids:
            vals["object_ids"] = str(object_ids)

        super().write(vals)

        if vals.get("body_html") or vals.get("send_mode") == "physical":
            self.count_pdf_page()

        if "need_call" in vals or "state" in vals:
            for job in self:

                # if the call must be done after the sending, we unlink all activities
                # associated with the job (as for the moment, there is only one activity
                # type)
                if job.need_call == "after_sending" and job.state == "pending":
                    job.activity_ids.unlink()

                # if the call must be done before the sending, and if there isn't an
                # activity already scheduled, we schedule a new activity
                # (there's only one activity type associated with the communication job)
                if ((job.need_call == "before_sending"
                     and job.state == "pending")
                        and not job.activity_ids):
                    job.sudo(job.user_id.id).schedule_call()

        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def send(self):
        """ Executes the job. """
        todo = self.filtered(
            lambda j: j.state == "pending" and not (
                j.need_call == "before_sending" and j.activity_ids))
        to_print = todo.filtered(lambda j: j.send_mode == "physical")
        for job in todo.filtered(lambda j: j.send_mode in ("both", "digital")):
            origin = self.env.context.get("origin")
            # if we print first in a communication with send_mode == both
            if origin == "both_print" and job.send_mode == "both":
                job.send_mode = "digital"
                return job._print_report()

            state = job._send_mail()
            if job.send_mode != "both":
                job.write(
                    {
                        "state": state,
                        "sent_date": state != "pending" and fields.Datetime.now(),
                    }
                )
            else:
                # Job was sent by e-mail and must now be printed
                job.send_mode = "physical"
                job.refresh_text()

            # if the call must be done after the sending, an activity is scheduled
            if job.need_call == "after_sending":
                job.sudo(job.user_id.id).schedule_call()
        if to_print:
            return to_print._print_report()
        return True

    def schedule_call(self):
        self.ensure_one()
        self.activity_schedule(
            'mail.mail_activity_data_call',
            summary="Call " + self.partner_id.name,
            user_id=self.env.uid,
            note=f"Call {self.partner_id.name} at (phone) "
                 f"{self.partner_phone or self.partner_mobile} regarding "
                 f"the communication."
        )

    @api.multi
    def cancel(self):
        self.mapped("activity_ids").unlink()
        return self.write({"state": "cancel"})

    @api.multi
    def reset(self):
        self.write(
            {"state": "pending", "sent_date": False, "email_id": False, }
        )
        return True

    @api.multi
    def refresh_text(self, refresh_uid=False):
        self.mapped("attachment_ids").unlink()
        failed = self.set_attachments()
        for job in self - failed:
            lang = self.env.context.get("lang_preview", job.partner_id.lang)
            if job.email_template_id and job.object_ids:
                try:
                    fields = (
                        self.env["mail.compose.message"]
                            .with_context(lang=lang)
                            .get_generated_fields(job.email_template_id, [job.id])
                    )
                    assert fields["body_html"] and fields["subject"]
                    job.write({
                        "body_html": fields["body_html"],
                        "subject": fields["subject"],
                        "state": job.state if job.state != "failure" else "pending"
                    })
                except (UserError, QWebException, TemplateSyntaxError, AssertionError):
                    logger.error("Failed to generate communication", exc_info=True)
                    job.env.clear()
                    if job.state == "pending":
                        job.write({
                            "state": "failure",
                            "body_html": "Error in template"
                        })
                finally:
                    if refresh_uid:
                        job.user_id = self.env.user

        return True

    @api.multi
    def quick_refresh(self):
        # Only refresh text and subject, all at once
        jobs = self.filtered("email_template_id").filtered("object_ids")
        lang = self.env.context.get("lang_preview", jobs.mapped("partner_id.lang"))
        template = jobs.mapped("email_template_id")
        if len(template) > 1:
            raise UserError(_("This is only possible for one template at time"))
        values = (
            self.env["mail.compose.message"]
                .with_context(lang=lang)
                .get_generated_fields(template, jobs.ids)
        )
        if not isinstance(values, list):
            values = [values]
        for index in range(0, len(values)):
            jobs[index].write(
                {
                    "body_html": values[index]["body_html"],
                    "subject": values[index]["subject"],
                }
            )
        return True

    @api.onchange("config_id", "partner_id")
    def onchange_config_id(self):
        if self.config_id and self.partner_id:
            send_mode = self.config_id.get_inform_mode(self.partner_id)
            self.send_mode = send_mode[0]
            # set default fields
            partner_id = None
            if self.partner_id:
                partner_id = self.partner_id.id
            default_vals = {"config_id": self.config_id.id, "partner_id": partner_id}
            self._get_default_vals(default_vals)
            for key, val in list(default_vals.items()):
                if key.endswith("_id"):
                    val = getattr(self, key).browse(val)
                setattr(self, key, val)

    @api.multi
    def open_related(self):
        object_ids = list(map(int, self.object_ids.split(",")))
        action = {
            "name": _("Related objects"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form,tree",
            "res_model": self.config_id.model,
            "context": self.with_context(group_by=False).env.context,
            "target": "current",
        }
        if len(object_ids) > 1:
            action.update(
                {"view_mode": "tree,form", "domain": [("id", "in", object_ids)]}
            )
        else:
            action["res_id"] = object_ids[0]

        return action

    @api.multi
    def call(self):
        """ Call partner from tree view button. """
        self.ensure_one()
        self.env["phone.common"].click2dial(self.partner_phone or self.partner_mobile)
        return self.log_call()

    @api.multi
    def get_objects(self):
        model = list(set(self.mapped("config_id.model")))
        assert len(model) == 1
        object_ids = list()
        object_id_strings = self.mapped("object_ids")
        for id_strings in object_id_strings:
            object_ids += list(map(int, id_strings.split(",")))
        return self.env[model[0]].browse(set(object_ids))

    @api.multi
    def set_attachments(self):
        """
        Generates attachments for the communication and link them to the
        communication record.
        """
        attachment_obj = self.env["partner.communication.attachment"]
        failed = self.env[self._name]
        for job in self.with_context(must_skip_send_to_printer=True):
            if job.config_id.attachments_function:
                try:
                    binaries = getattr(
                        job.with_context(lang=job.partner_id.lang),
                        job.config_id.attachments_function,
                        dict,
                    )()
                    if binaries and isinstance(binaries, dict):
                        for name, data in list(binaries.items()):
                            attachment_obj.create(
                                {
                                    "name": name,
                                    "communication_id": job.id,
                                    "report_name": data[0],
                                    "data": data[1],
                                }
                            )
                except:
                    logger.error("Error during attachment creation", exc_info=True)
                    job.env.clear()
                    if job.state == "pending":
                        job.write({
                            "state": "failure",
                            "body_html": "Error in attachments creation."
                        })
                    failed += job
        return failed

    @api.multi
    def preview_pdf(self):
        preview_model = "partner.communication.pdf.wizard"
        preview = self.env[preview_model].create({"communication_id": self.id})
        return {
            "name": _("Preview"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": preview_model,
            "res_id": preview.id,
            "context": self.env.context,
            "target": "new",
        }

    @api.multi
    def add_omr_marks(self, pdf_data, is_latest_document):
        # Documentation
        # http://meteorite.unm.edu/site_media/pdf/reportlab-userguide.pdf
        # https://pythonhosted.org/PyPDF2/PdfFileReader.html
        # https://stackoverflow.com/a/17538003
        # https://gist.github.com/kzim44/5023021
        # https://www.blog.pythonlibrary.org/2013/07/16/
        #   pypdf-how-to-write-a-pdf-to-memory/
        self.ensure_one()

        pdf_buffer = BytesIO()
        pdf_buffer.write(pdf_data)

        existing_pdf = PdfFileReader(pdf_buffer)
        output = PdfFileWriter()
        total_pages = existing_pdf.getNumPages()

        # the latest page number is the same as the number of total_pages if the document is 1-sided (recto)
        latest_omr_page = total_pages

        # if omr_single_sided is false, the document is 2-sided (recto-verso)
        if not self.omr_single_sided:
            # modulo to check if the total_pages number is even or odd
            if total_pages % 2 == 0:
                # latest_omr_page on 2-sided document with a pair total page number is the last front page
                latest_omr_page = total_pages - 1

        for page_number in range(total_pages):
            page = existing_pdf.getPage(page_number)
            # only print omr marks on pair pages (recto)
            if self.omr_single_sided or page_number % 2 == 0:
                # latest_omr_page is not starting from 0 as page_number that's why we need + 1
                is_latest_page = is_latest_document and latest_omr_page == page_number + 1
                marks = self._compute_marks(is_latest_page)
                omr_layer = self._build_omr_layer(marks)
                page.mergePage(omr_layer)
            output.addPage(page)

        out_buffer = BytesIO()
        output.write(out_buffer)

        return out_buffer.getvalue()

    def _compute_marks(self, is_latest_page):
        marks = [
            True,  # Start mark (compulsory)
            is_latest_page,
            is_latest_page and self.omr_add_attachment_tray_1,
            is_latest_page and self.omr_add_attachment_tray_2,
            is_latest_page and not self.omr_should_close_envelope,
        ]
        parity_check = sum(marks) % 2 == 0
        marks.append(parity_check)
        marks.append(True)  # End mark (compulsory)
        return marks

    def _build_omr_layer(self, marks):
        self.ensure_one()
        padding_x = 4.2 * mm
        padding_y = 8.5 * mm
        top_mark_x = self.omr_top_mark_x * mm
        top_mark_y = self.omr_top_mark_y * mm
        mark_y_spacing = 4 * mm

        mark_width = 6.5 * mm
        marks_height = (len(marks) - 1) * mark_y_spacing

        logger.debug(
            "Mailer DS-75i OMR Settings: 1=%s 2=%s",
            str((297 * mm - top_mark_y) / mm),
            str((top_mark_x + mark_width / 2) / mm + 0.5),
        )

        omr_buffer = BytesIO()
        omr_canvas = Canvas(omr_buffer)
        omr_canvas.setLineWidth(0.2 * mm)

        # add a white background for the omr code
        omr_canvas.setFillColor(white)
        omr_canvas.rect(
            x=top_mark_x - padding_x,
            y=top_mark_y - marks_height - padding_y,
            width=mark_width + 2 * padding_x,
            height=marks_height + 2 * padding_y,
            fill=True,
            stroke=False,
        )

        for offset, mark in enumerate(marks):
            mark_y = top_mark_y - offset * mark_y_spacing
            if mark:
                omr_canvas.line(top_mark_x, mark_y, top_mark_x + mark_width, mark_y)

        # Close the PDF object cleanly.
        omr_canvas.showPage()
        omr_canvas.save()

        # move to the beginning of the BytesIO buffer
        omr_buffer.seek(0)
        omr_pdf = PdfFileReader(omr_buffer)

        return omr_pdf.getPage(0)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _send_mail(self):
        """
        Called for sending the communication by e-mail.
        :return: state of the communication depending if the e-mail was
                 successfully sent or not.
        """
        self.ensure_one()
        partner = self.partner_id
        # Send by e-mail
        email = self.email_id
        if not email:
            email_vals = {
                "recipient_ids": [(4, partner.id)],
                "communication_config_id": self.config_id.id,
                "body_html": self.body_html,
                "subject": self.subject,
                "attachment_ids": [(6, 0, self.ir_attachment_ids.ids)],
                "auto_delete": False,
                "reply_to": (self.email_template_id.reply_to or self.user_id.email),
            }
            if self.email_to:
                # Replace partner e-mail by specified address
                email_vals["email_to"] = self.email_to
                del email_vals["recipient_ids"]
            if "default_email_vals" in self.env.context:
                email_vals.update(self.env.context["default_email_vals"])

            email = self.env["mail.compose.message"] \
                .with_context(lang=partner.lang) \
                .create_emails(self.email_template_id, [self.id], email_vals)
            self.email_id = email

            try:
                with self.env.cr.savepoint():
                    email.send()
            except:
                logger.error("Error while sending communication by email to %s ",
                             partner.email, exc_info=True)
                return "failure"

            # Subscribe author to thread, so that the reply
            # notifies the author.
            self.message_subscribe(self.user_id.partner_id.ids)

        return "done"

    def _print_report(self):
        name = self.env.user.firstname or self.env.user.name
        origin = self.env.context.get("origin")
        state = "done"
        if origin == "both_print":
            state = "pending"

        # Batch print communications of same type (if no attachments)
        batch_print = {
            lang: defaultdict(lambda: self.env[self._name])
            for lang in list(set(self.mapped("partner_id.lang")))
        }
        for job in self:
            if job.attachment_ids:
                # Print letter
                print_name = name[:3] + " " + (job.subject or "")
                output_tray = job.print_letter(print_name)["output_tray"]

                # Print attachments in the same output_tray
                job.attachment_ids.print_attachments(
                    output_tray=output_tray,
                )
                job.write({"state": state, "sent_date": fields.Datetime.now()})
                if not testing:
                    # Commit to avoid invalid state if process fails
                    self.env.cr.commit()  # pylint: disable=invalid-commit
            else:
                batch_print[job.partner_id.lang][job.config_id.name] += job

        for lang, configs in batch_print.items():
            for config, jobs in configs.items():
                print_name = name[:3] + " " + config
                jobs.print_letter(print_name)
                jobs.write({"state": state, "sent_date": fields.Datetime.now()})
                if not testing:
                    # Commit to avoid invalid state if process fails
                    self.env.cr.commit()  # pylint: disable=invalid-commit
        return True

    def print_letter(self, print_name, **print_options):
        """
        Sends the communication to the printer.
        Returns all configuration needed for printing the jobs.
        :param print_name: name of the document sent to the printer
        :param print_options: use inheritance to add printing options like duplex
                              printing
        :return: output_tray used to print letter
        """
        lang = list(set(self.mapped("partner_id.lang")))
        if len(lang) > 1:
            raise UserError(_("Cannot print multiple langs at the same time."))
        lang = lang[0]

        # Get report
        report = self.mapped("report_id").with_context(
            print_name=print_name, lang=lang, must_skip_send_to_printer=True
        )
        # Get communication config of language
        config_lang = self.mapped("config_id.printer_config_ids").filtered(
            lambda c: c.lang_id.code == lang
        )

        if len(report) > 1 or len(config_lang) > 1:
            raise UserError(_("Cannot print multiple communication types at the same time."))

        behaviour = report.behaviour()

        print_options["doc_format"] = report.report_type
        print_options["action"] = behaviour["action"]

        # The get the print options in the following order of priority:
        # - partner.communication.job (only for output bin)
        # - partner.communication.config
        # - ir.actions.report (behaviour: which can be specific for the user currently logged in)
        def get_first(source):
            return next((v for v in source if v), False)

        print_options["output_tray"] = get_first((
            self[:1].printer_output_tray_id.system_name,
            config_lang.printer_output_tray_id.system_name,
            behaviour["output_tray"]
        ))
        print_options["input_tray"] = get_first((
            config_lang.printer_input_tray_id.system_name,
            behaviour["input_tray"]
        ))

        printer = behaviour["printer"].with_context(lang=lang)
        if behaviour["action"] == "server" and printer:
            # Get pdf should directly send it to the printer
            to_print = report.render_qweb_pdf(self.ids)
            printer.print_document(report.report_name, to_print[0], **print_options)

        return print_options

    @api.model
    def _needaction_domain_get(self):
        """
        Used to display a count icon in the menu
        :return: domain of jobs counted
        """

        return [("state", "=", "pending")]
