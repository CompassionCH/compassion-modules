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


class MailTrackingEvent(models.Model):
    """ Push events to campaign_statistics
    """
    _inherit = 'mail.tracking.event'

    @api.model
    def process_sent(self, tracking_email, metadata):
        res = super(MailTrackingEvent, self).process_sent(
            tracking_email, metadata)
        mail_mail_stats = self.sudo().env['mail.mail.statistics'].search([
            ('mail_mail_id_int', '=', tracking_email.mail_id_int)])
        mail_mail_stats.write({
            'sent': fields.Datetime.now()
        })
        return res

    @api.model
    def process_reject(self, tracking_email, metadata):
        res = super(MailTrackingEvent, self).process_reject(
            tracking_email, metadata)
        mail_mail_stats = self.sudo().env['mail.mail.statistics'].search([
            ('mail_mail_id_int', '=', tracking_email.mail_id_int)])
        mail_mail_stats.write({
            'exception': fields.Datetime.now()
        })
        return res

    @api.model
    def process_hard_bounce(self, tracking_email, metadata):
        res = super(MailTrackingEvent, self).process_hard_bounce(
            tracking_email, metadata)
        mail_mail_stats = self.sudo().env['mail.mail.statistics']
        mail_mail_stats.set_bounced(
            mail_mail_ids=[tracking_email.mail_id_int])
        return res
