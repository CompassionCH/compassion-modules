# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _

import requests
import logging


logger = logging.getLogger(__name__)


class child_compassion(orm.Model):
    _inherit = 'compassion.child'

    def _get_related_contracts(self, cr, uid, ids, field_name, args,
                               context=None):
        con_obj = self.pool.get('recurring.contract')
        return {
            child_id: con_obj.search(cr, uid, [('child_id', '=', child_id)],
                                     context=context)
            for child_id in ids
        }

    def _get_unsponsored_since(self, cr, uid, ids, field_name, args,
                               context=None):
        """ Returns the date since the child is waiting for a sponsor.
        If child was never sponsored, this date comes from GMC services,
        otherwise we can infer it by looking at last sponsorship. """
        res = dict()
        con_obj = self.pool.get('recurring.contract')
        for child in self.browse(cr, uid, ids, context):
            con_ids = con_obj.search(
                cr, uid, [('child_id', '=', child.id)], order='end_date desc',
                limit=1, context=context)
            if con_ids and child.state not in ('P', 'F', 'X'):
                contract = con_obj.browse(cr, uid, con_ids[0], context)
                res[child.id] = contract.end_date
            elif not child.has_been_sponsored:
                # Retrieve the information from the webservice
                url = self.get_url(child.code, 'information')
                r = requests.get(url)
                json_data = r.json()
                if r.status_code == 200:
                    res[child.id] = json_data['beginWaitTime'] or False
                else:
                    logger.error(
                        'An error occured while fetching the unsponsored '
                        ' date of child %s.' % child.code +
                        json_data['error']['message'])
                    res[child.id] = False
            else:
                res[child.id] = False

        return res

    _columns = {
        'contract_ids': fields.function(
            _get_related_contracts, type='one2many', obj='recurring.contract',
            string=_("Sponsorships"), readonly=True),
        'unsponsored_since': fields.function(
            _get_unsponsored_since, type='date',
            string=_('Unsponsored since'), readonly=True, store={
                'compassion.child': (lambda self, cr, uid, ids,
                                     context=None: ids, ['state'], 10)}),
    }

    def _recompute_unsponsored(self, cr, uid, ids, context=None):
        """ Useful for updating unset values """
        self._store_set_values(cr, uid, ids, ['unsponsored_since'], context)
        return True

    def child_add_to_typo3(self, cr, uid, ids, context=None):
        """ Update unsponsored date before puting the children on internet.
        """
        self._recompute_unsponsored(cr, uid, ids, context)
        return super(child_compassion, self).child_add_to_typo3(cr, uid, ids,
                                                                context)

    def get_infos(self, cr, uid, ids, context=None):
        """ Update unsponsored date. """
        if not isinstance(ids, list):
            ids = [ids]
        self._recompute_unsponsored(cr, uid, ids, context)
        return super(child_compassion, self).get_infos(cr, uid, ids, context)
