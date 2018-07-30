# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests.common import TransactionCase


class TestPrintingPrinter(TransactionCase):

    def setUp(self):
        super(TestPrintingPrinter, self).setUp()
        self.server = self.env['printing.server'].create({})
        self.printer = self.env['printing.printer'].create({
            'name': 'Printer',
            'server_id': self.server.id,
            'system_name': 'Sys Name',
            'default': True,
            'status': 'unknown',
            'status_message': 'Msg',
            'model': 'res.users',
            'location': 'Location',
            'uri': 'URI',
        })
        bin = self.env['printing.bin'].create({
            'name': 'Bin1',
            'system_name': 'bin1',
            'printer_id': self.printer.id,
        })
        bin.lang_forwarded_ids += self.env['res.lang'] \
            .search([('code', '=', 'en_US')])

    def test_print_options__with_unknown_lang(self):
        options = self.printer \
            .with_context(lang='de') \
            .print_options(report={})
        self.assertEqual(options['OutputBin'], 'Default')

    def test_print_options__with_language_matching_a_bin(self):
        options = self.printer \
            .with_context(lang='en_US') \
            .print_options(report={})
        self.assertEqual(options['OutputBin'], 'bin1')
