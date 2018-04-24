# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields
import logging


logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """ Add a field for communication preference. """
    _inherit = 'res.partner'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    global_communication_delivery_preference = fields.Selection(
        selection='_get_delivery_preference',
        default='auto_digital',
        required=True,
        help='Delivery preference for Global Communication')
    email_only = fields.Boolean(help="Don't send any printed communication")
    communication_count = fields.Integer(compute='_compute_comm_count')

    _sql_constraints = [
        ('email_is_set_if_email_only',
         "CHECK (NOT email_only OR email IS NOT NULL)",
         'The email address should not be empty if email_only is selected.'),
        ('not_both_and_email_only',
         "CHECK (NOT email_only OR global_communication_delivery_preference "
         "!= 'both')",
         'The send mode should not be "both" if email_only is selected.')
    ]

    @api.multi
    def _compute_comm_count(self):
        for partner in self:
            partner.communication_count = self.env[
                'partner.communication.job'].search_count([
                    ('partner_id', '=', partner.id),
                    ('state', '!=', 'cancel'),
                ])

    @api.model
    def _get_delivery_preference(self):
        return self.env[
            'partner.communication.config'].get_delivery_preferences()
