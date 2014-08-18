# -*- coding: utf-8 -*-
##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
#    @author: Cyril Sester <cyril.sester@outlook.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
from export_tools import export_tools
from openerp.osv import orm, fields
from openerp.tools.translate import _

logger = logging.getLogger(__name__)

class post_dd_export_wizard(orm.TransientModel):
    _inherit = 'post.dd.export.wizard'
    
    def _get_communications(self, cr, uid, line, context=None):
        return export_tools.get_communications(self, cr, uid, line, context)
        
    def _customize_records(self, cr, uid, records, properties, context=None):
        ''' We try to group lines if possible. '''
        # See get_communication for languages explanations
        if not context:
            context = {}
        lang_backup = context.get('lang', '')
        
        grouped_lines = [records[0][1]]
        deb_account = records[1][1][72:81]
        ref = records[1][1][87:114]
        new_line = records[1][1]
        trans_id = 1
        nb_grouped = 1
        nb_transactions = 0
        
        for tuple in records[2:]:
            pay_line = tuple[0]
            line = tuple[1]
            if not pay_line: # It's a header or total records
                if line[35:37] == '97': #It's a total. We update trans_id and nb_transactions
                    line = line[:37] + str(trans_id+1).zfill(6) + line[43:53] + \
                           str(trans_id).zfill(6) + line[59:]
                    nb_transactions += trans_id
                    trans_id = 0
                grouped_lines.append(new_line)
                new_line = line
                deb_account = ''
                ref = ''
                continue
            if line[72:81] != deb_account or line[87:114] != ref:
                grouped_lines.append(new_line)
                trans_id += 1
                deb_account = line[72:81]
                ref = line[87:114]
                new_line = line
                new_line = new_line[:37] + str(trans_id).zfill(6) + new_line[43:]
                nb_grouped = 1
            else:
                #Set partner language for communication generation
                context['lang'] = pay_line.partner_id.lang
                nb_grouped += 1
                new_amount = float(new_line[53:66])/100 + float(line[53:66])/100
                new_amount = self._format_number(new_amount, 13)
                new_com = self._complete_line(_('debit for %d period(s)') % nb_grouped, 140)
                new_line = new_line[:53] + new_amount + new_line[66:402] + new_com + new_line[542:]
                
        grouped_lines.append(new_line)
        properties['nb_transactions'] = nb_transactions
                
        context['lang'] = lang_backup
        return grouped_lines
        