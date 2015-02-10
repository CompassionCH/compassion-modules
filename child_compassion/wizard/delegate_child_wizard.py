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
from datetime import datetime


class delegate_child_wizard(orm.TransientModel):
    _name = 'delegate.child.wizard'

    def _get_active_ids(self, cr, uid, ids, field_name, arg, context):
        child_ids = list()

        child_obj = self.pool.get('compassion.child')
        childrens = child_obj.browse(
            cr, uid, context.get('active_ids'), context)

        for child in childrens:
            possible_states = ['N', 'R', 'D', 'I']
            if (child.state in possible_states):
                child_ids.append(child.id)

        return {id: child_ids for id in ids}

    def _default_child_ids(self, cr, uid, context):
        return self._get_active_ids(cr, uid, [0], None, None, context)[0]

    _columns = {
        'partner': fields.many2one(
            'res.partner', string=_('Partner'), required=True),
        'comment': fields.text(_('Comment'), required=True),
        'child_ids': fields.function(
            _get_active_ids, type='one2many',
            obj='compassion.child',
            string=_('Selected childs')),
    }
    _defaults = {
        'child_ids': (_default_child_ids)
    }

    def delegate(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        child_ids = self._default_child_ids(cr, uid, context)
        child_obj = self.pool.get('compassion.child')

        for child in child_obj.browse(cr, uid, child_ids, context):
            if (child.state == 'I'):
                child_obj.child_remove_from_typo3(cr, uid, [child.id], context)

        child_obj.write(
            cr, uid, child_ids,
            {'state': 'D', 'delegated_to': wizard.partner.id,
                'delegated_comment': wizard.comment,
                'date_delegation': datetime.today()},
            context=context)
