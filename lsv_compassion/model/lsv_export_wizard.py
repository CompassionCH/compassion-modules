# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <cyril.sester@outlook.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
from export_tools import export_tools
from openerp.osv import orm
from openerp.tools.translate import _

logger = logging.getLogger(__name__)


class lsv_export_wizard(orm.TransientModel):
    _inherit = 'lsv.export.wizard'

    def _get_communications(self, cr, uid, line, context=None):
        return export_tools.get_communications(self, cr, uid, line, context)

    def _customize_lines(self, cr, uid, lsv_lines, properties, context=None):
        ''' We try to group lines if possible. '''
        # See get_communication for languages explanations
        if not context:
            context = {}
        lang_backup = context.get('lang', '')

        grouped_lines = []
        deb_iban = lsv_lines[0][1][237:271]
        treatment_date = lsv_lines[0][1][5:13]
        ref = lsv_lines[0][1][552:579]
        new_line = lsv_lines[0][1]
        seq_nb = 1
        nb_grouped = 1

        for tuple in lsv_lines[1:-1]:
            pay_line = tuple[0]
            line = tuple[1]
            if line[237:271] != deb_iban or line[5:13] != treatment_date or \
                    line[552:579] != ref:
                grouped_lines.append(new_line)
                seq_nb += 1
                deb_iban = line[237:271]
                treatment_date = line[237:271]
                ref = line[552:579]
                new_line = line
                new_line = new_line[:36] + str(seq_nb).zfill(7) + \
                    new_line[43:]
                nb_grouped = 1
            else:
                # Set partner language for communication generation
                context['lang'] = pay_line.partner_id.lang
                nb_grouped += 1
                new_amount = float(
                    new_line[51:63].replace(',', '.')) + \
                    float(line[51:63].replace(',', '.'))
                new_amount = self._format_number(new_amount, 12)
                new_com = self._complete_line(
                    _('debit for %d period(s)') % nb_grouped, 140)
                new_line = new_line[:51] + new_amount + \
                    new_line[63:411] + new_com + new_line[551:]

        grouped_lines.append(new_line)
        seq_nb += 1
        grouped_lines.append(
            lsv_lines[-1][1][:17] + str(seq_nb).zfill(7) +
            lsv_lines[-1][1][24:])
        properties['seq_nb'] = seq_nb

        context['lang'] = lang_backup
        return grouped_lines
