# -*- encoding: utf-8 -*-
##############################################################################
#
#    Compassion asset customizing module for openERP
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino, Cyril Sester
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
# from calendar import monthrange

from openerp.osv import orm, fields
import pdb


class asset_category(orm.Model):
    _inherit = 'account.asset.category'
    
    _columns = {
        'analytics_id': fields.many2one('account.analytic.plan.instance', 'Analytic Distribution'),
    }
    
    
class account_asset_depreciation_line(orm.Model):
    _inherit = 'account.asset.depreciation.line'
    
    def create_move(self, cr, uid, ids, context=None):
        """ Put the analytics_ids in context for retrieving it in create
        method of account_move_line."""
        if context is None:
            context = {}
        # Dict containing {asset_id : analytic_distribution_id}
        analytics_ids = {}
        for line in self.browse(cr, uid, ids, context):
            analytics_ids.update({line.asset_id.id: line.analytics_id.id})
        context['analytics_ids'] = analytics_ids
        
        return super(account_asset_depreciation_line, self).create_move(cr, uid, ids, context)
        

class account_move_line(orm.Model):
    _inherit = 'account.move.line'
    
    def create(self, cr, uid, vals, context=None, check=True):
        """ Retrieve the analytics ids from context, if defined,
        and create move line."""
        analytics_ids = context.get('analytics_ids')
        asset_id = vals.get('asset_id')
        if analytics_ids and asset_id:
            vals['analytics_id'] = analytics_ids[asset_id]

        return super(account_move_line, self).create(cr, uid, vals, context, check)
            

# class account_asset_asset(orm.Model):
    # _inherit = 'account.asset.asset'

    # def _compute_board_amount(self, cr, uid, asset, i, residual_amount,
                              # amount_to_depr, undone_dotation_number,
                              # posted_depreciation_line_ids, total_days,
                              # depreciation_date, context=None):
        # by default amount = 0
        # amount = 0
        # if i == undone_dotation_number:
            # amount = residual_amount
        # else:
            # if asset.method == 'linear':
                # amount = amount_to_depr / (undone_dotation_number - 
                                           # len(posted_depreciation_line_ids))
                # if asset.prorata:
                    # amount = amount_to_depr / asset.method_number
                    # days_in_month = monthrange(depreciation_date.year,
                                               # depreciation_date.month)[1]
                    # day_of_month = float(depreciation_date.strftime('%d'))
                    # if i == 1:
                        # month_part = days_in_month - (day_of_month - 1)
                        # amount = amount / days_in_month * month_part
                    # elif i == undone_dotation_number:
                        # month_part = day_of_month - 1
                        # amount = amount / days_in_month * month_part
            # elif asset.method == 'degressive':
                # amount = residual_amount * asset.method_progress_factor
                # if asset.prorata:
                    # days_in_month = monthrange(depreciation_date.year,
                                               # depreciation_date.month)[1]
                    # day_of_month = float(depreciation_date.strftime('%d'))
                    # if i == 1:
                        # month_part = days_in_month - (day_of_month - 1)
                        # amount = amount / total_days * month_part
                    # elif i == undone_dotation_number:
                        # month_part = day_of_month - 1
                        # amount = amount / total_days * month_part
        # return amount
