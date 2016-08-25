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
from openerp import models, fields, api


class MailTrackingEmail(models.Model):
    """ Count the user clicks on links inside e-mails sent.
    """
    _inherit = 'mail.tracking.email'

    click_count = fields.Integer(compute='_compute_clicks', store=True)

    @api.depends('tracking_event_ids')
    def _compute_clicks(self):
        for mail in self:
            mail.click_count = len(mail.tracking_event_ids.filtered(
                lambda event: event.event_type == 'click'))


class MailTrackingEvent(models.Model):
    """ Add events processing returning values for creating event.
    """
    _inherit = 'mail.tracking.event'

    @api.model
    def process_sent(self, tracking_email, metadata):
        return self._process_action(
            tracking_email, metadata, 'sent', 'sent')

    @api.model
    def process_delivered(self, tracking_email, metadata):
        return self._process_action(
            tracking_email, metadata, 'delivered', 'delivered')

    @api.model
    def process_reject(self, tracking_email, metadata):
        return self._process_action(
            tracking_email, metadata, 'reject', 'rejected')

    @api.model
    def process_hard_bounce(self, tracking_email, metadata):
        return self._process_action(
            tracking_email, metadata, 'hard_bounce', 'bounced')

    @api.model
    def process_deferral(self, tracking_email, metadata):
        return self._process_action(
            tracking_email, metadata, 'deferral', 'deferred')

    @api.model
    def process_click(self, tracking_email, metadata):
        return self._process_action(
            tracking_email, metadata, 'click', 'opened')

    @api.model
    def process_spam(self, tracking_email, metadata):
        return self._process_action(
            tracking_email, metadata, 'spam', 'spam')

    @api.model
    def process_unsub(self, tracking_email, metadata):
        return self._process_action(
            tracking_email, metadata, 'unsub', 'unsub')
