# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class EventCompassion(models.Model):

    _inherit = 'crm.event.compassion'

    accepts_sms_booking = fields.Boolean('Accepts SMS booking', default=False)
