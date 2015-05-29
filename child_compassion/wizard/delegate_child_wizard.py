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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime


class delegate_child_wizard(orm.TransientModel):
    _name = 'delegate.child.wizard'

    def _get_active_ids(self, cr, uid, ids, field_name, arg, context):
        child_ids = list()

        child_obj = self.pool.get('compassion.child')
        childrens = child_obj.browse(
            cr, uid, context.get('active_ids'), context)

        possible_states = ['N', 'R', 'D', 'I', 'Z']
        for child in childrens:
            if child.state in possible_states:
                child_ids.append(child.id)

        return {id: child_ids for id in ids}

    def _default_child_ids(self, cr, uid, context):
        return self._get_active_ids(cr, uid, [0], None, None, context)[0]

    _columns = {
        'partner': fields.many2one(
            'res.partner', string=_('Partner'), required=True),
        'comment': fields.text(_('Comment'), required=True),
        'date_delegation': fields.date(_('Delegation\'s beginning'),
                                       required=True),
        'date_end_delegation': fields.date(_('Delegation\'s end')),
        'child_ids': fields.function(
            _get_active_ids, type='one2many',
            obj='compassion.child',
            string=_('Selected childs')),
    }
    _defaults = {
        'child_ids': (_default_child_ids),
        'date_delegation': datetime.today().strftime(DF),
    }

    def delegate(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        child_ids = self._default_child_ids(cr, uid, context)
        child_obj = self.pool.get('compassion.child')

        if wizard.date_end_delegation:
            if datetime.strptime(wizard.date_delegation, DF) > \
               datetime.strptime(wizard.date_end_delegation, DF):
                raise orm.except_orm("Invalid value", "End date must "
                                     "be later than beginning")

        if datetime.strptime(wizard.date_delegation, DF) <= datetime.today():
            child_obj.write(cr, uid, child_ids, {'state': 'D'},
                            context=context)

        child_obj.write(
            cr, uid, child_ids,
            {'delegated_to': wizard.partner.id,
             'delegated_comment': wizard.comment,
             'date_delegation': wizard.date_delegation,
             'date_end_delegation': wizard.date_end_delegation, },
            context=context)

        return True
