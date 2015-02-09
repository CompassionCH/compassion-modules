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
import pdb

class undelegate_child_wizard(orm.TransientModel):
    _name = 'undelegate.child.wizard'

    def undelegate(self, cr, uid, ids, context=None): 
        child_obj = self.pool.get('compassion.child')
        childrens = child_obj.browse(
                cr, uid, context.get('active_ids', list()), context)

        for child in childrens:
            if (child.state == 'D'):
                newstate = 'N'
                if (child.has_been_sponsored):
                    newstate = 'R'

                self.pool.get('compassion.child').write(
                        cr, uid, child.id,
                        {'state':newstate},
                        context=context)
