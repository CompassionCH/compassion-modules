##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from io import StringIO, BytesIO
import logging
import threading
from html.parser import HTMLParser

from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import white

from odoo import api, models, fields, _, tools
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)
testing = tools.config.get('test_enable')

try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
except ImportError:
    logger.warning("Please install PyPDF2 for generating OMR codes in "
                   "Printed partner communications")


class MLStripper(HTMLParser):
    """ Used to remove HTML tags. """

    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


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
    _name = 'partner.communication.job'
    _description = 'Communication Job'
    _rec_name = 'subject'
    _order = 'date desc,sent_date desc'
    _inherit = ['partner.communication.defaults', 'mail.activity.mixin',
                'mail.thread', 'partner.communication.orm.config.abstract',
                'phone.validation.mixin']
    _phone_name_fields = ['partner_phone', 'partner_mobile']

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    config_id = fields.Many2one(
        'partner.communication.config', 'Type', required=True,
        default=lambda s: s.env.ref(
            'partner_communication.default_communication'),
    )
    model = fields.Char(related='config_id.model')
    partner_id = fields.Many2one(
        'res.partner', 'Send to', required=True, ondelete='cascade')
    partner_phone = fields.Char(related='partner_id.phone')
    partner_mobile = fields.Char(related='partner_id.mobile')
    country_id = fields.Many2one(related='partner_id.country_id')
    parent_id = fields.Many2one(related='partner_id.parent_id')
    object_ids = fields.Char('Resource ids', required=True)
    date = fields.Datetime(default=fields.Datetime.now)
    sent_date = fields.Datetime(readonly=True, copy=False)
    state = fields.Selection([
        ('call', _('Call partner')),
        ('pending', _('Pending')),
        ('done', _('Done')),
        ('cancel', _('Cancelled')),
    ], default='pending', track_visibility='onchange', copy=False)
    need_call = fields.Selection(
        [('before_sending', 'Before the communication is sent'),
         ('after_sending', 'After the communication is sent')],
        help='Indicates we should have a personal contact with the partner',
    )
    auto_send = fields.Boolean(
        help='Job is processed at creation if set to true', copy=False)
    send_mode = fields.Selection('send_mode_select')
    email_template_id = fields.Many2one(
        related='config_id.email_template_id', store=True)
    email_to = fields.Char(
        help='optional e-mail address to override recipient')
    email_id = fields.Many2one(
        'mail.mail', 'Generated e-mail', readonly=True, index=True, copy=False)
    phonecall_id = fields.Many2one('crm.phonecall', 'Phonecall log',
                                   readonly=True)
    body_html = fields.Html(sanitize=False)
    pdf_page_count = fields.Integer(string='PDF size',
                                    readonly=True)
    subject = fields.Char()
    attachment_ids = fields.One2many(
        'partner.communication.attachment', 'communication_id',
        string="Attachments")
    ir_attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        compute='_compute_ir_attachments',
        inverse='_inverse_ir_attachments',
        domain=[('report_id', '!=', False)]
    )
    ir_attachment_tmp = fields.Many2many('ir.attachment', string='Attachments',
                                         compute='_compute_void',
                                         inverse='_inverse_ir_attachment_tmp')

    def _compute_ir_attachments(self):
        for job in self:
            job.ir_attachment_ids = job.mapped('attachment_ids.attachment_id')

    def count_pdf_page(self):
        skip_count = self.env.context.get(
            'skip_pdf_count',
            getattr(threading.currentThread(), 'testing', False)
        )
        if not skip_count:
            for record in self.filtered('report_id'):
                if record.send_mode == 'physical':
                    report = record.report_id.with_context(
                        lang=record.partner_id.lang,
                        must_skip_send_to_printer=True)
                    pdf_str = report.render_qweb_pdf(record.ids)
                    pdf = PdfFileReader(BytesIO(pdf_str[0]))
                    record.pdf_page_count = pdf.getNumPages()

    def _inverse_ir_attachments(self):
        attach_obj = self.env['partner.communication.attachment']
        for job in self:
            for attachment in job.ir_attachment_ids:
                if attachment not in job.attachment_ids.mapped(
                        'attachment_id'):
                    if not attachment.report_id and not \
                            self.env.context.get('no_print'):
                        raise UserError(
                            _("Please select a printing configuration for the "
                              "attachments you add.")
                        )
                    attach_obj.create({
                        'name': attachment.name,
                        'communication_id': job.id,
                        'report_name': attachment.report_id.report_name or '',
                        'attachment_id': attachment.id
                    })
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
                    'partner_communication.report_a4_no_margin')
            job.ir_attachment_ids += job.ir_attachment_tmp

    @api.model
    def send_mode_select(self):
        return [
            ('digital', _('By e-mail')),
            ('physical', _('Print report')),
            ('both', _('Both'))
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
        object_ids = vals.get('object_ids')
        if isinstance(object_ids, list):
            vals['object_ids'] = ','.join(map(str, object_ids))
        elif object_ids:
            vals['object_ids'] = str(object_ids)
        else:
            vals['object_ids'] = str(vals['partner_id'])

        same_job_search = [('partner_id', '=', vals.get('partner_id')),
                           ('config_id', '=', vals.get('config_id')),
                           ('config_id', '!=',
                            self.env.ref(
                                'partner_communication.default_communication'
                            ).id),
                           ('state', 'in', ('call', 'pending'))
                           ] + self.env.context.get('same_job_search', [])
        job = self.search(same_job_search)
        if job:
            job.object_ids = job.object_ids + ',' + vals['object_ids']
            job.refresh_text()
            return job

        self._get_default_vals(vals)
        job = super().create(vals)

        # Determine send mode
        send_mode = job.config_id.get_inform_mode(job.partner_id)

        if 'send_mode' not in vals and 'default_send_mode' not in \
                self.env.context:
            job.send_mode = send_mode[0]
        if 'auto_send' not in vals and 'default_auto_send' not in \
                self.env.context:
            job.auto_send = send_mode[1]

        if not job.body_html or not strip_tags(job.body_html):
            job.refresh_text()
        else:
            job.set_attachments()

        # Check if phonecall is needed
        if job.need_call == 'before_sending' or \
                job.config_id.need_call == 'before_sending':
            job.state = 'call'

        if job.body_html or job.send_mode == 'physical':
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
        vals['auto_send'] = False
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
        default_vals.extend(['report_id', 'need_call', 'omr_enable_marks',
                             'omr_should_close_envelope',
                             'omr_add_attachment_tray_1',
                             'omr_add_attachment_tray_2',
                             'omr_top_mark_x', 'omr_top_mark_y',
                             'omr_single_sided',
                             ])

        partner = self.env['res.partner'].browse(vals.get('partner_id'))
        lang_of_partner = self.env['res.lang'].search([
            ('code', 'like', partner.lang or self.env.lang)
        ])
        config = self.config_id.browse(vals['config_id']).with_context(
            lang=lang_of_partner.code)

        # Determine user by default : take in config or employee
        omr_config = config.get_config_for_lang(lang_of_partner)[:1]
        if not vals.get('user_id'):
            # responsible for the communication is user specified in the omr_config
            # or user specified in the config itself
            # or the current user
            user_id = self.env.uid
            if omr_config.user_id:
                user_id = omr_config.user_id.id
            elif config.user_id:
                user_id = config.user_id.id
            vals['user_id'] = user_id

        # Check all default_vals fields
        for default_val in default_vals:
            if default_val not in vals:
                if default_val.startswith('omr_'):
                    value = getattr(omr_config, default_val, False)
                else:
                    value = getattr(config, default_val)
                    if default_val.endswith('_id'):
                        value = value.id
                vals[default_val] = value

        return config

    @api.multi
    def write(self, vals):
        object_ids = vals.get('object_ids')
        if isinstance(object_ids, list):
            vals['object_ids'] = ','.join(map(str, object_ids))
        elif object_ids:
            vals['object_ids'] = str(object_ids)

        super().write(vals)

        if vals.get('body_html') or vals.get('send_mode') == 'physical':
            self.count_pdf_page()

        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def send(self):
        """ Executes the job. """
        todo = self.filtered(lambda j: j.state == 'pending')
        to_print = todo.filtered(lambda j: j.send_mode == 'physical')
        for job in todo.filtered(lambda j: j.send_mode in ('both',
                                                           'digital')):
            state = job._send_mail()
            if job.send_mode != 'both':
                job.write({
                    'state': state,
                    'sent_date': state != 'pending' and fields.Datetime.now()
                })
            else:
                # Job was sent by e-mail and must now be printed
                job.send_mode = 'physical'
                job.refresh_text()

        if to_print:
            return to_print._print_report()
        return True

    @api.multi
    def cancel(self):
        to_call = self.filtered(lambda j: j.state == 'call')
        for job in to_call:
            state = 'pending'
            if job.need_call == 'after_sending' and job.sent_date:
                state = 'done'
            to_call.write({'state': state, 'need_call': False})
        (self - to_call).write({'state': 'cancel'})
        return True

    @api.multi
    def reset(self):
        self.write({
            'state': 'pending',
            'date_sent': False,
            'email_id': False,
        })
        return True

    @api.multi
    def refresh_text(self, refresh_uid=False):
        self.mapped('attachment_ids').unlink()
        self.set_attachments()
        for job in self:
            lang = self.env.context.get('lang_preview', job.partner_id.lang)
            if job.email_template_id and job.object_ids:
                fields = self.env['mail.compose.message'].with_context(
                    lang=lang).get_generated_fields(
                    job.email_template_id, [job.id])
                job.write({
                    'body_html': fields['body_html'],
                    'subject': fields['subject'],
                })
                if refresh_uid:
                    job.user_id = self.env.user
        return True

    @api.multi
    def quick_refresh(self):
        # Only refresh text and subject, all at once
        jobs = self.filtered('email_template_id').filtered('object_ids')
        lang = self.env.context.get('lang_preview', jobs.mapped(
            'partner_id.lang'))
        template = jobs.mapped('email_template_id')
        if len(template) > 1:
            raise UserError(_(
                "This is only possible for one template at time"))
        values = self.env['mail.compose.message'].with_context(
            lang=lang).get_generated_fields(template, jobs.ids)
        if not isinstance(values, list):
            values = [values]
        for index in range(0, len(values)):
            jobs[index].write({
                'body_html': values[index]['body_html'],
                'subject': values[index]['subject']
            })
        return True

    @api.onchange('config_id', 'partner_id')
    def onchange_config_id(self):
        if self.config_id and self.partner_id:
            send_mode = self.config_id.get_inform_mode(self.partner_id)
            self.send_mode = send_mode[0]
            # set default fields
            partner_id = None
            if self.partner_id:
                partner_id = self.partner_id.id
            default_vals = {'config_id': self.config_id.id,
                            'partner_id': partner_id}
            self._get_default_vals(default_vals)
            for key, val in list(default_vals.items()):
                if key.endswith('_id'):
                    val = getattr(self, key).browse(val)
                setattr(self, key, val)

    @api.onchange('need_call')
    def onchange_need_call(self):
        if self.need_call == 'before_sending' and self.state == 'pending':
            self.state = 'call'
        if self.need_call == 'after_sending':
            if self.state == 'done':
                self.state = 'call'
            elif self.state == 'call' and not self.sent_date:
                self.state = 'pending'
        if not self.need_call and self.state == 'call':
            self.state = 'pending' if not self.sent_date else 'done'

    @api.multi
    def open_related(self):
        object_ids = list(map(int, self.object_ids.split(',')))
        action = {
            'name': _('Related objects'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': self.config_id.model,
            'context': self.with_context(group_by=False).env.context,
            'target': 'current',
        }
        if len(object_ids) > 1:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', object_ids)]
            })
        else:
            action['res_id'] = object_ids[0]

        return action

    @api.multi
    def log_call(self):
        return {
            'name': _("Log your call"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'partner.communication.call.wizard',
            'context': self.with_context({
                'click2dial_id': self.id,
                'phone_number': self.partner_phone or self.partner_mobile,
                'timestamp': fields.Datetime.now(),
                'default_communication_id': self.id,
            }).env.context,
            'target': 'new',
        }

    @api.multi
    def call(self):
        """ Call partner from tree view button. """
        self.ensure_one()
        self.env['phone.common'].with_context(
            click2dial_model=self._name, click2dial_id=self.id) \
            .click2dial(self.partner_phone or self.partner_mobile)
        return self.log_call()

    @api.multi
    def get_objects(self):
        model = list(set(self.mapped('config_id.model')))
        assert len(model) == 1
        object_ids = list()
        object_id_strings = self.mapped('object_ids')
        for id_strings in object_id_strings:
            object_ids += list(map(int, id_strings.split(',')))
        return self.env[model[0]].browse(set(object_ids))

    @api.multi
    def set_attachments(self):
        """
        Generates attachments for the communication and link them to the
        communication record.
        """
        attachment_obj = self.env['partner.communication.attachment']
        for job in self.with_context(must_skip_send_to_printer=True):
            if job.config_id.attachments_function:
                binaries = getattr(
                    job.with_context(lang=job.partner_id.lang),
                    job.config_id.attachments_function, dict())()
                for name, data in list(binaries.items()):
                    attachment_obj.create({
                        'name': name,
                        'communication_id': job.id,
                        'report_name': data[0],
                        'data': data[1],
                    })

    @api.multi
    def preview_pdf(self):
        preview_model = 'partner.communication.pdf.wizard'
        preview = self.env[preview_model].create({
            'communication_id': self.id
        })
        return {
            'name': _("Preview"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': preview_model,
            'res_id': preview.id,
            'context': self.env.context,
            'target': 'new',
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

        pdf_buffer = StringIO()
        pdf_buffer.write(pdf_data)

        existing_pdf = PdfFileReader(pdf_buffer)
        output = PdfFileWriter()
        total_pages = existing_pdf.getNumPages()

        def lastpair(a):
            b = a - 1
            if self.omr_single_sided or b % 2 == 0:
                return b
            return lastpair(b)

        # print latest omr mark on latest pair page (recto)
        latest_omr_page = lastpair(total_pages)

        for page_number in range(total_pages):
            page = existing_pdf.getPage(page_number)
            # only print omr marks on pair pages (recto)
            if self.omr_single_sided or page_number % 2 == 0:
                is_latest_page = is_latest_document and \
                    page_number == latest_omr_page
                marks = self._compute_marks(is_latest_page)
                omr_layer = self._build_omr_layer(marks)
                page.mergePage(omr_layer)
            output.addPage(page)

        out_buffer = StringIO()
        output.write(out_buffer)

        return out_buffer.getvalue()

    def _compute_marks(self, is_latest_page):
        marks = [
            True,  # Start mark (compulsory)
            is_latest_page,
            is_latest_page and self.omr_add_attachment_tray_1,
            is_latest_page and self.omr_add_attachment_tray_2,
            is_latest_page and not self.omr_should_close_envelope
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

        logger.info(
            'Mailer DS-75i OMR Settings: 1=%s 2=%s',
            str((297 * mm - top_mark_y) / mm),
            str((top_mark_x + mark_width / 2) / mm + 0.5)
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
            stroke=False
        )

        for offset, mark in enumerate(marks):
            mark_y = top_mark_y - offset * mark_y_spacing
            if mark:
                omr_canvas.line(top_mark_x, mark_y,
                                top_mark_x + mark_width, mark_y)

        # Close the PDF object cleanly.
        omr_canvas.showPage()
        omr_canvas.save()

        # move to the beginning of the StringIO buffer
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
                'recipient_ids': [(4, partner.id)],
                'communication_config_id': self.config_id.id,
                'body_html': self.body_html,
                'subject': self.subject,
                'attachment_ids': [(6, 0, self.ir_attachment_ids.ids)],
                'auto_delete': False,
                'reply_to': (self.email_template_id.reply_to or
                             self.user_id.email),
            }
            if self.email_to:
                # Replace partner e-mail by specified address
                email_vals['email_to'] = self.email_to
                del email_vals['recipient_ids']
            if 'default_email_vals' in self.env.context:
                email_vals.update(
                    self.env.context['default_email_vals'])

            email = self.env['mail.compose.message'].with_context(
                lang=partner.lang).create_emails(
                self.email_template_id, [self.id], email_vals)
            self.email_id = email
            email.send()
            # Subscribe author to thread, so that the reply
            # notifies the author.
            self.message_subscribe(self.user_id.partner_id.ids)

        final_state = 'pending'
        if email.state == 'sent':
            if self.need_call == 'after_sending':
                final_state = 'call'
            else:
                final_state = 'done'
        return final_state

    def _print_report(self):
        name = self.env.user.firstname or self.env.user.name
        for job in self:
            report = job.report_id.with_context(
                print_name=name[:3] + ' ' + (job.subject or ''),
                must_skip_send_to_printer=True,
                lang=job.partner_id.lang
            )
            # Get pdf should directly send it to the printer if report
            # is correctly configured.
            to_print = report.render_qweb_pdf(job.ids)

            # Print letter
            report = job.report_id
            behaviour = report.behaviour()
            printer = behaviour['printer'] \
                .with_context(lang=job.partner_id.lang)
            if behaviour['action'] != 'client' and printer:
                printer.print_document(
                    report.report_name, to_print[0], format=report.report_type)

            # Print attachments
            job.attachment_ids.print_attachments()
            job.write({
                'state': 'call' if job.need_call == 'after_sending'
                else 'done',
                'sent_date': fields.Datetime.now()
            })
            if not testing:
                # Commit to avoid invalid state if process fails
                self.env.cr.commit()  # pylint: disable=invalid-commit
                return True

    @api.model
    def _needaction_domain_get(self):
        """
        Used to display a count icon in the menu
        :return: domain of jobs counted
        """
        return [('state', 'in', ('call', 'pending'))]
