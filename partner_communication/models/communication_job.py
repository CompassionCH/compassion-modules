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
from openerp import api, models, fields, _
import logging


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

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    config_id = fields.Many2one('partner.communication.config',
                                'Type', required=True)
    partner_id = fields.Many2one('res.partner', 'Send to', required=True)
    object_id = fields.Integer('Resource id', required=True)

    date = fields.Datetime(default=fields.Datetime.now)
    sent_date = fields.Datetime()
    state = fields.Selection([
        ('pending', _('Pending')),
        ('done', _('Done')),
        ('cancel', _('Cancelled')),
    ], default='pending', readonly=True)

    auto_send = fields.Boolean(
        help='Job is processed at creation if set to true')
    send_mode = fields.Selection(
        [('digital', _('By e-mail')), ('physical', _('Print report'))],
        compute='_compute_send_mode', inverse='_inverse_generation',
        store=True)
    email_template_id = fields.Many2one(
        related='config_id.email_template_id', store=True)
    report_id = fields.Many2one(related='config_id.report_id', store=True)
    from_employee_id = fields.Many2one(
        'hr.employee', 'Communication From',
        help='The sponsor will receive the communication from this employee'
    )
    email_to = fields.Char(
        help='optional e-mail address to override recipient')
    email_id = fields.Many2one('mail.mail', 'Generated e-mail')
    generated_document = fields.Many2one('ir.attachment')

    body_html = fields.Html(
        compute='_compute_html', inverse='_inverse_generation',
        store=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends('partner_id', 'config_id')
    @api.multi
    def _compute_send_mode(self):
        for job in self:
            if job.config_id:
                job.send_mode = job.config_id.get_inform_mode(
                    job.partner_id)[0]

    @api.depends('object_id', 'config_id')
    @api.multi
    def _compute_html(self):
        for job in self:
            if job.object_id and job.email_template_id:
                job.body_html = self.env[
                    'mail.compose.message'].get_generated_html(
                    job.email_template_id, [job.object_id])

    @api.multi
    def _inverse_generation(self):
        # Allow to write on computed field
        return True

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        job = super(CommunicationJob, self).create(vals)
        if 'auto_send' not in vals:
            job.auto_send = job.config_id.get_inform_mode(job.partner_id)[1]
        if 'from_employee_id' not in vals:
            job.from_employee_id = job.config_id.from_employee_id
        if job.auto_send:
            job.send()
        return job

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def send(self):
        """ Executes the job. """
        for job in self:
            if job._inform_sponsor():
                job.write({
                    'state': 'done',
                    'sent_date': fields.Datetime.now()
                })
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
            'generated_document': False
        })

    @api.multi
    def refresh_text(self):
        self._compute_generation()

    def _inform_sponsor(self):
        """ Sends a communication to the sponsor based on the configuration.
        """
        self.ensure_one()
        partner = self.partner_id

        if self.send_mode == 'digital':
            _from = self.from_employee_id.work_email or self.env[
                'ir.config_parameter'].get_param(
                'partner_communication.default_from_address')
            if self.email_to or partner.email:
                # Send by e-mail
                email_vals = {
                    'email_from': _from,
                    'recipient_ids': [(4, partner.id)],
                    # 'communication_config_id': self.id,
                    'communication_config_id': self.config_id.id,
                    'body_html': self.body_html
                }
                if self.email_to:
                    # Replace partner e-mail by specified address
                    email_vals['email_to'] = self.email_to
                    del email_vals['recipient_ids']

                email = self.env['mail.compose.message'].with_context(
                    lang=partner.lang).create_emails(
                    self.email_template_id, [self.object_id], email_vals)
                email.send_sendgrid()
                self.email_id = email
                return True

        elif self.send_mode == 'physical':
            # TODO Print letter
            return False

        # A valid path was not found
        return False
