# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class HrAttendanceLocation(models.Model):
    _name = "hr.attendance.location"
    _description = "Attendance Location"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    name = fields.Char()
