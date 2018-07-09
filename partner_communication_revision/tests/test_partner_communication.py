# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#    The licence is in the file __manifest__.py
#
##############################################################################
from psycopg2 import IntegrityError
from odoo.tests.common import TransactionCase
import logging
logger = logging.getLogger(__name__)


class TestPartnerCommunicationRevision(TransactionCase):

    def setUp(self):
        super(TestPartnerCommunicationRevision, self).setUp()
        self.env['res.lang'].load_lang('de_DE')
        self.partner = self.env['res.partner'] \
            .browse(self.ref('base.res_partner_2'))
        self.test_communication = self.env['partner.communication.config'] \
            .browse(self.ref('partner_communication.test_communication'))

    def test_config_state(self):
        """ The config state should only be active if all its revisions are """
        self.assertEqual(self.test_communication.state, "active")

        gb_revision = self.env['partner.communication.revision'].create({
            'lang': 'de_DE',
            'config_id': self.test_communication.id,
            'state': 'pending'
        })
        self.test_communication.revision_ids += gb_revision

        self.assertEqual(self.test_communication.state, "pending")
