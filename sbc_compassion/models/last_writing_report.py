##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api
from odoo import tools


class LastWritingReport(models.Model):
    _name = "correspondence.last.writing.report"
    _table = "correspondence_last_writing_report"
    _description = "Last writing report"
    _order = "last_write_date desc,activation_date desc"
    _auto = False

    sponsorship_id = fields.Many2one(
        "recurring.contract", "Sponsorship", readonly=False
    )
    name = fields.Char(related="sponsorship_id.name")
    partner_id = fields.Many2one("res.partner", "Partner", readonly=False)
    child_id = fields.Many2one("compassion.child", "Child", readonly=False)
    sponsorship_type = fields.Selection(related="sponsorship_id.type")
    activation_date = fields.Datetime()
    first_write_date = fields.Date()
    last_write_date = fields.Date()
    time_to_first_writing = fields.Integer(help="In days")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
CREATE OR REPLACE VIEW correspondence_last_writing_report AS
SELECT sp.id, sp.id AS sponsorship_id, sp.correspondent_id AS partner_id,
       sp.child_id, sp.type AS sponsorship_type, sp.activation_date,
       MAX(c.scanned_date) AS last_write_date,
       MIN(c.scanned_date) AS first_write_date,
       EXTRACT(epoch FROM COALESCE(MIN(c.scanned_date), CURRENT_DATE)
       - sp.activation_date)/86400 AS time_to_first_writing
FROM recurring_contract sp
FULL OUTER JOIN correspondence c ON c.sponsorship_id = sp.id
WHERE sp.state = 'active' AND sp.child_id IS NOT NULL
AND c.direction = 'Supporter To Beneficiary'
GROUP BY sp.id, sp.correspondent_id, sp.child_id, sp.type, sp.activation_date
ORDER BY id asc;
"""
        )
