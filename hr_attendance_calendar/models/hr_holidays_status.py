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

from odoo import models, fields


class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    remove_from_due_hours = fields.Boolean(string="Remove from due hours",
                                           default=False)
