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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class child_on_internet_wizard(orm.TransientModel):
    _name = 'child.on.internet.wizard'

    def _get_active_ids(self, cr, uid, ids, field_name, arg, context):
        child_ids = list()

        child_obj = self.pool.get('compassion.child')
        childrens = child_obj.browse(
            cr, uid, context.get('active_ids'), context)

        for child in childrens:
            possible_states = ['N', 'R']
            if child.state in possible_states:
                child_ids.append(child.id)

        return {id: child_ids for id in ids}

    def _default_child_ids(self, cr, uid, context):
        return self._get_active_ids(cr, uid, [0], None, None, context)[0]

    _columns = {
        'child_ids': fields.function(
            _get_active_ids, type='one2many',
            obj='compassion.child',
            string=_('Selected childs')),
    }

    _defaults = {
        'child_ids': (_default_child_ids)
    }

    def put_child_on_internet(self, cr, uid, ids, context=None):
        child_ids = self._default_child_ids(cr, uid, context)

        for child in self.pool.get('compassion.child').browse(
                cr, uid, child_ids, context):
            # Check for descriptions
            if(not(child.desc_de) or not(child.desc_fr)):
                raise orm.except_orm(
                    _('Warning'), _('Missing descriptions'))

            # Check for pictures
            if not(child.portrait and child.fullshot):
                raise orm.except_orm(
                    _('Warning'), _('Child has no picture'))

        self.pool.get('compassion.child').child_add_to_typo3(
            cr, uid, child_ids, context=None)
