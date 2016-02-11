# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Roman Zoller
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api, exceptions, _
from openerp.tools.config import config

import logging
import sendgrid
import re


SUBSTITUTION_PREFIX = '{'
SUBSTITUTION_POSTFIX = '}'

STATUS_OK = 200

_logger = logging.getLogger(__name__)


class Email(models.Model):
    """ Email message sent through SendGrid """
    _inherit = 'mail.mail'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    body_text = fields.Text()
    sent_date = fields.Datetime(copy=False)
    substitution_ids = fields.One2many(
        'sendgrid.substitution', 'email_id', copy=True)
    layout_template_id = fields.Many2one('sendgrid.template')
    text_template_id = fields.Many2one('email.template')

    @api.model
    def get_default_from(self):
        return config.get('sendgrid_from_address')

    @api.one
    def send_sendgrid(self):
        api_key = config.get('sendgrid_api_key')
        if not api_key:
            raise exceptions.Warning(
                'ConfigError',
                _('Missing sendgrid_api_key in conf file'))

        production_mode = config.get('sendgrid_production_mode')

        test_address = config.get('sendgrid_test_address')
        if not test_address:
            # From SendGrid documentation: All messages to this domain are
            # accepted for delivery and then immediately deleted.
            test_address = 'odoo@sink.sendgrid.net'

        sg = sendgrid.SendGridClient(api_key)
        message = sendgrid.Mail()

        message.set_from(self.email_from)

        if self.text_template_id:
            substitution_dict = {}
            for substitution in self.substitution_ids:
                substitution_dict[substitution.key] = substitution.value
            self.subject = self.text_template_id.subject.format(
                **substitution_dict)
            self.body_html = self.text_template_id.body_html.format(
                **substitution_dict)

        message.set_subject(self.subject or ' ')

        html = self.body_html or ' '
        message.set_html(html)

        # Update message body in associated message, which will be shown in
        # message history view for linked odoo object defined through fields
        # model and res_id
        self.mail_message_id.body = html

        p = re.compile(r'<.*?>')  # Remove HTML markers
        text_only = self.body_text or p.sub('', html.replace('<br/>', '\n'))
        message.set_text(text_only)

        if production_mode:
            message.add_to(self.email_to)
            if self.cc_address:
                message.add_cc(self.cc_address)
        else:
            _logger.info('Sending email to test address {}'.format(
                         test_address))
            _logger.info('Set sendgrid_production_mode=1 in odoo.conf in'
                         ' order to use real destination address, or set'
                         ' set sendgrid_test_address={test_address} to'
                         ' use another test address.')
            message.add_to(test_address)

        if self.layout_template_id:
            message.add_filter('templates', 'enable', '1')
            message.add_filter('templates', 'template_id',
                               self.layout_template_id.remote_id)

        for substitution in self.substitution_ids:
            formatted_key = '{}{}{}'.format(SUBSTITUTION_PREFIX,
                                            substitution.key,
                                            SUBSTITUTION_POSTFIX)
            message.add_substitution(formatted_key, substitution.value)

        status, msg = sg.send(message)

        if status == STATUS_OK:
            _logger.info("Email sent!")
            self.write({
                'sent_date': fields.Datetime.now(),
                'state': 'sent'
            })
        else:
            _logger.error("Failed to send email: {}".format(message))
