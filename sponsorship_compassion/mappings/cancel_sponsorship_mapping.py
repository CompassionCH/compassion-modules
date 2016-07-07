# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Michael Sandoz <michaelsandoz87@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from base_sponsorship_mapping import BaseSponsorshipMapping
from datetime import datetime


class CancelSponsorship(BaseSponsorshipMapping):
    """ This class contains the mapping between Odoo fields and GMC field names
    for delete a sponsorship.
    """
    MAPPING_NAME = 'CancelSponsorship'

    FIELDS_TO_SUBMIT = {
        "FinalCommitmentOfLine": None,
        "Beneficiary_GlobalID": None,
        "HoldExpirationDate": None,
        "Commitment_ID": None,
        "SponsorSupporterGlobalID": None,
        "GlobalPartner_ID": None,
        "HoldType": None,
        "DelinkType": None,
        "PrimaryHoldOwner": None
    }

    def __init__(self, env):
        super(CancelSponsorship, self).__init__(env)
        self.CONNECT_MAPPING['HoldID'] = 'hold_id'

    def _process_connect_data(self, connect_data):
        # Set end date to correct format for Connect

        end_date_str = connect_data['HoldExpirationDate']
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
        connect_data['HoldExpirationDate'] = end_date.strftime(
            "%Y-%m-%dT%H:%M:%SZ")

        child_global_id = connect_data['Beneficiary_GlobalID']
        child = self.env['compassion.child'].search(
            [('global_id', '=', child_global_id)], limit=1)

        # save future hold with expiration date
        if child.active:
            hold_vals = {
                'name': "",
                'child_id': child.id,
                'type': 'Consignment Hold',
                'expiration_date': end_date,
                'primary_owner': 'Rose-Marie Reber',
                'secondary_owner': 'Carole Rochat',
                'no_money_yield_rate': '1.1',
                'yield_rate': '1.1',
                'channel': '',
                'source_code': '',
            }
            hold = self.env['compassion.hold'].create(hold_vals)
            child.write({'hold_id': hold.id})

    def _process_odoo_data(self, connect_data):
        if 'child_id' in connect_data:
            child = self.env['compassion.child'].browse(
                connect_data['child_id'])
            if child.active:
                # Update new hold
                child.hold_id.write({'hold_id': connect_data['hold_id']})

            # Don't write hold_id in contract
            del connect_data['hold_id']
