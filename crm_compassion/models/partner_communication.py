from odoo import fields, models


class CommunicationJob(models.Model):
    _inherit = "partner.communication.job"

    event_id = fields.Many2one("crm.event.compassion", "Event", readonly=False)
