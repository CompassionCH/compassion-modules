# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Roman Zoller, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import base64
import logging
import re

from openerp import models, fields, api, exceptions, _
from openerp.tools.config import config

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *


STATUS_OK = 202

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    """ Add SendGrid related fields so that they dispatch in all
    subclasses of mail.message object
    """
    _inherit = 'mail.message'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    body_text = fields.Text(help='Text only version of the body')
    sent_date = fields.Datetime(copy=False)
    substitution_ids = fields.Many2many(
        'sendgrid.substitution', string='Substitutions', copy=True)
    sendgrid_template_id = fields.Many2one(
        'sendgrid.template', 'Sendgrid Template')
    send_method = fields.Char(compute='_compute_send_method')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    def _compute_send_method(self):
        """ Check whether to use traditional send method, sendgrid or disable.
        """
        send_method = self.env['ir.config_parameter'].get_param(
            'mail_sendgrid.send_method', 'traditional')
        for email in self:
            email.send_method = send_method


class OdooMail(models.Model):
    """ Email message sent through SendGrid """
    _inherit = 'mail.mail'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    sendgrid_failure = fields.Char(readonly=True)
    sendgrid_open = fields.Datetime(
        string='Last opened',
        help='Indicates the last time the recipient opened the e-mail',
        readonly=True)
    sendgrid_clicks = fields.Integer(compute='_compute_clicks', store=True)
    sendgrid_click_ids = fields.One2many(
        'sendgrid.mail.click', 'email_id', string='Registered clicks',
        readonly=True)

    @api.depends('sendgrid_click_ids', 'sendgrid_click_ids.click_count')
    def _compute_clicks(self):
        for mail in self:
            mail.sendgrid_clicks = sum(mail.sendgrid_click_ids.mapped(
                'click_count'))

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def send(self, auto_commit=False, raise_exception=False):
        """ Override send to select the method to send the e-mail. """
        for email in self:
            send_method = email.send_method
            if send_method == 'traditional':
                return super(OdooMail, email).send(
                    auto_commit, raise_exception)
            elif send_method == 'sendgrid':
                return email.send_sendgrid()
            else:
                _logger.warning(
                    "Traditional e-mails are disabled. Please remove system "
                    "parameter mail_sendgrid.send_method if you want to send "
                    "e-mails through your configured SMTP.")
                email.write({'state': 'exception'})
        return True

    @api.one
    def send_sendgrid(self):
        """ Use sendgrid transactional e-mails : e-mails are sent one by
        one. """
        api_key = config.get('sendgrid_api_key')
        if not api_key:
            raise exceptions.Warning(
                'ConfigError',
                _('Missing sendgrid_api_key in conf file'))

        message = Mail()
        message.set_from(Email(self.email_from))
        message.set_reply_to(Email(self.reply_to))
        message.add_custom_arg(CustomArg('odoo_id', self.message_id))
        html = self.body_html or ' '

        # Update message body in associated message, which will be shown in
        # message history view for linked odoo object defined through fields
        # model and res_id
        self.mail_message_id.body = html

        p = re.compile(r'<.*?>')  # Remove HTML markers
        text_only = self.body_text or p.sub('', html.replace('<br/>', '\n'))

        message.add_content(Content("text/plain", text_only))
        message.add_content(Content("text/html", html))

        test_address = config.get('sendgrid_test_address')

        # TODO For now only one personalization (transactional e-mail)
        personalization = Personalization()
        personalization.set_subject(self.subject or ' ')
        if not test_address:
            if self.email_to:
                personalization.add_to(Email(self.email_to))
            for recipient in self.recipient_ids:
                personalization.add_to(Email(recipient.email))
            if self.email_cc:
                personalization.add_cc(Email(self.email_cc))
        else:
            _logger.info('Sending email to test address {}'.format(
                         test_address))
            personalization.add_to(Email(test_address))
            self.email_to = test_address

        if self.sendgrid_template_id:
            message.set_template_id(self.sendgrid_template_id.remote_id)

        for substitution in self.substitution_ids:
            personalization.add_substitution(Substitution(
                substitution.key, substitution.value))

        message.add_personalization(personalization)

        for attachment in self.attachment_ids:
            s_attachment = Attachment()
            # Datas are not encoded properly for sendgrid
            s_attachment.set_content(base64.b64encode(base64.b64decode(
                attachment.datas)))
            s_attachment.set_filename(attachment.name)
            message.add_attachment(s_attachment)

        sg = SendGridAPIClient(apikey=api_key)
        try:
            response = sg.client.mail.send.post(request_body=message.get())
        except Exception as e:
            raise exceptions.Warning(e.read())
        status = response.status_code
        msg = response.body

        if status == STATUS_OK:
            _logger.info(str(msg))
            self.write({
                'sent_date': fields.Datetime.now(),
                'state': 'sent'
            })
        else:
            _logger.error("Failed to send email: {}".format(str(msg)))


class SengridEmailClicks(models.Model):
    """
    Tracks the user clicks on links inside e-mails sent.
    """
    _name = 'sendgrid.mail.click'
    _rec_name = 'url'

    email_id = fields.Many2one('mail.mail', required=True)
    url = fields.Char(required=True)
    click_count = fields.Integer(default=1)
    last_click = fields.Datetime(default=fields.Datetime.now)

    _sql_constraints = [
        ('unique_clicks', 'unique(email_id, url)',
         'This click is already registered')
    ]

    def create(self, vals):
        """ Update count if click is already registered. """
        click = self.search([
            ('email_id', '=', vals['email_id']),
            ('url', '=', vals['url'])
        ])
        if click:
            click.write({
                'click_count': click.click_count + 1,
                'last_click': fields.Datetime.now()
            })
        else:
            click = super(SengridEmailClicks, self).create(vals)

        return click
