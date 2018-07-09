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
import re

logger = logging.getLogger(__name__)


class TestPartnerCommunicationRevision(TransactionCase):

    def setUp(self):
        super(TestPartnerCommunicationRevision, self).setUp()
        self.env['res.lang'].load_lang('de_DE')
        self.test_communication = self.env['partner.communication.config'] \
            .browse(self.ref('partner_communication.test_communication'))

    def test_config_state(self):
        """ The config state should only be active if all its revisions are """
        self.assertEqual(self.test_communication.state, "active")

        de_revision = self.env['partner.communication.revision'].create({
            'lang': 'de_DE',
            'config_id': self.test_communication.id,
            'state': 'pending'
        })
        self.test_communication.revision_ids += de_revision

        self.assertEqual(self.test_communication.state, "pending")

    def test_install_revision(self):
        """ Should not fail if applied once again"""
        self.env['partner.communication.revision.install'].install()

    def test_creating_keyword(self):
        revision = self.test_communication.revision_ids[0]
        keyword = self.env['partner.communication.keyword'].create({
            'revision_id': revision.id,
            'type': 'if',
            'raw_code': """% if max_per_day() >= 3:
                    <p>test</p>
                % endif"""
        })

        self.assertEqual(keyword.short_code, 'max_per_day')
        self.assertEqual(keyword.color, 'darkblue')
        self.assertEqual(keyword.index, 1)
        html = '<span id="1-max_per_day" style="color: darkblue;">False</span>'
        self.assertEqual(keyword.replacement, html)

    def test_simplifying_revision(self):
        communication = self._load_communication_config(
            'partner_communication_revision.test_communication2')
        revision = communication.revision_ids[0]

        revision.reload_text()
        simplified_text = revision.simplified_text

        expected = """<div><spanid="1-var-invoice_lines"></span></div><div>
        <spanid="1-salutation"style="color:white;background-color:darkblue;">
        [salutation]</span>,<br><br>WethankyouforthedonationofCHF
        <spanid="2-donations"style="color:white;background-color:darkred;">
        [donations]</span>.-<spanid="1-donations"style="color:darkblue;">
        youmadefor<spanid="3-donations"style="color:white;
        background-color:darkgreen;">[donations]</span>.%elseyoumade.</span>
        Weappreciateyourgenerosity.<br><br>Yourssincerely</div>"""

        obtained_normalized = re.sub('\s+', '', revision.simplified_text)
        expected_normalized = re.sub('\s+', '', expected)
        self.assertEqual(obtained_normalized, expected_normalized)

    def _load_communication_config(self, ref):
        return self.env['partner.communication.config'] \
            .browse(self.ref(ref))
