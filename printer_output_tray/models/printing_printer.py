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
import errno
import logging
import os

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    import cups
except ImportError:
    _logger.debug('Cannot `import cups`.')


class PrintingPrinter(models.Model):
    _inherit = 'printing.printer'

    bin_ids = fields.One2many(comodel_name='printing.bin',
                              inverse_name='printer_id',
                              string='Output Bins')

    def _get_values_for_option(self, cups_connection, cups_printer,
                               option_key):
        printer_uri = cups_printer['printer-uri-supported']
        printer_system_name = printer_uri[printer_uri.rfind('/') + 1:]
        ppd_info = cups_connection.getPPD3(printer_system_name)
        ppd_path = ppd_info[2]
        if not ppd_path:
            return False

        ppd = cups.PPD(ppd_path)
        option = ppd.findOption(option_key)
        try:
            os.unlink(ppd_path)
        except OSError as err:
            # ENOENT means No such file or directory
            # The file has already been deleted, we can continue the update
            if err.errno != errno.ENOENT:
                raise
        return option

    @api.multi
    def _prepare_update_from_cups(self, cups_connection, cups_printer):
        vals = super(PrintingPrinter, self)._prepare_update_from_cups(
            cups_connection, cups_printer)

        option = self._get_values_for_option(
            cups_connection, cups_printer, 'OutputBin'
        )

        if not option:
            return vals

        vals['bin_ids'] = []
        cups_bins = {
            entry['choice']: entry['text']
            for entry in option.choices
        }

        # Add new bins
        vals['bin_ids'].extend([
            (0, 0, {'name': text, 'system_name': choice})
            for choice, text in cups_bins.items()
            if choice not in self.bin_ids.mapped('system_name')
        ])

        # Remove deleted bins
        vals['bin_ids'].extend([
            (2, bin.id)
            for bin in self.bin_ids.filtered(
                lambda record: record.system_name not in cups_bins.keys())
        ])

        return vals

    @api.multi
    def print_options(self, report=None, format=None, copies=1):
        # Use lpoptions to have an exhaustive list of the supported options
        options = super(PrintingPrinter, self).print_options(report, format)

        if report is not None:
            print_lang = self.env.lang
            valid_bin_names = (bin.system_name for bin in self.bin_ids
                               if bin.forward_lang(print_lang))
            options['OutputBin'] = next(valid_bin_names, 'Default')
        return options
