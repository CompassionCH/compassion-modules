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

from openerp.addons.base_status.base_stage import base_stage
import crm
from datetime import datetime
from operator import itemgetter
from openerp.osv import fields, osv, orm
import time
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import html2plaintext

from base.res.res_partner import format_address

class crm_lead(osv.osv):
    """ CRM Lead Case """
    _inherit = "crm.lead"
    _name = "crm.lead"
    
    _columns = {
            'planned_sponsorship': fields.integer('Expected new sponsorship', track_visibility='always'),

    }

crm_lead()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
