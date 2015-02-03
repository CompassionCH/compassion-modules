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


class resource_calendar(orm.Model):
    _inherit = 'resource.calendar'

    def create(self, cr, uid, vals, context=None):
        res = super(resource_calendar, self).create(cr, uid, vals,
                                                    context=context)
        self.pool.get('hr.planning.wizard').generate(
            cr, uid, [], context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(resource_calendar, self).write(
            cr, uid, ids, vals, context=context)
        self.pool.get('hr.planning.wizard').generate(
            cr, uid, [], context=context)
        return res
