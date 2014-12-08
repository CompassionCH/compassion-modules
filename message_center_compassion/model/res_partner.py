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
from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import date


class res_partner(orm.Model):
    """ UPSERT constituents. """
    _inherit = 'res.partner'

    def write(self, cr, uid, ids, vals, context=None):
        """If partner has active contracts, UPSERT Constituent in GMC."""
        for partner in self.browse(cr, uid, ids, context):
            contract_ids = self.pool.get('recurring.contract').search(
                cr, uid, [('partner_id', '=', partner.id),
                          ('state', 'not in', ('terminated', 'cancelled'))],
                context=context)
            if contract_ids and (vals.get('firstname') or vals.get('lastname')
                                 or vals.get('name')):
                # UpsertConstituent Message
                action_id = self.pool.get('gmc.action').search(
                    cr, uid, [('name', '=', 'UpsertConstituent')],
                    limit=1, context=context)[0]
                message_vals = {
                    'action_id': action_id,
                    'object_id': partner.id,
                    'partner_id': partner.id,
                    'date': date.today().strftime(DF),
                }
                self.pool.get('gmc.message.pool').create(
                    cr, uid, message_vals, context=context)
        return super(res_partner, self).write(cr, uid, ids, vals, context)
