# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm


class child_remove_from_internet(orm.TransientModel):
    _name = 'child.remove.from.internet'

    def remove_child_from_internet(self, cr, uid, ids, context=None):
        child_obj = self.pool.get('compassion.child')
        childrens = child_obj.browse(
            cr, uid, context.get('active_ids', list()), context)
        child_ids = []

        for child in childrens:
            possible_states = ['I']
            if child.state in possible_states:
                child_ids.append(child.id)

        child_obj.child_remove_from_typo3(cr, uid, child_ids, context=None)
