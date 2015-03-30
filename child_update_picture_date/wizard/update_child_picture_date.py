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
import traceback

from openerp.osv import orm


class update_child_picture_date(orm.TransientModel):
    _name = 'update.child.picture.date'

    def update(self, cr, uid, context=None):
        print('LAUNCH CHILD PICTURE UPDATE')
        child_obj = self.pool.get('compassion.child')
        child_ids = child_obj.search(
            cr, uid, [('state', 'not in', ['F', 'X'])], context=context)

        for child in child_obj.browse(cr, uid, child_ids, context):
            try:
                child_obj.get_infos(cr, uid, child.id, context)
            except Exception:
                child_obj.write(
                    cr, uid, child.id,
                    {'state': 'E', 'previous_state': child.state},
                    context=context)
                self.pool.get('mail.thread').message_post(
                    cr, uid, child.id,
                    traceback.format_exc(), 'Child update',
                    context={'thread_model': 'compassion.child'})
