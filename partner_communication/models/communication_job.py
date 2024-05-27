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
import re
import threading
from collections import defaultdict
from html.parser import HTMLParser
from io import BytesIO

from jinja2 import TemplateSyntaxError

from odoo import _, api, fields, models, tools
from odoo.exceptions import MissingError, QWebException, UserError

_logger = logging.getLogger(__name__)
testing = tools.config.get("test_enable")

try:
    from PyPDF2 import PdfFileReader
    from PyPDF2.utils import PdfReadError
except ImportError:
    _logger.warning(
        "Please install PyPDF2 for generating print versions of communications."
    )

try:
    from bs4 import BeautifulSoup
except ImportError:
    _logger.warning("Please install bs4 for using the module")


class MLStripper(HTMLParser):
    """Used to remove HTML tags."""

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
    """Communication Jobs are task that will either generate and send
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
    _check_company_auto = True
    _inherit = [
        "partner.communication.defaults",
        "mail.activity.mixin",
        "mail.thread",
        "phone.validation.mixin",
    ]

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    config_id = fields.Many2one(
        "partner.communication.config",
        "Type",
        required=True,
        default=lambda s: s.env.ref("partner_communication.default_communication"),
        readonly=False,
        index=True,
    )
    model = fields.Char(related="config_id.model", store=True, index=True)
    partner_id = fields.Many2one(
        "res.partner",
        "Send to",
        required=True,
        ondelete="cascade",
        readonly=False,
        index=True,
        check_company=True,
    )
    company_id = fields.Many2one(
        "res.company", compute="_compute_company", store=True, index=True
    )
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
            ("failure", _("Failure")),
        ],
        default="pending",
        tracking=True,
        copy=False,
        index=True,
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
    email_id = fields.Many2one(
        "mail.mail", "Generated e-mail", readonly=True, index=True, copy=False
    )
    body_html = fields.Html(sanitize=False)
    pdf_page_count = fields.Integer("Page count", readonly=True)
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
    printed_pdf_data = fields.Binary(
        help="Technical field used when the report was not sent to printer "
        "but to client in order to download the result afterwards."
    )
    printed_pdf_name = fields.Char(compute="_compute_print_pdfname")

    # printer_output_tray_id = fields.Many2one("printing.tray.output",
    #                                          "Printer Output Bin")

    sms_cost = fields.Float()

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
                        pdf_str = report.sudo()._render_qweb_pdf(record.ids)
                        pdf = PdfFileReader(BytesIO(pdf_str[0]))
                        record.pdf_page_count = pdf.getNumPages()
                    except (
                        UserError,
                        PdfReadError,
                        QWebException,
                        TemplateSyntaxError,
                    ):
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
                lambda a, job=job: a.attachment_id not in job.ir_attachment_ids
            ).unlink()

    @api.depends("partner_id", "object_ids")
    def _compute_company(self):
        """
        Rule for setting company:
            1. Check the related records and use the company set in those
            2. Check for a company linked to the partner
            3. Look if a company exists at the country of the partner
            4. Call a fallback function that can provide a custom rule for finding a
               company
        """
        for job in self:
            company = job.partner_id.company_id
            first_object = job.object_ids and job.get_objects()[:1]
            if (
                first_object
                and hasattr(first_object, "company_id")
                and first_object.company_id
            ):
                company = first_object.company_id
            if not company and job.partner_id.country_id:
                company = self.env["res.company"].search(
                    [("partner_id.country_id", "=", job.partner_id.country_id.id)],
                    limit=1,
                )
            if not company:
                company = self._fallback_company()
            job.company_id = company

    def _fallback_company(self):
        # Used when company couldn't be found with the partner
        return self.env.company

    @api.model
    def send_mode_select(self):
        return [
            ("digital", _("By e-mail")),
            ("physical", _("Print report")),
            ("both", _("Both")),
            ("sms", _("SMS")),
        ]

    def _compute_print_pdfname(self):
        for job in self:
            job.printed_pdf_name = (
                fields.Datetime.to_string(job.sent_date) + "-" + job.subject + ".pdf"
            )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """If a pending communication for same partner exists,
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
            (
                "config_id",
                "!=",
                self.env.ref("partner_communication.default_communication").id,
            ),
            ("state", "in", ["pending", "failure"]),
        ] + self.env.context.get("same_job_search", [])
        job = self.search(same_job_search, limit=1)

        if job and not job.config_id.forbid_merging:
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
        if (
            "auto_send" not in vals
            and "default_auto_send" not in self.env.context
            and send_mode[1]
        ):
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

        if job.need_call == "before_sending":
            job.schedule_call()
        if job.auto_send:
            job.send()
        return job

    def copy(self, vals=None):
        if vals is None:
            vals = {}
        vals["auto_send"] = False
        return super().copy(vals)

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
                "print_if_not_email",
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
        default_config = config.get_default_config(lang_of_partner)
        if not vals.get("user_id"):
            # responsible for the communication is user specified in the print_config
            # or user specified in the config itself
            # or the current user
            user_id = self.env.uid
            if default_config.user_id:
                user_id = default_config.user_id.id
            elif config.user_id:
                user_id = config.user_id.id
            vals["user_id"] = user_id

        # if not vals.get("printer_output_tray_id"):
        #     if printer_config.printer_output_tray_id:
        #         vals["printer_output_tray_id"] = \
        #             printer_config.printer_output_tray_id.id

        # Check all default_vals fields
        for default_val in default_vals:
            if default_val not in vals:
                value = getattr(default_config, default_val, False) or getattr(
                    config, default_val, False
                )
                if default_val.endswith("_id"):
                    value = value.id
                vals[default_val] = value

        return config

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
                if (
                    job.need_call == "before_sending" and job.state == "pending"
                ) and not job.activity_ids:
                    job.with_user(job.user_id.id).schedule_call()

        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def send(self):
        """Executes the job."""
        todo = self.filtered(
            lambda j: j.state == "pending"
            and not (j.need_call == "before_sending" and j.activity_ids)
        )

        # Filter jobs for SMS
        sms_jobs = self.filtered(lambda j: j.send_mode == "sms")
        sms_jobs.send_by_sms()

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
                job.with_user(job.user_id.id).schedule_call()
        if to_print:
            return to_print._print_report()
        return self.download_data()

    def schedule_call(self):
        self.ensure_one()
        self.activity_schedule(
            "mail.mail_activity_data_call",
            summary="Call " + self.partner_id.name,
            user_id=self.user_id.id,
            note=f"Call {self.partner_id.name} at (phone) "
            f"{self.partner_id.phone or self.partner_id.mobile} regarding "
            f"the communication.",
        )

    def cancel(self):
        self.mapped("activity_ids").unlink()
        return self.write({"state": "cancel"})

    def reset(self):
        self.mapped("attachment_ids").write({"printed_pdf_data": False})
        self.write(
            {
                "state": "pending",
                "sent_date": False,
                "email_id": False,
                "printed_pdf_data": False,
            }
        )
        return True

    def send_by_sms(self):
        """
        Sends communication jobs with SMS 939 service.
        :return: list of sms_texts
        """
        link_pattern = re.compile(r'<a href="([^<>]*)">([^<]*)</a>')
        sms_medium_id = self.env.ref("mass_mailing_sms.utm_medium_sms").id
        sms_texts = []
        for job in self.filtered(lambda j: j.state == "pending" and j.partner_mobile):
            sms_text = job.convert_html_for_sms(link_pattern, sms_medium_id)
            sms_texts.append(sms_text)
            job.partner_id.message_post_send_sms(sms_text, note_msg=job.subject)
            job.write(
                {
                    "state": "done",
                    "sent_date": fields.Datetime.now(),
                }
            )
            _logger.debug("SMS length: %s", len(sms_text))
        return sms_texts

    def convert_html_for_sms(self, link_pattern, sms_medium_id):
        """
        Converts HTML into simple text for SMS.
        First replace links with short links using Link Tracker.
        Then clean HTML using BeautifulSoup library.
        :param link_pattern: the regex pattern for replacing links
        :param sms_medium_id: the associated utm.medium id for generated links
        :return: Clean text with short links for SMS use.
        """
        self.ensure_one()
        source_id = self.config_id.source_id.id
        paragraph_delimiter = "###P###"

        def _replace_link(match):
            full_link = match.group(1).replace("&amp;", "&")
            short_link = self.env["link.tracker"].search(
                [
                    ("url", "=", full_link),
                    ("source_id", "=", source_id),
                    ("medium_id", "=", sms_medium_id),
                ]
            )
            if not short_link:
                short_link = self.env["link.tracker"].create(
                    {
                        "url": full_link,
                        "campaign_id": self.utm_campaign_id.id
                        or self.env.ref(
                            "partner_communication_compassion."
                            "utm_campaign_communication"
                        ).id,
                        "medium_id": sms_medium_id,
                        "source_id": source_id,
                    }
                )
            return short_link.short_url

        body = self.body_html.replace("\n", " ").replace(
            "</p>", "</p>" + paragraph_delimiter
        )
        body = link_pattern.sub(_replace_link, body)
        body = re.sub(r"[ \t\r\f\v]+", " ", body)
        body = re.sub(r"<br>|<br/>", "\n", body)
        soup = BeautifulSoup(body, "lxml")
        text = soup.get_text().replace(paragraph_delimiter, "\n\n")
        return "\n".join([t.strip() for t in text.split("\n")])

    def refresh_text(self):
        self.mapped("attachment_ids").unlink()
        failed = self.set_attachments()
        for job in self - failed:
            lang = self.env.context.get("lang_preview", job.partner_id.lang)
            if job.email_template_id and job.object_ids:
                try:
                    fields = job.email_template_id.with_context(
                        template_preview_lang=lang
                    ).generate_email(job.ids, ["body_html", "subject"])
                    job.write(
                        {
                            "body_html": fields[job.id]["body_html"],
                            "subject": fields[job.id]["subject"],
                            "state": job.state if job.state != "failure" else "pending",
                        }
                    )
                except (
                    MissingError,
                    UserError,
                    QWebException,
                    TemplateSyntaxError,
                ) as e:
                    _logger.error(
                        f"Failed to generate communication {str(e)}",
                        exc_info=True,
                    )
                    job.env.clear()
                    if job.state == "pending":
                        job.write(
                            {
                                "state": "failure",
                                "body_html": f"{str(type(e))} {str(e)}",
                            }
                        )
        return True

    def quick_refresh(self):
        # Only refresh text and subject, all at once
        jobs = self.filtered("email_template_id").filtered("object_ids")
        lang = self.env.context.get("lang_preview", jobs.mapped("partner_id.lang"))
        template = jobs.mapped("email_template_id")
        if len(template) > 1:
            raise UserError(_("This is only possible for one template at time"))
        values = template.with_context(template_preview_lang=lang).generate_email(
            jobs.ids, ["body_html", "subject"]
        )
        for job, vals in zip(jobs, values.values()):
            job.write(
                {
                    "body_html": vals["body_html"],
                    "subject": vals["subject"],
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

    def open_related(self):
        object_ids = list(map(int, self.object_ids.split(",")))
        action = {
            "name": _("Related objects"),
            "type": "ir.actions.act_window",
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

    def get_objects(self):
        model = list(set(self.mapped("config_id.model")))
        assert len(model) == 1
        object_ids = list()
        object_id_strings = self.mapped("object_ids")
        for id_strings in object_id_strings:
            object_ids += list(map(int, id_strings.split(",")))
        return self.env[model[0]].browse(set(object_ids))

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
                except Exception:
                    _logger.error("Error during attachment creation", exc_info=True)
                    job.env.clear()
                    if job.state == "pending":
                        job.write(
                            {
                                "state": "failure",
                                "body_html": "Error in attachments creation.",
                            }
                        )
                    failed += job
        return failed

    def preview_pdf(self):
        preview_model = "partner.communication.pdf.wizard"
        preview = self.env[preview_model].create({"communication_id": self.id})
        return {
            "name": _("Preview"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": preview_model,
            "res_id": preview.id,
            "context": self.env.context,
            "target": "new",
        }

    def download_data(self):
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": self._name,
            "domain": [("id", "in", self.ids)],
            "name": _("Send result"),
        }
        to_download = self.filtered("printed_pdf_data")
        if to_download:
            # Redirect user for fetching the printed data
            res_wizard = self.env[
                "partner.communication.download.print.job.wizard"
            ].create({"communication_job_ids": [(6, 0, to_download.ids)]})
            action.update(
                {
                    "view_mode": "form",
                    "res_model": "partner.communication.download.print.job.wizard",
                    "res_id": res_wizard.id,
                    "target": "new",
                    "domain": [],
                }
            )
        return action

    @api.model
    def get_snippet(self, snippet_name):
        return (
            self.env["communication.snippet"]
            .search([("name", "=", snippet_name)])
            .snippet_text
        )

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
            }
            if "default_email_vals" in self.env.context:
                email_vals.update(self.env.context["default_email_vals"])

            email = (
                self.env["mail.compose.message"]
                .with_context(lang=partner.lang)
                .create_emails(self.email_template_id, [self.id], email_vals)
            )
            self.email_id = email

            try:
                with self.env.cr.savepoint():
                    email.send()
            except Exception:
                _logger.error(
                    "Error while sending communication by email to %s ",
                    partner.email,
                    exc_info=True,
                )
                return "failure"

            # Subscribe author to thread, so that the reply
            # notifies the author.
            self.message_subscribe(self.user_id.partner_id.ids)

        return "done"

    def _print_report(self):
        name = self.env.user.name
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
                try:
                    with self.env.cr.savepoint():
                        # Print letter
                        print_name = name[:3] + " " + (job.subject or "")
                        # output_tray = job.print_letter(print_name)["output_tray"]
                        job.print_letter(print_name)

                        # Print attachments in the same output_tray
                        job.attachment_ids.print_attachments(
                            # output_tray=output_tray,
                        )
                        job.write({"state": state, "sent_date": fields.Datetime.now()})
                except Exception:
                    _logger.error("Error printing job %s", [job.id])
            else:
                batch_print[job.partner_id.lang][job.config_id.name] += job

        for configs in batch_print.values():
            for config, jobs in configs.items():
                try:
                    print_name = name[:3] + " " + config
                    jobs.print_letter(print_name)
                    jobs.write({"state": state, "sent_date": fields.Datetime.now()})
                except Exception:
                    _logger.error(
                        "Error while printing jobs %s", str(jobs.ids), exc_info=True
                    )
        return self.download_data()

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
        config_lang = self.mapped("config_id.default_config_ids").filtered(
            lambda c: c.lang_id.code == lang
        )

        if len(report) > 1 or len(config_lang) > 1:
            raise UserError(
                _("Cannot print multiple communication types at the same time.")
            )

        behaviour = report.behaviour()

        print_options["doc_format"] = report.report_type
        print_options["action"] = behaviour["action"]

        # TODO Migrate this code when printing.tray functionalities are migrated to 14.0
        # # The get the print options in the following order of priority:
        # # - partner.communication.job (only for output bin)
        # # - partner.communication.config
        # # - ir.actions.report (behaviour: which can be specific for the user
        # currently logged in)
        # def get_first(source):
        #     return next((v for v in source if v), False)
        #
        # print_options["output_tray"] = get_first((
        #     self[:1].printer_output_tray_id.system_name,
        #     config_lang.printer_output_tray_id.system_name,
        #     behaviour["output_tray"]
        # ))
        # print_options["input_tray"] = get_first((
        #     config_lang.printer_input_tray_id.system_name,
        #     behaviour["input_tray"]
        # ))

        to_print = report._render_qweb_pdf(self.ids)
        printer = behaviour["printer"].with_context(lang=lang)
        if behaviour["action"] == "server" and printer:
            # Get pdf should directly send it to the printer
            printer.print_document(report, to_print[0], **print_options)
        else:
            # Store result in one communication
            # (for later download from the result wizard)
            self[:1].printed_pdf_data = base64.b64encode(to_print[0])

        return print_options
