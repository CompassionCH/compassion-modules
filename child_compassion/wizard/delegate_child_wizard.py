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

class delegate_child_wizard(orm.TransientModel):
    _name = 'delegate.child.wizard'

    _columns = {
        'partner':fields.many2one(
            'res.partner', string=_('Partner'), required=True),
        'comment':fields.text(_('Comment'),required=True),
    }

    def delegate(self, cr, uid, ids, context=None): 
        child_obj = self.pool.get('compassion.child')
        childrens = child_obj.browse(
                cr, uid, context.get('active_ids', list()), context)
        child_ids = []
        
        for child in childrens:
            possible_states = ['N','R','D','I']
            if (child.state in possible_states):
                if child.state == 'I':
                    child_obj.child_remove_from_typo3(cr, uid, [child.id], context)
                child_ids.append(child.id)
            
        wizard = self.browse(cr, uid, ids[0], context)

        child_obj.write(
            cr, uid, child_ids,
            {'state':'D','delegated_to':wizard.partner.id,'delegated_comment':wizard.comment},
            context=context)
            
        # return {
            # 'type': 'ir.actions.client',
            # 'tag': 'action_warn',
            # 'name': 'Warning',
            # 'params': {
            # 'title': 'Warning!',
            # 'text': 'Entered Quantity is greater than quantity on source.',
            # }
        # }

