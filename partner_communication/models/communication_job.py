# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import StringIO
import logging
import threading
from HTMLParser import HTMLParser

from odoo.addons.base_phone import fields as phone_fields

from pyPdf import PdfFileReader, PdfFileWriter
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import white

from odoo import api, models, fields, _, tools
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)
testing = tools.config.get('test_enable')


class MLStripper(HTMLParser):
    """ Used to remove HTML tags. """

    def __init__(self):
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
    _order = 'date desc,sent_date desc'
    _inherit = ['partner.communication.defaults', 'ir.needaction_mixin',
                'mail.thread', 'partner.communication.orm.config.abstract']

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
    partner_phone = phone_fields.Phone(related='partner_id.phone')
    partner_mobile = phone_fields.Phone(related='partner_id.mobile')
    country_id = fields.Many2one(related='partner_id.country_id')
    parent_id = fields.Many2one(related='partner_id.parent_id')
    object_ids = fields.Char('Resource ids', required=True)
    date = fields.Datetime(default=fields.Datetime.now)
    sent_date = fields.Datetime(readonly=True)
    state = fields.Selection([
        ('call', _('Call partner')),
        ('pending', _('Pending')),
        ('done', _('Done')),
        ('cancel', _('Cancelled')),
    ], default='pending', readonly=True, track_visibility='onchange')
    need_call = fields.Boolean(
        readonly=True,
        states={'pending': [('readonly', False)]}
    )
    auto_send = fields.Boolean(
        help='Job is processed at creation if set to true')
    send_mode = fields.Selection('send_mode_select')
    email_template_id = fields.Many2one(
        related='config_id.email_template_id', store=True)
    email_to = fields.Char(
        help='optional e-mail address to override recipient')
    email_id = fields.Many2one('mail.mail', 'Generated e-mail', readonly=True)
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
                    report_obj = record.env['report'].with_context(
                        lang=record.partner_id.lang,
                        must_skip_send_to_printer=True)
                    pdf_str = report_obj.get_pdf(record.ids,
                                                 record.report_id.report_name)
                    pdf = PdfFileReader(StringIO.StringIO(pdf_str))
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

        same_job_search = [
            ('partner_id', '=', vals.get('partner_id')),
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
        job = super(CommunicationJob, self).create(vals)

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
        if job.need_call or job.config_id.need_call:
            job.state = 'call'

        if job.body_html or job.send_mode == 'physical':
            job.count_pdf_page()

        if job.auto_send:
            job.send()

        return job

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
                             'omr_add_attachment_tray_2'])

        config = self.config_id.browse(vals['config_id'])

        # Determine user by default : take in config or employee
        if not vals.get('user_id'):
            vals['user_id'] = config.user_id.id or self.env.uid
        user = self.env['res.users'].browse(vals['user_id'])
        orm_config_of_right_lang = config.omr_config_ids \
            .filtered(lambda c: c.lang_id.code == user.lang)
        orm_config = orm_config_of_right_lang[0] if orm_config_of_right_lang \
            else config.omr_config_ids

        # Check all default_vals fields
        for default_val in default_vals:
            if default_val not in vals:
                if default_val.startswith('omr_'):
                    value = getattr(orm_config, default_val, False)
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
        if vals.get('need_call'):
            vals['state'] = 'call'

        super(CommunicationJob, self).write(vals)

        if vals.get('body_html') or vals.get('send_mode') == 'physical':
            self.count_pdf_page()

        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def send(self):
        """ Executes the job. """
        no_call = self.filtered(lambda j: not j.need_call)
        to_print = no_call.filtered(lambda j: j.send_mode == 'physical')
        for job in no_call.filtered(lambda j: j.send_mode in ('both',
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
        to_call.write({'state': 'pending', 'need_call': False})
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
            if job.email_template_id and job.object_ids:
                fields = self.env['mail.compose.message'].with_context(
                    lang=job.partner_id.lang).get_generated_fields(
                    job.email_template_id, [job.id])
                job.write({
                    'body_html': fields['body_html'],
                    'subject': fields['subject'],
                })
                if refresh_uid:
                    job.user_id = self.env.user
                if job.state == 'call' and not job.need_call:
                    job.state = 'pending'

        return True

    @api.multi
    def quick_refresh(self):
        # Only refresh text and subject, all at once
        jobs = self.filtered('email_template_id').filtered('object_ids')
        langs = set(jobs.mapped('partner_id.lang'))
        template = jobs.mapped('email_template_id')
        if len(langs) > 1:
            raise UserError(_("This is only possible for one lang at time"))
        if len(template) > 1:
            raise UserError(_(
                "This is only possible for one template at time"))
        values = self.env['mail.compose.message'].with_context(
            lang=langs.pop()).get_generated_fields(template, jobs.ids)
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
            default_vals = {'config_id': self.config_id.id}
            self._get_default_vals(default_vals)
            for key, val in default_vals.iteritems():
                if key.endswith('_id'):
                    val = getattr(self, key).browse(val)
                setattr(self, key, val)

    @api.multi
    def open_related(self):
        object_ids = map(int, self.object_ids.split(','))
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
                'click2dial_id': self.partner_id.id,
                'phone_number': self.partner_phone or self.partner_mobile,
                'call_name': self.config_id.name,
                'timestamp': fields.Datetime.now(),
                'communication_id': self.id,
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
            object_ids += map(int, id_strings.split(','))
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
                    job.config_id.attachments_function, lambda: dict())()
                for name, data in binaries.iteritems():
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
    def message_post(self, **kwargs):
        """
        If message is not from a user, it is probably the answer of the
        partner by e-mail. We post it on the partner thread instead of
        the communication thread
        :param kwargs: arguments
        :return: mail_message record
        """
        message = super(CommunicationJob, self).message_post(**kwargs)
        if not message.author_id.user_ids:
            message.write({
                'model': 'res.partner',
                'res_id': self.partner_id.id
            })
        return message.id

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

        pdf_buffer = StringIO.StringIO()
        pdf_buffer.write(pdf_data)

        existing_pdf = PdfFileReader(pdf_buffer)
        output = PdfFileWriter()
        total_pages = existing_pdf.getNumPages()

        # print latest omr mark on latest pair page (recto)
        latest_omr_page = total_pages // 2

        for page_number in range(total_pages):
            page = existing_pdf.getPage(page_number)
            # only print omr marks on pair pages (recto)
            if page_number % 2 is 0:
                is_latest_page = is_latest_document and \
                    page_number == latest_omr_page
                marks = self._compute_marks(is_latest_page)
                omr_layer = self._build_omr_layer(marks)
                page.mergePage(omr_layer)
            output.addPage(page)

        out_buffer = StringIO.StringIO()
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

    @staticmethod
    def _build_omr_layer(marks):
        padding_x = 4.2 * mm
        padding_y = 8.5 * mm
        top_mark_x = 7 * mm
        top_mark_y = 220 * mm
        mark_y_spacing = 4 * mm

        mark_width = 6.5 * mm
        marks_height = (len(marks) - 1) * mark_y_spacing

        logger.info('Mailer DS-75i OMR Settings: 1={} 2={}'.format(
            (297 * mm - top_mark_y) / mm,
            (top_mark_x + mark_width / 2) / mm + 0.5
        ))

        omr_buffer = StringIO.StringIO()
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
                             self.user_id.email)
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

        return 'done' if email.state == 'sent' else 'pending'

    def _print_report(self):
        report_obj = self.env['report']

        for job in self:
            # Get pdf should directly send it to the printer if report
            # is correctly configured.
            to_print = report_obj.with_context(
                print_name=self.env.user.firstname[:3] + ' ' + (
                    job.subject or ''),
                must_skip_send_to_printer=True,
                lang=job.partner_id.lang
            ).get_pdf(job.ids, job.report_id.report_name)

            # Print letter
            report = job.report_id
            behaviour = report.behaviour()[report.id]
            printer = behaviour['printer'] \
                .with_context(lang=job.partner_id.lang)
            if behaviour['action'] != 'client' and printer:
                printer.print_document(
                    report.report_name, to_print, report.report_type)

            # Print attachments
            job.attachment_ids.print_attachments()
            # Save info
            job.partner_id.message_post(
                job.body_html, job.subject)
            job.write({
                'state': 'done',
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
