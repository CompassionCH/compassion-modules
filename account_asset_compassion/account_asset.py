# -*- encoding: utf-8 -*-
##############################################################################
#
#    Compassion asset customizing module for openERP
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
from calendar import monthrange

from openerp.osv import orm


class account_asset_asset(orm.Model):
    _inherit = 'account.asset.asset'

    def _compute_board_amount(self, cr, uid, asset, i, residual_amount,
                              amount_to_depr, undone_dotation_number,
                              posted_depreciation_line_ids, total_days,
                              depreciation_date, context=None):
        #by default amount = 0
        amount = 0
        if i == undone_dotation_number:
            amount = residual_amount
        else:
            if asset.method == 'linear':
                amount = amount_to_depr / (undone_dotation_number - 
                                           len(posted_depreciation_line_ids))
                if asset.prorata:
                    amount = amount_to_depr / asset.method_number
                    days_in_month = monthrange(depreciation_date.year,
                                               depreciation_date.month)[1]
                    day_of_month = float(depreciation_date.strftime('%d'))
                    if i == 1:
                        month_part = days_in_month - (day_of_month - 1)
                        amount = amount / days_in_month * month_part
                    elif i == undone_dotation_number:
                        month_part = day_of_month - 1
                        amount = amount / days_in_month * month_part
            elif asset.method == 'degressive':
                amount = residual_amount * asset.method_progress_factor
                if asset.prorata:
                    days_in_month = monthrange(depreciation_date.year,
                                               depreciation_date.month)[1]
                    day_of_month = float(depreciation_date.strftime('%d'))
                    if i == 1:
                        month_part = days_in_month - (day_of_month - 1)
                        amount = amount / total_days * month_part
                    elif i == undone_dotation_number:
                        month_part = day_of_month - 1
                        amount = amount / total_days * month_part
        return amount
