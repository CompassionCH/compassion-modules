
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, api, fields, _


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
        state = 'cancel'
        communication = self.env['partner.communication.job'].browse(
            self.env.context.get('default_communication_id'))
        communication.message_post(
            subject=_('Phone attempt'),
            body=self.comments or _('Partner did not answer')
        )
        return self.call_log(state)

    @api.multi
    def call_success(self):
        state = 'done'
        return self.call_log(state)

    @api.multi
    def call_log(self, state):
        """ Prepare crm.phonecall creation. """
        action_ctx = self.env.context.copy()
        action_ctx.update({
            'default_state': state,
            'default_description': self.comments,
            'default_name': self.env.context.get('call_name'),
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
            'view_mode': 'form,tree,calendar',
            'type': 'ir.actions.act_window',
            'nodestroy': False,  # close the pop-up wizard after action
            'target': 'new',
            'context': action_ctx,
        }
