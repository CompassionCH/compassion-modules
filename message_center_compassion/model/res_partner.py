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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import date


class res_partner(orm.Model):

    """ UPSERT constituents. """
    _inherit = 'res.partner'

    """ Add write_date for the middleware to have the information. """
    def _get_write_date(self, cr, uid, ids, field_name, args, context=None):
        metadata = self.perm_read(cr, uid, ids, context)
        return {md['id']: md['write_date'][:10] for md in metadata}

    _columns = {
        'write_date': fields.function(_get_write_date, 'Write date',
                                      type='date')
    }

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('firstname') or vals.get('lastname') or \
                vals.get('name'):
            self._upsert_constituent(cr, uid, ids, context)
        return super(res_partner, self).write(cr, uid, ids, vals, context)

    def write_from_gp(self, cr, uid, ids, vals, context=None):
        """ GP always send firstname and lastname. We check if they changed.
        """
        to_update_ids = list()
        for partner in self.browse(cr, uid, ids, context):
            new_firstname = vals.get('fisrtname', partner.firstname)
            new_lastname = vals.get('lastname', partner.lastname)
            if partner.firstname != new_firstname or \
                    partner.lastname != new_lastname:
                to_update_ids.append(partner.id)
        self._upsert_constituent(cr, uid, to_update_ids, context)
        return super(res_partner, self).write_from_gp(cr, uid, ids, vals,
                                                      context)

    def _upsert_constituent(self, cr, uid, ids, context=None):
        """If partner has active contracts, UPSERT Constituent in GMC."""
        if not isinstance(ids, list):
            ids = [ids]
        for partner in self.browse(cr, uid, ids, context):
            contract_ids = self.pool.get('recurring.contract').search(
                cr, uid, [('partner_id', '=', partner.id),
                          ('state', 'not in', ('terminated', 'cancelled'))],
                context=context)
            if contract_ids:
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
