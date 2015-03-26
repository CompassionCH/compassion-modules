# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.osv import orm


class child_properties(orm.Model):
    """ Write contracts in Biennial State when a picture is attached to a
        Case Study. """
    _inherit = 'compassion.child.property'

    def attach_pictures(self, cr, uid, ids, pictures_id, context=None):
        res = super(child_properties, self).attach_pictures(
            cr, uid, ids, pictures_id, context)
        if not isinstance(ids, list):
            ids = [ids]
        property = self.browse(cr, uid, ids, context)[0]
        for contract in property.child_id.contract_ids:
            if contract.state in ('waiting', 'active', 'mandate'):
                contract.write({'gmc_state': 'biennial'})
        return res
