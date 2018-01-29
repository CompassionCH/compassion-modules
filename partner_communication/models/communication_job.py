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
import logging

from odoo import api, models, fields, _, http
from odoo.exceptions import UserError
from odoo.addons.base_phone import fields as phone_fields
from odoo.addons.base_phone.controllers.main import BasePhoneController

logger = logging.getLogger(__name__)


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
    _inherit = ['ir.needaction_mixin', 'mail.thread']

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
        help='Indicates we should have a personal contact with the partner',
        readonly=True,
        states={'pending': [('readonly', False)]}
    )

    auto_send = fields.Boolean(
        help='Job is processed at creation if set to true')
    send_mode = fields.Selection('send_mode_select')
    email_template_id = fields.Many2one(
        related='config_id.email_template_id', store=True)
    report_id = fields.Many2one(
        'ir.actions.report.xml', 'Letter template',
        domain=[('model', '=', 'partner.communication.job')]
    )
    user_id = fields.Many2one(
        'res.users', 'From', domain=[('share', '=', False)])
    email_to = fields.Char(
        help='optional e-mail address to override recipient')
    email_id = fields.Many2one('mail.mail', 'Generated e-mail', readonly=True)
    phonecall_id = fields.Many2one('crm.phonecall', 'Phonecall log',
                                   readonly=True)

    body_html = fields.Html()
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
             self.env.ref('partner_communication.default_communication').id),
            ('state', 'in', ('call', 'pending'))
        ] + self.env.context.get('same_job_search', [])
        job = self.search(same_job_search)
        if job:
            job.object_ids = job.object_ids + ',' + vals['object_ids']
            job.refresh_text()
            return job

        job = super(CommunicationJob, self).create(vals)

        # Determine user by default : employee or take in config
        if not vals.get('user_id'):
            user = self.env.user
            if not user.employee_ids and job.config_id.user_id:
                user = job.config_id.user_id
            job.user_id = user

        # Check if phonecall is needed
        if job.need_call or job.config_id.need_call:
            job.state = 'call'

        # Check print report
        if not vals.get('report_id'):
            job.report_id = job.config_id.report_id

        # Determine send mode
        send_mode = job.config_id.get_inform_mode(job.partner_id)
        if 'send_mode' not in vals and 'default_send_mode' not in \
                self.env.context:
            job.send_mode = send_mode[0]
        if 'auto_send' not in vals and 'default_auto_send' not in \
                self.env.context:
            job.auto_send = send_mode[1]

        if not job.body_html:
            job.refresh_text()
        else:
            job.set_attachments()

        if job.auto_send:
            job.send()

        return job

    @api.multi
    def write(self, vals):
        object_ids = vals.get('object_ids')
        if isinstance(object_ids, list):
            vals['object_ids'] = ','.join(map(str, object_ids))
        elif object_ids:
            vals['object_ids'] = str(object_ids)
        if vals.get('need_call'):
            vals['state'] = 'call'

        return super(CommunicationJob, self).write(vals)

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
            to_print.write({
                'state': 'done',
                'sent_date': fields.Datetime.now()
            })
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

    @api.onchange('config_id', 'partner_id')
    def onchange_config_id(self):
        if self.config_id and self.partner_id:
            send_mode = self.config_id.get_inform_mode(self.partner_id)
            self.send_mode = send_mode[0]

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
        phone_controller = BasePhoneController()
        request = http.request
        phone_controller.click2dial(
            request,
            self.partner_phone or self.partner_mobile,
            self._name,
            self.id
        )
        return self.log_call()

    @api.multi
    def get_objects(self):
        config = self.mapped('config_id')
        config.ensure_one()
        object_ids = list()
        object_id_strings = self.mapped('object_ids')
        for id_strings in object_id_strings:
            object_ids += map(int, id_strings.split(','))
        return self.env[config.model].browse(set(object_ids))

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
        return message

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
            report_obj.with_context(
                print_name=self.env.user.firstname[:3] + ' ' + (
                    job.subject or '')
            ).get_pdf(job.ids, job.report_id.report_name)
            # Print attachments
            job.attachment_ids.print_attachments()
            job.partner_id.message_post(
                job.body_html, job.subject)
        return True

    @api.model
    def _needaction_domain_get(self):
        """
        Used to display a count icon in the menu
        :return: domain of jobs counted
        """
        return [('state', 'in', ('call', 'pending'))]
