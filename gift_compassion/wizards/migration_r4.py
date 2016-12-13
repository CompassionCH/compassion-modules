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
from openerp import models, api


logger = logging.getLogger(__name__)


class MigrationR4(models.TransientModel):
    """ Perform migrations at module installation
    """
    _inherit = 'migration.r4'

    @api.model
    def install_gifts(self):
        # CreateGift
        messages = self._get_messages('CreateGift')
        self._create_gifts(messages)

        # Remove backup column for old messages
        self.env.cr.execute(
            "ALTER TABLE gmc_message_pool DROP COLUMN old_action;"
        )

        return True

    def _create_gifts(self, messages):
        """
        Migrate the old CreateGift messages
        """
        logger.info("MIGRATION 8.0.3 ----> CreateGift")
        invl_obj = self.env['account.invoice.line']
        gift_obj = self.env['sponsorship.gift']
        action = self.env.ref('gift_compassion.create_gift')
        for message in messages:
            invl = invl_obj.browse(message.object_id)
            if not invl or not invl.contract_id:
                message.action_id = action.id
                continue
            sponsorship = invl.contract_id
            product_name = invl.product_id.name
            gift_type = 'Beneficiary Gift'
            attribution = 'Sponsorship'
            sponsorship_gift_type = ''
            if product_name == 'Birthday Gift':
                sponsorship_gift_type = 'Birthday'
            elif product_name == 'General Gift':
                sponsorship_gift_type = 'General'
            elif product_name == 'Graduation Gift':
                sponsorship_gift_type = 'Graduation/Final'
            elif product_name == 'Family Gift':
                gift_type = 'Family Gift'
                attribution = 'Sponsored Child Family'
            elif product_name == 'Project Gift':
                gift_type = 'Project Gift'
                attribution = 'Center Based Programming'

            state = 'draft'
            if message.state == 'pending':
                state = 'open'
            gift_vals = {
                'sponsorship_id': sponsorship.id,
                'invoice_line_ids': [(4, invl.id)],
                'message_id': message.id,
                'instructions': invl.name.replace('[', '(').replace(']', ')'),
                'gift_type': gift_type,
                'attribution': attribution,
                'sponsorship_gift_type': sponsorship_gift_type,
                'state': state,
            }
            gift = gift_obj.create(gift_vals)
            message_vals = {
                'object_id': gift.id,
                'action_id': action.id
            }
            message.write(message_vals)

        # Messages were sent to GMC, only money has to be sent.
        self.env.cr.execute(
            "UPDATE gmc_message_pool SET state='success'"
            "WHERE state = 'fondue'"
        )
        self.env.invalidate_all()
