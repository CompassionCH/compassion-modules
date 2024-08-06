##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Praz <npraz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class CrmLeadLost(models.TransientModel):
    _inherit = "crm.lead.lost"

    team_id = fields.Many2one('crm.team', string='Sales Team', compute='_compute_team_id')
    lost_stage_id = fields.Many2one('crm.stage', string='Stage', domain="['|', ('team_id', '=', False), ('team_id', '=', team_id)]", required=True)

    def action_lost_reason_apply(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        self.env['crm.stage'].browse(leads.stage_id)
        return leads.action_set_lost(lost_reason=self.lost_reason_id.id, stage_id=self.lost_stage_id.id)

    def _compute_team_id(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        return leads.team_id
