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

from openerp import models, fields


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    compassion_event_id = fields.Many2one('crm.event.compassion', 'Event')
