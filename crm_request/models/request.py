# -*- coding: utf-8 -*-45.00
# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CrmClaim(models.Model):
    _inherit = "crm.claim"
    _description = "Request"

    date = fields.Datetime(string='Date', readonly=True, index=False)
    name = fields.Char(string='Subject')
    code = fields.Char(string='Number')
    claim_type = fields.Many2one(string='Type')

    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------
    # Change the stage to "Waiting on support" when the customer write a new
    # mail on the thread
    @api.multi
    def message_update(self, msg_dict, update_vals=None):
        result = super(CrmClaim, self).message_update(msg_dict, update_vals)
        for request in self:
            request.stage_id = self.env[
                'ir.model.data'].get_object_reference(
                'crm_request', 'stage_wait_support')[1]
        return result

    # Change the stage to "Waiting on customer" when the employee answer to the
    # supporter
    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, **kwargs):
        result = super(CrmClaim, self).message_post(**kwargs)

        if 'mail_server_id' in kwargs:
            for request in self:
                ir_data = self.env['ir.model.data']
                request.stage_id = ir_data.get_object_reference(
                    'crm_request', 'stage_wait_customer')[1]

        return result

    @api.multi
    def write(self, values):
        # Get all followers before change
        super(CrmClaim, self)._get_followers

        #  unsubscribe all followers before change
        super(CrmClaim, self).message_unsubscribe(
            partner_ids=[self.message_partner_ids.id])

        # launching the standard process "write"
        return super(CrmClaim, self).write(values)
