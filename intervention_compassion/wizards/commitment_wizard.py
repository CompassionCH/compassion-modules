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
from odoo import models, fields, api
from odoo.exceptions import UserError


class HoldWizard(models.TransientModel):
    _name = 'compassion.intervention.commitment.wizard'
    _description = 'Intervention Commitment Wizard'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    intervention_id = fields.Many2one(
        'compassion.intervention', 'Intervention'
    )
    additional_fund_amount = fields.Float(
        related='intervention_id.requested_additional_funding'
    )
    additional_info = fields.Text(
        related='intervention_id.additional_marketing_information'
    )
    hold_id = fields.Char(related='intervention_id.hold_id')
    usd = fields.Many2one(related='intervention_id.currency_usd')
    commitment_amount = fields.Float(required=True, readonly=True)
    commit_to_additional_fund = fields.Boolean()

    @api.multi
    def commitment_created(self, intervention_vals):
        """ Called when commitment is created """
        self.intervention_id.write({
            'state': 'committed',
            'commitment_amount': self.commitment_amount,
            'hold_id': False
        })

    @api.multi
    def send_commitment(self):
        self.ensure_one()
        create_commitment = self.env.ref(
            'intervention_compassion.intervention_create_commitment_action')
        message = self.env['gmc.message.pool'].with_context(
            async_mode=False).create({
                'action_id': create_commitment.id,
                'object_id': self.id,
            })
        if message.state == 'failure':
            raise UserError(message.failure_reason)
        return True
