# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Open Net Sarl (https://www.open-net.ch)
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Eicher Stephane <seicher@compassion.ch>
#    @author: Coninckx David <david@coninckx.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ResCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    due_hours = fields.Float()
