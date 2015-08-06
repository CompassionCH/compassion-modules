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

from openerp import models, fields, api, exceptions, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime


class delegate_child_wizard(models.TransientModel):
    _name = 'delegate.child.wizard'

    partner = fields.Many2one(
        'res.partner', 'Partner', required=True)
    comment = fields.Text('Comment', required=True)
    date_delegation = fields.Date(
        'Delegation\'s beginning', required=True,
        default=datetime.today().strftime(DF))
    date_end_delegation = fields.Date('Delegation\'s end')
    child_ids = fields.Many2many(
        'compassion.child', string='Selected children',
        compute='_set_active_ids',
        default=lambda self: self._set_active_ids())

    @api.multi
    def _set_active_ids(self):
        child_obj = self.env['compassion.child']
        active_ids = self.env.context.get('active_ids')
        child_ids = [c.id for c in child_obj.browse(active_ids)
                     if c.is_available]

        self.write({'child_ids': [(6, 0, child_ids)]})
        return child_ids

    @api.multi
    def delegate(self):
        self.ensure_one()
        child_ids = self.env['compassion.child'].browse(self.env.context.get(
            'active_ids')).filtered('is_available')

        if self.date_end_delegation:
            if datetime.strptime(self.date_delegation, DF) > \
               datetime.strptime(self.date_end_delegation, DF):
                raise exceptions.Warning(
                    "Invalid value",
                    _("End date must be later than beginning"))

        if datetime.strptime(self.date_delegation, DF) <= datetime.today():
            child_ids.write({'state': 'D'})

        child_ids.write({
            'delegated_to': self.partner.id,
            'delegated_comment': self.comment,
            'date_delegation': self.date_delegation,
            'date_end_delegation': self.date_end_delegation})

        return True
