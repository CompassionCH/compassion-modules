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

from openerp.osv import orm, fields


class update_child_wizard(orm.TransientModel):
    _name = 'update.child.picture.date'

    def update(self, cr, uid, method, context=None):
        count = 1
        print('LAUNCH CHILD UPDATE -- ' + method)
        child_obj = self.pool.get('compassion.child')
        child_ids = child_obj.search(
            cr, uid, [('state', 'not in', ['F', 'X']),
                      ('update_done', '=', False)], context=context)

        total = str(len(child_ids))
        for child in child_obj.browse(cr, uid, child_ids, context):
            try:
                print('Updating child {0}/{1}').format(str(count), total)

                if method == 'picture':
                    child_obj.get_infos(cr, uid, child.id, context)
                elif method == 'basic':
                    child_obj._get_basic_informations(cr, uid, child.id,
                                                      context)
                child.write({'update_done': True})

            except Exception:
                if child.state != 'E':
                    child.write({
                        'state': 'E',
                        'previous_state': child.state})
                self.pool.get('mail.thread').message_post(
                    cr, uid, child.id,
                    traceback.format_exc(), 'Child update',
                    context={'thread_model': 'compassion.child'})
            finally:
                count += 1
                cr.commit()
        # When update is finished, restore update state
        child_obj.write(cr, uid, child_ids, {'update_done': False}, context)
        return True


class child_compassion(orm.Model):
    _inherit = 'compassion.child'

    _columns = {
        'update_done': fields.boolean('update done')
    }
