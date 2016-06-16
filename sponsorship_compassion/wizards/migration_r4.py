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
    """ Perform migrations after upgrading the module
    """
    _inherit = 'migration.r4'

    @api.model
    def perform_migration(self):
        # Only execute migration for 8.0.2 -> 8.0.3.0
        sponsorship_compassion_module = self.env['ir.module.module'].search([
            ('name', '=', 'sponsorship_compassion')
        ])
        if sponsorship_compassion_module.latest_version == '8.0.2':
            self._perform_migration()
        return True

    def _perform_migration(self):
        """
        Migrate sponsorship related messages
        """
        # CreateCommitment
        messages = self._get_messages('CreateCommitment')
        self._create_commitments(messages)

        # CancelCommitment
        messages = self._get_messages('CancelCommitment')
        self._cancel_commitments(messages)

        # UpsertConstituent
        messages = self._get_messages('UpsertConstituent')
        self._upsert_constituents(messages)

        # CreateGift
        messages = self._get_messages('CreateGift')
        self._create_gifts(messages)

        # Remove backup column for old messages
        self.env.cr.execute(
            "ALTER TABLE gmc_message_pool DROP COLUMN old_action;"
        )

        # Restore transfer country for sponsorships terminated
        self._restore_transferred_sponsorships()

        # Rename sponsorships with new child codes
        self.env['recurring.contract'].search([])._set_name()

    def _get_messages(self, type):
        """
        Returns the old messages
        :param type: Name of the action of the old message
        :return: Recordset of gmc.message.pool objects
        """
        query = "SELECT id from gmc_message_pool where old_action='{}'"
        self.env.cr.execute(query.format(type))
        message_ids = [r[0] for r in self.env.cr.fetchall()]
        return self.env['gmc.message.pool'].browse(message_ids)

    def _create_commitments(self, messages):
        """
        Migrate the old CreateCommitment messages
        """
        logger.info("MIGRATION 8.0.3 ----> CreateCommitment")
        messages.write({'action_id': self.env.ref(
            'sponsorship_compassion.create_sponsorship').id})

    def _cancel_commitments(self, messages):
        """
        Migrate the old CancelCommitment messages
        """
        logger.info("MIGRATION 8.0.3 ----> CancelCommitment")
        messages.write({'action_id': self.env.ref(
            'sponsorship_compassion.cancel_sponsorship').id})

    def _upsert_constituents(self, messages):
        """
        Migrate the old UpsertConstituent messages
        """
        logger.info("MIGRATION 8.0.3 ----> UpsertConstituent")
        messages.write({'action_id': self.env.ref(
            'sponsorship_compassion.upsert_partner').id})

    def _create_gifts(self, messages):
        """
        Migrate the old CreateGift messages
        """
        logger.info("MIGRATION 8.0.3 ----> CreateGift")
        invl_obj = self.env['account.invoice.line']
        gift_obj = self.env['sponsorship.gift']
        action = self.env.ref('sponsorship_compassion.create_gift')
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

            gift_vals = {
                'sponsorship_id': sponsorship.id,
                'invoice_line_ids': [(4, invl.id)],
                'instructions': invl.name,
                'gift_type': gift_type,
                'attribution': attribution,
                'sponsorship_gift_type': sponsorship_gift_type,
                'state': 'fund_due' if message.state == 'fondue' else 'open'
            }
            gift = gift_obj.create(gift_vals)
            message_vals = {
                'object_id': gift.id,
                'action_id': action.id
            }
            if message.state == 'fondue':
                # Message was sent to GMC, only money has to be sent.
                self.env.cr.execute(
                    "UPDATE gmc_message_pool SET state='success'"
                    "WHERE id = " + str(message.id)
                )
            message.write(message_vals)
        self.env.invalidate_all()

    def _restore_transferred_sponsorships(self):
        """
        Put the global partner to which the sponsorship was transferred.
        """
        logger.info("MIGRATION 8.0.3 ----> Transfer Country of Sponsorships.")
        sponsorships = self.env['recurring.contract'].search([
            ('state', '=', 'terminated'),
            ('type', 'like', 'S'),
            ('end_reason', '=', '4')    # (=Sponsor moved)
        ])
        for sponsorship in sponsorships:
            child_id = sponsorship.child_id.id
            self.env.cr.execute(
                "SELECT transfer_country_backup FROM compassion_child "
                "WHERE id = " + str(child_id) + ";"
            )
            country_id = self.env.cr.fetchone()[0]
            if country_id:
                global_partner = self.env['compassion.global.partner'].search(
                    [('country_id', '=', country_id)]
                )
                sponsorship.transfer_partner_id = global_partner
        self.env.cr.execute(
            "ALTER TABLE compassion_child DROP COLUMN transfer_country_backup;"
        )
