# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.osv import orm


class compassion_child(orm.Model):

    """ Add allocation and deallocation methods on the children. """
    _inherit = 'compassion.child'

    def allocate(self, cr, uid, args, context=None):
        child_id = self.create(cr, uid, args, context=context)
        self.update(cr, uid, child_id, context=context)
        return self.get_basic_informations(cr, uid, child_id, context=context)

    def deallocate(self, cr, uid, id, context=None):
        # TODO : should be done from GP or see what to do.
        return True

    def depart(self, cr, uid, id, context=None):
        # TODO : terminate the contract, mark the child as departed and the
        # user should do the right communication from GP.
        return True

    def update(self, cr, uid, id, context=None):
        """ When we receive a notification that child has been updated,
        we fetch the last case study. """
        self.get_last_case_study(cr, uid, id, context=context)
        return True

compassion_child()


class compassion_project(orm.Model):

    """ Add update method. """
    _inherit = 'compassion.project'

    def update(self, cr, uid, id, context=None):
        # TODO : add a method that calls webservice like get_last_case_study.
        return True
