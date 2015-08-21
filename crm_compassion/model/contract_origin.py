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

from openerp import api, models, fields


class contract_origin(models.Model):
    """ Add event to origin of a contract """
    _inherit = 'recurring.contract.origin'

    event_id = fields.Many2one('crm.event.compassion', 'Event')

    def _name_get(self):
        if self.type == 'event':
            name = self.event_id.full_name
        else:
            name = super(contract_origin, self)._name_get()
        return name


class contracts(models.Model):
    """ Adds the Salesperson to the contract. """

    _inherit = 'recurring.contract'

    user_id = fields.Many2one('res.partner', 'Ambassador')

    @api.onchange('origin_id')
    def on_change_origin(self):
        origin = self.origin_id
        if origin:
            self.user_id = self._get_user_from_origin(origin)

    def _get_user_from_origin(self, origin):
        user_id = False
        if origin.partner_id:
            user_id = origin.partner_id.id
        elif origin.analytic_id and origin.analytic_id.manager_id:
            user_id = origin.analytic_id.manager_id.partner_id.id
        elif origin.event_id and origin.event_id.user_id:
            user_id = origin.event_id.user_id.partner_id.id
        return user_id


class contract_group(models.Model):
    """ Push salesperson to invoice on invoice generation """
    _inherit = 'recurring.contract.group'

    def _setup_inv_line_data(self, contract_line, invoice_id):
        invl_data = super(contract_group, self)._setup_inv_line_data(
            contract_line, invoice_id)
        if contract_line.contract_id.user_id:
            invl_data['user_id'] = contract_line.contract_id.user_id.id
        return invl_data
