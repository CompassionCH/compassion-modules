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
from datetime import datetime

from openerp import models, api, fields, _


_logger = logging.getLogger(__name__)

try:
    import phonenumbers
except ImportError:
    _logger.error('Please install phonenumbers')


class CallWizard(models.TransientModel):
    _name = 'partner.communication.call.wizard'

    comments = fields.Text()

    @api.multi
    def log_fail(self):
        communication = self.env['partner.communication.job'].browse(
            self.env.context.get('communication_id'))
        communication.message_post(
            self.comments or _('Partner did not answer'),
            _('Phone attempt')
        )
        return True

    @api.multi
    def call_success(self):
        """ Prepare crm.phonecall creation. """
        categ = self.with_context(lang='en_US').env['crm.case.categ'].search(
            [('name', '=', 'Outbound')])
        case_section = self.env['crm.case.section'].search(
            [('member_ids', 'in', self._uid)])
        action_ctx = self.env.context.copy()
        now = self.env.context.get('timestamp')
        if isinstance(now, int):
            now = datetime.fromtimestamp(now / float(1000))
        else:
            now = fields.Datetime.from_string(now)
        call_time = datetime.now() - now
        action_ctx.update({
            'default_categ_id': categ and categ[0].id or False,
            'default_section_id':
                case_section and case_section[0].id or False,
            'default_state': 'done',
            'default_description': self.comments,
            'default_name': self.env.context.get('call_name'),
            'default_duration': call_time.total_seconds() / 60,
        })
        partner_id = self.env.context.get('click2dial_id')
        action_ctx['default_partner_id'] = partner_id
        domain = [('partner_id', '=', partner_id)]
        try:
            parsed_num = phonenumbers.parse(
                self.env.context.get('phone_number'))
            number_type = phonenumbers.number_type(parsed_num)
            if number_type == 1:
                action_ctx['default_partner_mobile'] = \
                    self.env.context.get('phone_number')
            else:
                action_ctx['default_partner_phone'] = \
                    self.env.context.get('phone_number')
        except TypeError:
            _logger.info("Partner has no phone number")
        return {
            'name': _('Phone Call'),
            'domain': domain,
            'res_model': 'crm.phonecall',
            'view_mode': 'form,tree',
            'type': 'ir.actions.act_window',
            'nodestroy': False,  # close the pop-up wizard after action
            'target': 'current',
            'context': action_ctx,
        }
