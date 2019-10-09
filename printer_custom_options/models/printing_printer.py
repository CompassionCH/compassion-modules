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

    printer_option_ids = fields.One2many(comodel_name='printer.option',
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

        current_option_keys = self.printer_option_ids.mapped('composite_key')

        new_option_values = []
        # TODO: We could make this list dynamic.
        for option_key in ['OutputBin', 'Fold', 'MediaType']:
            new_options = self.discover_printer_options(cups_connection,
                                                        cups_printer,
                                                        current_option_keys,
                                                        option_key)
            new_option_values.extend(new_options)
        vals['printer_option_ids'] = new_option_values
        return vals

    def discover_printer_options(self, cups_connection, cups_printer,
                                 current_option_keys, option_key):
        """ Returns all new values for one printer option category. Most
        probably it will insert all option values the first time we sync with
        CUPS and then return an empty list."""
        option = self._get_values_for_option(
            cups_connection, cups_printer, option_key
        )
        if not option:
            return []

        printer_option_values = {entry['choice'] for entry in option.choices}
        option_model = self.env['printer.option']

        # Insertion tuples
        return [
            (0, 0,
             {'option_value': option_value, 'option_key': option_key})
            for option_value in printer_option_values
            if option_model.build_composite_key(option_key, option_value)
            not in current_option_keys
        ]

    @api.multi
    def print_options(self, report=None, format=None, copies=1):
        # Use lpoptions to have an exhaustive list of the supported options
        options = super(PrintingPrinter, self).print_options(report, format)

        if report is not None:
            for printer_option in report.printer_options:
                options[
                    printer_option.option_key] = printer_option.option_value
        return options
