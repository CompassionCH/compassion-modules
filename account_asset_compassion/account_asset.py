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
# from calendar import monthrange

from openerp.osv import orm, fields


class asset_category(orm.Model):
    _inherit = 'account.asset.category'

    _columns = {
        'analytics_id': fields.many2one('account.analytic.plan.instance',
                                        'Analytic Distribution'),
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
            analytics_ids.update({
                line.asset_id.id: line.asset_id.category_id.analytics_id.id})
        context['analytics_ids'] = analytics_ids

        return super(account_asset_depreciation_line,
                     self).create_move(cr, uid, ids, context)


class account_move_line(orm.Model):
    _inherit = 'account.move.line'

    def create(self, cr, uid, vals, context=None, check=True):
        """ Retrieve the analytics ids from context, if defined,
        and create move line."""
        analytics_ids = context.get('analytics_ids')
        asset_id = vals.get('asset_id')
        if analytics_ids and asset_id:
            vals['analytics_id'] = analytics_ids[asset_id]

        return super(account_move_line,
                     self).create(cr, uid, vals, context, check)
