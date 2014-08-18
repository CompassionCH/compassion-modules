# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time
from lxml import etree

from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    _columns = {
        'bank_statement_label':fields.char('Bank Statement Label', size=100, help="enter the various label found on your bank statement separated by a ; If one of this label is include in the bank statement line the partner will be automatically filled"),
            }
res_partner()
