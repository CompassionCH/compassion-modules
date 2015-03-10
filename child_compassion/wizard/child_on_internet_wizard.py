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
            possible_states = ['N', 'R', 'Z']
            if child.state in possible_states:
                child_ids.append(child.id)

        return {id: child_ids for id in ids}

    def _default_child_ids(self, cr, uid, context):
        return self._get_active_ids(cr, uid, [0], None, None, context)[0]

    _columns = {
        'state': fields.selection((
            ('default', 'Default'),
            ('error', 'Error')), 'state'),
        'child_ids': fields.function(
            _get_active_ids, type='one2many',
            obj='compassion.child',
            string=_('Selected childs')),
    }

    _defaults = {
        'child_ids': (_default_child_ids),
        'state': 'default'
    }

    def put_child_on_internet(self, cr, uid, ids, context=None):
        child_ids = self._default_child_ids(cr, uid, context)
        child_obj = self.pool.get('compassion.child')

        for child in child_obj.browse(cr, uid, child_ids, context):
            # Check for descriptions
            if(not(child.desc_de) or not(child.desc_fr)):
                raise orm.except_orm(
                    _('Warning'),
                    _('Missing descriptions for child %s') % child.code)
            if not (child.project_id.description_fr and
                    child.project_id.description_de):
                raise orm.except_orm(
                    _('Warning'),
                    _('Missing descriptions for project %s') %
                    child.project_id.code)

            # Check for pictures
            if not(child.portrait and child.fullshot):
                self.pool.get('compassion.child.pictures').create(
                    cr, uid, {'child_id': child.id}, context)
                child = child_obj.browse(cr, uid, child.id, context)
                if not(child.portrait and child.fullshot):
                    raise orm.except_orm(
                        _('Warning'), _('Child has no picture'))

        res = self.pool.get('compassion.child').child_add_to_typo3(
            cr, uid, child_ids, context=None)

        if not res:
            # Display the warning that typo3 index is not synchronized
            self.write(cr, uid, ids, {'state': 'error'}, context)
            return {
                'name': _('Put child on internet'),
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': ids[0],
                'context': context,
                'target': 'new',
            }
        else:
            return True
