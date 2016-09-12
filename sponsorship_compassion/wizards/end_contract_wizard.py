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

from openerp.addons.child_compassion.models.compassion_hold import \
    HoldType


class EndContractWizard(models.TransientModel):
    _inherit = 'end.contract.wizard'

    child_id = fields.Many2one(related='contract_id.child_id')
    do_transfer = fields.Boolean('I want to transfer the child')
    transfer_country_id = fields.Many2one(
        'compassion.global.partner', 'Country')
    keep_child_on_hold = fields.Boolean(default=True)
    hold_expiration_date = fields.Datetime(
        default=lambda s: s.env[
            'compassion.hold'].get_default_hold_expiration(
            HoldType.SPONSOR_CANCEL_HOLD),
        required=True)

    @api.multi
    def end_contract(self):
        self.ensure_one()
        child = self.child_id

        if self.keep_child_on_hold:
            if child.hold_id and not self.contract_id.global_id:
                # Update the hold
                child.hold_id.write({
                    'type': HoldType.SPONSOR_CANCEL_HOLD.value,
                    'expiration_date': self.hold_expiration_date
                })
            else:
                # Since the child is sponsored, create a reservation
                # for when we send the CancelCommitment, the child will
                # be put back on hold for us.
                self.env['icp.reservation'].create({
                    'name': 'Sponsor Cancel Reservation',
                    'reservation_expiration_date': self.hold_expiration_date,
                    'expiration_date': self.hold_expiration_date,
                    'hold_expiration_date': self.hold_expiration_date,
                    'number_of_beneficiaries': '1',
                    'icp_id': child.project_id.id,
                    'child_id': child.id,
                    'source_code': 'sponsor_cancel',
                })
        else:
            # Remove the hold on the child
            if child.hold_id:
                child.hold_id.release_hold()

        child.signal_workflow('release')

        return super(EndContractWizard, self).end_contract()
