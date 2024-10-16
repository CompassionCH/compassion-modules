##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import datetime

from odoo import SUPERUSER_ID, api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    planned_sponsorships = fields.Integer(
        "Expected new sponsorships",
        tracking=True,
        compute="_compute_planned_sponsorship",
        store=True,
    )
    event_ids = fields.One2many(
        "crm.event.compassion", "lead_id", "Events", readonly=False
    )

    def create_event(self):
        self.ensure_one()
        # Open the create form...
        return {
            "type": "ir.actions.act_window",
            "name": "New event",
            "view_mode": "form,calendar,tree",
            "res_model": "crm.event.compassion",
            "target": "current",
            "context": {
                "default_name": self.name,
                "default_partner_id": self.partner_id.id,
                "default_street": self.street,
                "default_street2": self.street2,
                "default_city": self.city,
                "default_state_id": self.state_id.id,
                "default_zip": self.zip,
                "default_country_id": self.country_id.id,
                "default_user_id": self.user_id.id,
                "default_planned_sponsorships": self.planned_sponsorships,
                "default_lead_id": self.id,
            },
        }

    def write(self, vals):
        updated_stage_id = vals.get("stage_id")

        if updated_stage_id:
            stage = self.env["crm.stage"].browse(updated_stage_id)
            is_lost = not self.active and self.probability == 0
            if not is_lost and stage.is_lost:
                vals.update({"active": False, "probability": 0})
            elif is_lost and not stage.is_lost:
                vals.update({"active": True, "lost_reason": False})
                lead_probabilities = self._pls_get_naive_bayes_probabilities()
                if self.id in lead_probabilities:
                    vals.update({"automated_probability": lead_probabilities[self.id]})
                    if self.is_automated_probability:
                        vals.update({"probability": lead_probabilities[self.id]})

        return super().write(vals)

    @api.depends("event_ids", "event_ids.planned_sponsorships")
    def _compute_planned_sponsorship(self):
        for lead in self:
            future_planned_sponsorships = 0
            for e in lead.event_ids:
                if e.start_date > datetime.datetime.now():
                    future_planned_sponsorships += e.planned_sponsorships
            lead.planned_sponsorships = future_planned_sponsorships

    def _merge_data(self, fields):
        """Update the _merge_data function to be able to merge
        many2many and one2may

            :param fields: list of fields to process
            :return dict data: contains the merged values of
            the new opportunity
        """
        data = super()._merge_data(fields)

        for field_name in fields:
            field = self._fields.get(field_name)
            if field.type in ("many2many", "one2many"):
                data[field_name] = [(6, 0, self.mapped(field_name).ids)]

        return data

    @api.depends("partner_id")
    def _compute_name(self):
        for lead in self:
            if not lead.name and lead.partner_id and lead.partner_id.name:
                lead.name = lead.partner_id.name

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        res = super()._read_group_stage_ids(stages, domain, order)

        # if the domain contains team_id filters, add them to the search domain
        team_id_domain = [
            cond
            for cond in domain
            if hasattr(cond, "__getitem__") and cond[0] == "team_id"
        ]

        if len(team_id_domain) > 0:
            search_domain = [
                *(["|"] * (len(team_id_domain) - 1) + team_id_domain),
            ]
            res += stages.browse(
                stages._search(
                    search_domain, order=order, access_rights_uid=SUPERUSER_ID
                )
            )

            # Order is lost by the merge and empty stages are pushed back, so we need
            # to sort them.
            res = res.sorted()

        return res
