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
import mock
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
        self.bin_option = self.env['printer.option'].create({
            'option_key': 'OutputBin',
            'option_value': 'bin1',
            'printer_id': self.printer.id,
        })

    def test_print_options__copies_options_from_report(self):
        mock_report = mock.Mock()
        mock_report.printer_options = [self.bin_option]

        options = self.printer \
            .print_options(report=mock_report)

        self.assertEqual(options['OutputBin'], 'bin1')

    def test_print_options__without_option(self):
        mock_report = mock.Mock()
        mock_report.printer_options = []

        options = self.printer \
            .print_options(report=mock_report)

        self.assertEqual(options, {})

    def test_prepare_update_from_cups(self):
        self._mock_cups_options(self.printer,
                                [{'choice': 'bin1'},
                                 {'choice': 'bin2'}])
        cups_printer = {'printer-info': ''}

        vals = self.printer._prepare_update_from_cups({}, cups_printer)

        # OutputBin:bin1 was already inserted
        self.assertEqual(len(vals['printer_option_ids']), 5)
        self.assertIn((0, 0,
                       {'option_key': 'OutputBin', 'option_value': 'bin2'}),
                      vals['printer_option_ids'])
        self.assertNotIn((0, 0,
                          {'option_key': 'OutputBin', 'option_value': 'bin1'}),
                         vals['printer_option_ids'])

    def _mock_cups_options(self, printer,
                           choices):
        def mock_get_values_for_option(*args):
            class DictWrapper(dict):
                __getattr__ = dict.__getitem__
                __setattr__ = dict.__setitem__

            return DictWrapper({
                'choices': choices
            })

        printer._get_values_for_option = \
            types.MethodType(mock_get_values_for_option, self.printer)
