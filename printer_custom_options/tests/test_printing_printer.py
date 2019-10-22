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
        self.bin_option = self.env['printer.option.choice'].create({
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

    def test_prepare_update_from_cups__load_options(self):
        self._mock_cups_options(self.printer, [])
        cups_printer = {'printer-info': ''}

        self.printer._prepare_update_from_cups({}, cups_printer)

        self.assertEqual(len(self.printer.printer_options), 1)
        self.assertEqual(self.printer.printer_options[0].option_key,
                         'OutputBin')

    def test_prepare_update_from_cups(self):
        self._mock_cups_options(self.printer,
                                [{'choice': 'bin1'},
                                 {'choice': 'bin2'}])
        cups_printer = {'printer-info': ''}

        vals = self.printer._prepare_update_from_cups({}, cups_printer)

        # OutputBin:bin1 was already inserted
        self.assertEqual(len(vals['printer_option_choices']), 1)
        self.assertIn((0, 0,
                       {'option_key': 'OutputBin', 'option_value': 'bin2'}),
                      vals['printer_option_choices'])
        self.assertNotIn((0, 0,
                          {'option_key': 'OutputBin', 'option_value': 'bin1'}),
                         vals['printer_option_choices'])

    def _mock_cups_options(self, printer,
                           choices):
        def mock__get_cups_ppd(*args):
            mock_ppd = mock.Mock()
            # Mock optionGroups
            mock_option_group = mock.Mock()
            mock_option = mock.Mock()
            mock_option.keyword = 'OutputBin'
            mock_option.choices = choices
            mock_option_group.options = [mock_option]
            mock_ppd.optionGroups = [mock_option_group]
            # Mock findOption
            mock_ppd.findOption = lambda x: mock_option
            return 'pdd_path', mock_ppd

        printer._get_cups_ppd = \
            types.MethodType(mock__get_cups_ppd, self.printer)
