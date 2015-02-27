# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields


class asset_category(orm.Model):
    _inherit = 'account.asset.category'

    _columns = {
        'analytics_id': fields.many2one('account.analytic.plan.instance',
                                        'Analytic Distribution'),
    }


class account_asset_depreciation_line(orm.Model):
    _inherit = 'account.asset.depreciation.line'

    def _setup_move_line_data(self, depreciation_line, depreciation_date,
                              period_ids, account_id, type, move_id, context):
        """ Add analytic distribution to move_line """
        move_line_data = super(account_asset_depreciation_line,
                               self)._setup_move_line_data(
            depreciation_line, depreciation_date, period_ids, account_id,
            type, move_id, context)
        if type == 'expense':
            move_line_data.update({
                'analytics_id':
                depreciation_line.asset_id.category_id.analytics_id.id})
        return move_line_data


class asset(orm.Model):
    _inherit = 'account.asset.asset'

    def close_old_asset(self, cr, uid, ids, context=None):
        for asset in self.browse(cr, uid, ids, context):
            asset.write({
                # Triggers the computation of residual value
                'purchase_value': asset.purchase_value,
                'state': 'close'
                }, context=dict(context, asset_validate_from_write=True))

        return True
