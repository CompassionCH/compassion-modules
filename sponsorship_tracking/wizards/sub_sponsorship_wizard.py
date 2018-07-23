# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _

from odoo.addons.child_compassion.models.compassion_hold import HoldType

from datetime import datetime
from dateutil.relativedelta import relativedelta


class SubSponsorshipWizard(models.TransientModel):
    _name = "sds.subsponsorship.wizard"
    _description = "Sub Sponsorship Wizard"

    state = fields.Selection([
        ('sub', 'sub'),
        ('no_sub', 'no_sub')])
    channel = fields.Selection([
        ('childpool', 'Global Childpool'),
        ('direct', 'Direct')
    ])
    child_id = fields.Many2one(
        'compassion.child', 'Child', domain=[('state', 'in', ['N', 'I'])])
    no_sub_default_reasons = fields.Selection(
        '_get_no_sub_reasons', 'No sub reason')
    no_sub_reason = fields.Char('No sub reason')

    def _get_no_sub_reasons(self):
        return [
            ('other_sponsorship', _('Sponsors other children')),
            ('financial', _('Financial reasons')),
            ('old', _('Is too old to sponsor another child')),
            ('other_support', _('Wants to support with fund donations')),
            ('other_organization', _('Supports another organization')),
            ('not_now', _("Doesn't want to take another child right now")),
            ('not_given', _('Not given')),
            ('other', _('Other...'))
        ]

    @api.multi
    def create_subsponsorship(self):
        """ Creates a subsponsorship. """
        self.ensure_one()

        sponsorship_id = self.env.context.get('active_id')
        contract_obj = self.env['recurring.contract'].with_context(
            allow_rewind=True)
        contract = contract_obj.browse(sponsorship_id)
        contract.sds_uid = self.env.user
        sub_contract = contract.copy({
            'parent_id': sponsorship_id,
            'channel': 'sub',
            'child_id': self.child_id.id,
            'user_id': False,
            'sds_uid': self.env.uid,
            'medium_id': self.env.ref('utm.utm_medium_direct').id,
            'source_id': self.env.ref('contract_compassion.utm_source_sub').id,
            'campaign_id': self.env.ref(
                'contract_compassion.utm_campaign_sub').id
        })
        today = datetime.today()
        next_invoice_date = fields.Date.from_string(
            contract.next_invoice_date).replace(month=today.month,
                                                year=today.year)
        if contract.last_paid_invoice_date:
            sub_invoice_date = fields.Date.from_string(
                contract.last_paid_invoice_date) + relativedelta(months=1)
            next_invoice_date = max(next_invoice_date, sub_invoice_date)

        if self.child_id:
            sub_contract.next_invoice_date = next_invoice_date
            return {
                'name': sub_contract.name,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'recurring.contract',
                'res_id': sub_contract.id,
                'target': 'current',
                'context': self.with_context({
                    'default_type': 'S',
                }).env.context
            }
        else:
            return {
                'name': _('Global Childpool'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'compassion.childpool.search',
                'target': 'current',
                'context': self.with_context({
                    'default_take': 1,
                    'contract_id': sub_contract.id,
                    'next_invoice_date': fields.Date.to_string(
                        next_invoice_date),
                    'default_type': HoldType.SUB_CHILD_HOLD.value,
                    'default_return_action': 'sub',
                    'default_source_code': 'sub_proposal',
                }).env.context
            }

    @api.multi
    def no_sub(self):
        """ No SUB for the sponsorship. """
        self.ensure_one()
        sponsorship_id = self.env.context.get('active_id')
        contract = self.env['recurring.contract'].browse(sponsorship_id)
        default_reason = self.no_sub_default_reasons
        if default_reason == 'other':
            reason = self.no_sub_reason
        else:
            reason = dict(self._get_no_sub_reasons()).get(default_reason)
        contract.write({
            'no_sub_reason': reason,
            'sds_uid': self.env.uid,
            'sds_state': 'no_sub',
            'color': 1
        })
        contract.partner_id.message_post(
            subject=_('{} - No SUB'.format(contract.child_code)),
            body=_("The sponsor doesn't want a new child.")
        )
        return True
