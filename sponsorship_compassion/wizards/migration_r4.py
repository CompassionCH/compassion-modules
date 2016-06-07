# -*- encoding: utf-8 -*-
#
#    Copyright (C)  Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    The licence is in the file __openerp__.py
#

import logging
from openerp import models, api


logger = logging.getLogger(__name__)


class MigrationR4(models.TransientModel):
    """ Perform migrations after upgrading the module
    """
    _name = 'migration.r4'

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
        messages.unlink()

        # CancelCommitment
        messages = self._get_messages('CancelCommitment')
        self._cancel_commitments(messages)
        messages.unlink()

        # UpsertConstituent
        messages = self._get_messages('UpsertConstituent')
        self._upsert_constituents(messages)

        # CreateGift
        messages = self._get_messages('CreateGift')
        self._create_gifts(messages)
        messages.unlink()

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
