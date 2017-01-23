# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models, fields
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
        default='digital',
        required=True,
        help='Delivery preference for Global Communication')

    @api.model
    def _get_delivery_preference(self):
        return self.env[
            'partner.communication.config'].get_delivery_preferences()
