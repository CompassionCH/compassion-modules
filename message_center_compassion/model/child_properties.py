# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import models


class child_properties(models.Model):
    """ Write contracts in Biennial State when a picture is attached to a
        Case Study. """
    _inherit = 'compassion.child.property'

    def attach_pictures(self, pictures_id):
        res = super(child_properties, self).attach_pictures(pictures_id)
        contracts = self.mapped('child_id.sponsorship_ids').mapped(
            lambda c: c.state in ('waiting', 'active', 'mandate'))
        if contracts:
            contracts.new_biennial()
        return res
