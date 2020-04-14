# -*- coding: utf-8 -*-

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Custom printer options do not have the input/output choices anymore
    # They are filtered and should be moved to the respective fields

    reports = env['ir.actions.report.xml'].search([])
    for report in reports:
        remove = []
        for opt in report.printer_options:
            if opt.option_key == 'InputSlot':
                report.printer_input_tray_id = env['printing.tray.input'].search(
                    [('system_name', 'like', opt.option_value)], limit=1)
                remove.append((2, opt.id))
            elif opt.option_key == 'OutputBin':
                report.printer_output_tray_id = env['printing.tray.output'].search(
                    [('system_name', 'like', opt.option_value)], limit=1)
                remove.append((2, opt.id))
        if remove:
            report.write({'printer_options': remove})

    printers = env['printing.printer'].search([])
    for printer in printers:
        remove = []
        for opt in printer.printer_option_choices:
            if opt.option_key in ['InputSlot', 'OutputSlot']:
                remove.append((2, opt.id))
        if remove:
            printer.write({'printer_options_choices': remove})
