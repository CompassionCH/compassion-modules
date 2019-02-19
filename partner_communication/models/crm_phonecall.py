# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _
import logging


logger = logging.getLogger(__name__)


class Phonecall(models.Model):
    """ Add a communication when phonecall is logged. """
    _inherit = 'crm.phonecall'

    @api.model
    def create(self, vals):
        phonecall = super(Phonecall, self).create(vals)
        communication_id = self.env.context.get('communication_id')
        if communication_id:
            # Mark communication done when phonecall log created from
            # communication call wizard.
            communication = self.env['partner.communication.job'].browse(
                communication_id)
            if communication.state == 'pending':
                communication.write({
                    'state': 'done',
                    'sent_date': fields.Datetime.now(),
                    'phonecall_id': phonecall.id
                })
            elif communication.state == 'call':
                # Unlock the need call state
                state = 'pending'
                if communication.need_call == 'after_sending' and \
                        communication.sent_date:
                    state = 'done'
                communication.write({
                    'need_call': False,
                    'state': state,
                    'phonecall_id': phonecall.id
                })
            info = _('Phone call with sponsor') + ':' + '<br/>'
            if phonecall.description:
                info += phonecall.description
            communication.partner_id.message_post(
                info, communication.config_id.name)
        else:
            # Phone call was made outside from communication call wizard.
            # Create a communication to log the call.
            config = self.env.ref(
                'partner_communication.phonecall_communication')
            self.env['partner.communication.job'].create({
                'config_id': config.id,
                'partner_id': phonecall.partner_id.id,
                'user_id': self.env.uid,
                'object_ids': phonecall.partner_id.ids,
                'state': 'done',
                'phonecall_id': phonecall.id,
                'sent_date': vals.get('date', fields.Datetime.now()),
                'body_html': phonecall.name,
                'subject': phonecall.name,
                'auto_send': False,
            })
            phonecall.partner_id.message_post(
                phonecall.name, _("Phonecall")
            )
        return phonecall
