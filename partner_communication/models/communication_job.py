# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import logging

from openerp import api, models, fields, _, http
from openerp.addons.base_phone.controller import BasePhoneController

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
        'partner.communication.config', 'Type', required=True, readonly=True,
        default=lambda s: s.env.ref(
                'partner_communication.default_communication'),
    )
    partner_id = fields.Many2one(
        'res.partner', 'Send to', required=True,
        domain=[('opt_out', '=', False)])
    partner_phone = fields.Char(related='partner_id.phone')
    partner_mobile = fields.Char(related='partner_id.mobile')
    object_ids = fields.Char('Resource ids', required=True)

    date = fields.Datetime(default=fields.Datetime.now)
    sent_date = fields.Datetime()
    state = fields.Selection([
        ('pending', _('Pending')),
        ('done', _('Done')),
        ('cancel', _('Cancelled')),
    ], default='pending', readonly=True, track_visibility='onchange')

    auto_send = fields.Boolean(
        help='Job is processed at creation if set to true')
    send_mode = fields.Selection([
        ('digital', 'By e-mail'), ('physical', 'Print report'),
        ('both', 'Both')
    ])
    email_template_id = fields.Many2one(
        related='config_id.email_template_id', store=True)
    report_id = fields.Many2one(related='config_id.report_id', store=True)
    user_id = fields.Many2one(
        'res.users', 'From', default=lambda s: s.env.user)
    email_to = fields.Char(
        help='optional e-mail address to override recipient')
    email_id = fields.Many2one('mail.mail', 'Generated e-mail')
    phonecall_id = fields.Many2one('crm.phonecall', 'Phonecall log')

    body_html = fields.Html()
    subject = fields.Char()
    attachment_ids = fields.One2many(
        'partner.communication.attachment', 'communication_id',
        string="Attachments")
    ir_attachment_ids = fields.Many2many(
        'ir.attachment', compute='_compute_ir_attachments')

    def _compute_ir_attachments(self):
        for job in self:
            job.ir_attachment_ids = job.mapped('attachment_ids.attachment_id')

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

        job = self.search([
            ('partner_id', '=', vals.get('partner_id')),
            ('config_id', '=', vals.get('config_id')),
            ('state', '=', 'pending')
        ])
        if job:
            job.object_ids = job.object_ids + ',' + vals['object_ids']
            job.refresh_text()
            return job

        partner = self.env['res.partner'].browse([vals['partner_id']])
        if partner.opt_out:
            return self

        job = super(CommunicationJob, self).create(vals)
        job.set_attachments()
        if not job.body_html:
            job.refresh_text()

        send_mode = job.config_id.get_inform_mode(job.partner_id)
        if 'send_mode' not in vals:
            job.send_mode = send_mode[0]
        if 'auto_send' not in vals:
            job.auto_send = send_mode[1]
        if job.auto_send:
            job.send()
        return job

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def send(self):
        """ Executes the job. """
        for job in self.filtered(lambda j: j.send_mode in ('both', 'digital')):
            state = job._send_mail()
            if job.send_mode != 'both':
                job.write({
                    'state': state,
                    'sent_date': fields.Datetime.now()
                })
            else:
                # Job was sent by e-mail and must now be printed
                job.send_mode = 'physical'
                job.refresh_text()

        # Commit after sending by e-mail
        self.env.cr.commit()
        to_print = self.filtered(lambda j: j.send_mode == 'physical')
        if to_print:
            to_print.write({
                'state': 'done',
                'sent_date': fields.Datetime.now()
            })
            return to_print._print_report()
        return True

    @api.multi
    def cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def reset(self):
        self.write({
            'state': 'pending',
            'date_sent': False,
            'email_id': False,
        })

    @api.multi
    def refresh_text(self):
        for job in self:
            if job.email_template_id and job.object_ids:
                fields = self.env['mail.compose.message'].with_context(
                    lang=job.partner_id.lang).get_generated_fields(
                    job.email_template_id, [job.id])
                job.write({
                    'body_html': fields['body_html'],
                    'subject': fields['subject'],
                })

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.config_id and self.partner_id:
            self.send_mode = self.config_id.get_inform_mode(self.partner_id)[0]

    @api.multi
    def open_related(self):
        object_ids = map(int, self.object_ids.split(','))
        action = {
            'name': _('Related objects'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': self.config_id.model,
            'context': self.env.context,
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
        self.ensure_one()
        object_ids = map(int, self.object_ids.split(','))
        return self.env[self.config_id.model].browse(object_ids)

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
                for name, data in binaries.iteritems():
                    attachment_obj.create({
                        'name': name,
                        'communication_id': job.id,
                        'report_name': data[0],
                        'data': data[1],
                    })

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
                'attachment_ids': [(6, 0, self.ir_attachment_ids.ids)]
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
            email.send_sendgrid()

        return 'done' if email.state == 'sent' else 'pending'

    def _print_report(self):
        report_obj = self.env['report']
        for job in self:
            # Get pdf should directly send it to the printer if report
            # is correctly configured.
            report_obj.get_pdf(job, job.report_id.report_name)
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
        return [('state', '=', 'pending')]
