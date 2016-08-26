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
from openerp import models


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _prepare_sendgrid_tracking(self):
        track_vals = super(MailMail, self)._prepare_sendgrid_tracking()
        track_vals.update({
            'mail_id_int': self.id,
            'mass_mailing_id': self.mailing_id.id,
            'mail_stats_id': self.statistics_ids[:1].id
            if self.statistics_ids else False
        })
        return track_vals
