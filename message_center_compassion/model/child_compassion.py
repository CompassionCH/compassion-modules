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
        return True

    def deallocate(self, cr, uid, id, context=None):
        """Deallocate is uncertain, because it may disappear from GMC messages
        when the childpool will be global (same children for all countries).
        Until we don't need it, we don't implement it."""
        return True

    def depart(self, cr, uid, id, context=None):
        """For the depart method, we don't have enough information on the
        children right now to do it (state), plus we would need the user
        to be aware of procedure to do in this case. So it is a bit early
        to have it implemented, we should carefully separe functionnalities
        between GP and Odoo before."""
        # TODO : possibly terminate the contract, mark the child as departed
        # and the user should do the right communication
        # to the sponsor from GP.
        return True

    def update(self, cr, uid, id, context=None):
        """ When we receive a notification that child has been updated,
        we fetch the last case study. """
        self.get_infos(cr, uid, id, context=context)
        return True


class compassion_project(orm.Model):
    """ Add update method. """
    _inherit = 'compassion.project'

    def update(self, cr, uid, id, context=None):
        """ When we receive a notification that a project has been updated,
        we fetch the last informations. """
        self.update_informations(cr, uid, id, context)
        return True
