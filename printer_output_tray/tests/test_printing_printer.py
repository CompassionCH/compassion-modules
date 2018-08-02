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
import types
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

    def test_prepare_update_from_cups(self):
        self._mock_cups_options_to_always_return_an_empty_list(self.printer)
        cups_printer = {'printer-info': ''}

        vals = self.printer._prepare_update_from_cups({}, cups_printer)

        # The only bin should be listed for deletion
        self.assertEqual(len(vals['bin_ids']), 1)
        [(operation, _)] = vals['bin_ids']
        self.assertEqual(operation, 2)

    def _mock_cups_options_to_always_return_an_empty_list(self, printer):
        def mock_get_values_for_option(*args):
            class DictWrapper(dict):
                __getattr__ = dict.__getitem__
                __setattr__ = dict.__setitem__
            return DictWrapper({
                'choices': []
            })
        printer._get_values_for_option = \
            types.MethodType(mock_get_values_for_option, self.printer)
