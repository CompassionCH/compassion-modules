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


SUBSTITUTION_PREFIX = '{'
SUBSTITUTION_POSTFIX = '}'

STATUS_OK = 200

_logger = logging.getLogger(__name__)


class Email(models.Model):
    """ Email message sent through SendGrid """
    _name = 'sendgrid.email'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    email_to = fields.Char()
    subject = fields.Char()
    body_html = fields.Text()
    body_text = fields.Text()
    sent_date = fields.Datetime()
    substitution_ids = fields.One2many('sendgrid.substitution', 'email_id')
    template_id = fields.Many2one('sendgrid.template')

    @api.one
    def send(self):
        api_key = config.get('sendgrid_api_key')
        if not api_key:
            raise exceptions.Warning(
                'ConfigError',
                _('Missing sendgrid_api_key in conf file'))

        from_address = config.get('sendgrid_from_address')
        if not from_address:
            raise exceptions.Warning(
                'ConfigError',
                _('Missing sendgrid_from_address in conf file'))

        production_mode = config.get('sendgrid_production_mode')

        test_address = config.get('sendgrid_test_address')
        if not test_address:
            # From SendGrid documentation: All messages to this domain are
            # accepted for delivery and then immediately deleted.
            test_address = 'odoo@sink.sendgrid.net'

        sg = sendgrid.SendGridClient(api_key)
        message = sendgrid.Mail()

        message.set_from(from_address)

        subject = self.subject if self.subject else ' '
        message.set_subject(subject)

        text = self.body_text if self.body_text else ' '
        message.set_text(text)

        html = self.body_html if self.body_html else ' '
        message.set_html(html)

        if production_mode:
            message.add_to(self.email_to)
        else:
            _logger.info('Sending email to test address {}'.format(
                         test_address))
            _logger.info('Set sendgrid_production_mode=1 in odoo.conf in'
                         ' order to use real destination address, or set'
                         ' set sendgrid_test_address={test_address} to'
                         ' use another test address.')
            message.add_to(test_address)

        if self.template_id:
            message.add_filter('templates', 'enable', '1')
            message.add_filter('templates', 'template_id',
                               self.template_id.remote_id)

        for substitution in self.substitution_ids:
            formatted_key = '{}{}{}'.format(SUBSTITUTION_PREFIX,
                                            substitution.key,
                                            SUBSTITUTION_POSTFIX)
            message.add_substitution(formatted_key, substitution.value)

        status, msg = sg.send(message)

        if status == STATUS_OK:
            _logger.info("Email sent!")
            self.sent_date = fields.Datetime.now()
        else:
            _logger.error("Failed to send email: {}".format(message))
