# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields


class undelegate_child_wizard(models.TransientModel):
    _name = 'undelegate.child.wizard'

    child_ids = fields.One2many(
        'compassion.child', string='Selected children',
        compute='_set_children', default=lambda self: self._set_children())

    def _set_children(self):
        child_ids = list()
        for child in self.env['compassion.child'].browse(
                self.env.context.get('active_ids')):
            if (child.state == 'D'):
                child_ids.append(child.id)

        self.child_ids = child_ids

    def undelegate(self):
        child_obj = self.env['compassion.child']
        for child in child_obj.browse(self.env.context.get('active_ids')):
            if child.state == 'D':
                newstate = 'R' if child.has_been_sponsored else 'N'
                child.write({
                    'state': newstate, 'delegated_to': False,
                    'delegated_comment': False, 'date_delegation': False,
                    'date_end_delegation': False})

        return True
