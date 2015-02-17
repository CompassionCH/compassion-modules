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


class compassion_project(orm.Model):
    """ Add update method. """
    _inherit = 'compassion.project'

    def update(self, cr, uid, args, context=None):
        """ When we receive a notification that a project has been updated,
        we fetch the last informations. """
        self.update_informations(cr, uid, args.get('object_id'), context)
        return True
