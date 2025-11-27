##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    compassion_event_id = fields.Many2one(
        "crm.event.compassion", "Compassion Event", readonly=False
    )
