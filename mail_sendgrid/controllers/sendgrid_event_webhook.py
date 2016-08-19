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
from werkzeug.useragents import UserAgent


STATUS_OK = 200

_logger = logging.getLogger(__name__)


class EventWebhook(http.Controller):
    """ Add SendGrid related fields so that they dispatch in all
    subclasses of mail.message object
    """
    @http.route('/sendgrid/events', type='json', auth='public', methods=[
        'POST'])
    def handler_sendgrid(self):
        message_data = request.jsonrequest
        _logger.info("SENDGRID Webhook received: %s" % str(message_data))
        if message_data and isinstance(message_data, list):
            message_data.sort(key=lambda m: m.get('timestamp'))
            for notification in message_data:
                event = notification.get('event')
                recipient = notification.get('email')
                message_id = notification.get('odoo_id')
                t_email = request.env['mail.tracking.email'].sudo().search([
                    ('mail_id.message_id', '=', message_id),
                    ('recipient', '=', recipient)
                ])
                if not t_email:
                    _logger.error("Sendgrid e-mail not found: %s" % message_id)
                    continue

                tracking_event = request.env['mail.tracking.event'].sudo()

                t_vals = {
                    'recipient': recipient,
                    'timestamp': notification.get('timestamp'),
                    'time': fields.Datetime.now(),
                    'tracking_email_id': t_email.id,
                    'ip': notification.get('ip'),
                }
                if notification.get('useragent'):
                    user_agent = UserAgent(notification.get('useragent'))
                    t_vals.update({
                        'user_agent': user_agent.string,
                        'os_family': user_agent.platform,
                        'ua_family': user_agent.browser,
                        'mobile': user_agent.platform in [
                            'android', 'iphone', 'ipad']
                    })
                m_vals = {}

                if event == 'processed':
                    t_vals.update({
                        'event_type': 'sent',
                        'smtp_server': notification.get('smtp-id')
                    })
                    m_vals.update({
                        'state': 'sent',
                    })
                elif event == 'dropped':
                    t_vals.update({
                        'event_type': 'reject',
                        'smtp_server': notification.get('smtp-id')
                    })
                    m_vals.update({
                        'state': 'rejected',
                        'error_description': notification.get('reason'),
                    })
                elif event == 'bounce':
                    t_vals.update({
                        'event_type': 'hard_bounce',
                        'smtp_server': notification.get('smtp-id')
                    })
                    m_vals.update({
                        'state': 'bounced',
                        'error_type': notification.get('status'),
                        'bounce_type': notification.get('type'),
                        'bounce_description': notification.get('reason'),
                    })
                elif event == 'deferred':
                    t_vals.update({
                        'event_type': 'deferral',
                        'smtp_server': notification.get('smtp-id')
                    })
                    m_vals.update({
                        'state': 'deferred',
                        'error_smtp_server': notification.get('response'),
                    })
                elif event == 'delivered':
                    t_vals.update({
                        'event_type': 'delivered',
                        'smtp_server': notification.get('smtp-id')
                    })
                    m_vals.update({
                        'state': 'delivered',
                    })
                elif event == 'open':
                    t_vals.update({
                        'event_type': 'open',

                    })
                    m_vals.update({
                        'state': 'opened',
                    })
                elif event == 'click':
                    t_vals.update({
                        'event_type': 'click',
                        'url': notification.get('url')
                    })
                elif event == 'spamreport':
                    t_vals.update({
                        'event_type': 'spam',
                    })
                    m_vals.update({
                        'state': 'spam',
                    })
                elif event == 'unsubscribe':
                    t_vals.update({
                        'event_type': 'unsub',
                    })
                    m_vals.update({
                        'state': 'unsub',
                    })
                elif event == 'group_unsubscribe':
                    t_vals.update({
                        'event_type': 'unsub',
                    })
                    m_vals.update({
                        'state': 'unsub',
                    })

                # Create tracking event
                tracking_event.create(t_vals)
                # Write email tracking modifications
                if m_vals:
                    t_email.write(m_vals)

            return {'status': 200}

        else:
            return {'status': 400, 'message': 'wrong request'}
