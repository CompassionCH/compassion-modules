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
from openerp import api, models, fields
import logging


logger = logging.getLogger(__name__)


class Phonecall(models.Model):
    """ Add a communication when phonecall is logged. """
    _inherit = 'crm.phonecall'

    @api.model
    def create(self, vals):
        phonecall_log = super(Phonecall, self).create(vals)
        config = self.env.ref('partner_communication.phonecall_communication')
        self.env['partner.communication.job'].create({
            'config_id': config.id,
            'partner_id': phonecall_log.partner_id.id,
            'user_id': self.uid,
            'object_ids': phonecall_log.partner_id.ids,
            'state': 'done',
            'phonecall_id': phonecall_log.id,
            'sent_date': fields.Datetime.now(),
            'body_html': phonecall_log.name,
            'subject': phonecall_log.name,
        })
        phonecall_log.partner_id.message_post(
            phonecall_log.name, "Phonecall"
        )
        return phonecall_log
