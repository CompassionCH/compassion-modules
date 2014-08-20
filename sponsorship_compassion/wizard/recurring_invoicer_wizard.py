# -*- encoding: utf-8 -*-
##############################################################################
#
#    Recurring contract module for openERP
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    @author: Cyril Sester <csester@compassion.ch>
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

from openerp.osv import orm, fields
from openerp.tools.translate import _
import logging

logger = logging.getLogger(__name__)

class recurring_invoicer_wizard(orm.TransientModel):
    _inherit = 'recurring.invoicer.wizard'

    def generate_from_cron(self, cr, uid, group=False, context=None):
        ret_dict = self.generate(cr, uid, [], context=context, group=group)
        recurring_invoicer_obj = self.pool.get('recurring.invoicer')
        recurring_invoicer_obj.validate_invoices(cr, uid, [ret_dict['res_id']]) 