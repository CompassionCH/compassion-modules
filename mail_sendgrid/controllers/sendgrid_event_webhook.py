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

from openerp import http, fields
from openerp.http import request


STATUS_OK = 200

_logger = logging.getLogger(__name__)


class EventWebhook(http.Controller):
    """ Add SendGrid related fields so that they dispatch in all
    subclasses of mail.message object
    """
    @http.route('/sendgrid', type='json', auth='public', methods=['POST'])
    def handler_sendgrid(self, key=None):
        message_data = request.jsonrequest
        _logger.info("SENDGRID Webhook received: %s" % str(message_data))
        if message_data and isinstance(message_data, list):
            for notification in message_data:
                event = notification.get('event')
                sendgrid_id = notification.get('sg_message_id')
                email = request.env['mail.mail'].sudo().search([
                    ('sendgrid_id', '=', sendgrid_id),
                    ('sendgrid_id', '!=', False),
                ])
                if not email:
                    # Email has not yet sendgrid_id. Find last e-mail sent
                    if event in ('processed', 'dropped'):
                        recipient = notification.get('email')
                        partners = request.env['res.partner'].sudo().search([
                            ('email', '=', recipient)
                        ])
                        email = request.env['mail.mail'].sudo().search([
                            ('state', '=', 'sent'),
                            ('sendgrid_id', '=', False),
                            ('sent_date', '!=', False),
                            '|', ('email_to', 'ilike', recipient),
                            ('recipient_ids', 'in', partners.ids)
                        ], order='sent_date desc', limit=1)
                        if email:
                            email.sendgrid_id = sendgrid_id
                        else:
                            _logger.error(
                                "Sendgrid e-mail not found: %s" % sendgrid_id)
                            continue
                    else:
                        _logger.error(
                            "Sendgrid e-mail not found: %s" % sendgrid_id)
                        continue

                if event in ('dropped', 'bounce'):
                    # E-mail was not transmitted.
                    email.write({
                        'state': 'exception',
                        'sendgrid_failure': notification.get('reason')})
                elif event == 'delivered':
                    email.state = 'received'
                elif event == 'open':
                    email.sendgrid_open = fields.Datetime.now()
                elif event == 'click':
                    request.env['sendgrid.mail.click'].sudo().create({
                        'email_id': email.id,
                        'url': notification.get('url')
                    })

            return {'status': 200}
        else:
            return {'status': 400, 'message': 'wrong request'}
