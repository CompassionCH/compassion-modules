##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _, api, fields, models


class ICPDisasterImpact(models.Model):
    _name = "fcp.disaster.impact"
    _inherit = "compassion.mapped.model"
    _description = "FCP Disaster Impact"
    _order = "id desc"

    project_id = fields.Many2one(
        "compassion.project",
        "Project",
        compute="_compute_project",
        store=True,
        readonly=True,
    )
    disaster_id = fields.Many2one(
        "fo.disaster.alert", "Disaster Alert", ondelete="cascade", readonly=False
    )
    project_fcp_id = fields.Char(required=True)
    impact_on_fcp_program = fields.Char()
    disaster_impact_description = fields.Char()
    state = fields.Selection(related="disaster_id.state")
    infrastructure = fields.Char()
    field_office_impact_status = fields.Char()

    @api.depends("project_fcp_id")
    def _compute_project(self):
        for impact in self:
            impact.project_id = self.env["compassion.project"].search(
                [("fcp_id", "=", impact.project_fcp_id)], limit=1
            )


class FieldOfficeDisasterUpdate(models.Model):
    _name = "fo.disaster.update"
    _description = "National Office Disaster Update"
    _order = "id desc"
    _inherit = "compassion.mapped.model"

    disaster_id = fields.Many2one(
        "fo.disaster.alert", "Disaster Alert", ondelete="cascade", readonly=False
    )
    fo_id = fields.Many2one(
        "compassion.field.office", "National Office", ondelete="cascade", readonly=False
    )

    fodu_id = fields.Char()
    name = fields.Char()
    summary = fields.Char()

    _sql_constraints = [
        (
            "fodu_id",
            "unique(fodu_id)",
            "The disaster update already exists in database.",
        ),
    ]

    @api.model
    def json_to_data(self, json, mapping_name=None):
        odoo_data = super().json_to_data(json, mapping_name)
        if "summary" in odoo_data:
            odoo_data["summary"] = (
                odoo_data["summary"]
                .replace("\\r", "\n")
                .replace("\\n", "\n")
                .replace("\\t", "\t")
            )

        return odoo_data


class ChildDisasterImpact(models.Model):
    _name = "child.disaster.impact"
    _inherit = "compassion.mapped.model"
    _description = "Child Disaster Impact"
    _order = "id desc"

    child_id = fields.Many2one(
        "compassion.child", "Child", compute="_compute_child", store=True, readonly=True
    )
    disaster_id = fields.Many2one(
        "fo.disaster.alert", "Disaster Alert", ondelete="cascade", readonly=False
    )
    child_global_id = fields.Char(required=True)
    name = fields.Char()
    beneficiary_location = fields.Char()
    beneficiary_physical_condition = fields.Char()
    beneficiary_physical_condition_description = fields.Char()
    caregivers_died_number = fields.Integer()
    caregivers_seriously_injured_number = fields.Integer()
    disaster_status = fields.Char()
    state = fields.Selection(related="disaster_id.state")
    house_condition = fields.Char()
    loss_ids = fields.Many2many("fo.disaster.loss", string="Child loss", readonly=False)
    siblings_died_number = fields.Integer()
    siblings_seriously_injured_number = fields.Integer()
    sponsorship_status = fields.Char()

    @api.depends("child_global_id")
    def _compute_child(self):
        for impact in self:
            impact.child_id = self.env["compassion.child"].search(
                [("global_id", "=", impact.child_global_id)], limit=1
            )

    @api.model
    def create(self, vals):
        """Log a note in child when new disaster impact is registered."""
        impact = super().create(vals)
        if impact.child_id:
            impact.child_id.message_post(
                body=_("Child was affected by the natural disaster %s")
                % impact.disaster_id.name,
                subject=_("Disaster Alert"),
            )
        return impact


class DisasterLoss(models.Model):
    _inherit = "connect.multipicklist"
    _name = "fo.disaster.loss"
    _description = "National office disaster loss"
    res_model = "child.disaster.impact"
    res_field = "loss_ids"


class FieldOfficeDisasterAlert(models.Model):
    _name = "fo.disaster.alert"
    _description = "National Office Disaster Alert"
    _inherit = ["mail.thread", "compassion.mapped.model"]
    _order = "disaster_date desc, id desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    disaster_id = fields.Char()
    area_description = fields.Char()
    close_date = fields.Date()

    # GMC notification related fields
    disaster_communication_update_name = fields.Char()
    api_url = fields.Char()

    name = fields.Char()
    disaster_date = fields.Datetime()
    state = fields.Selection([("Active", "Active"), ("Closed", "Closed")])
    disaster_type = fields.Selection(
        [
            ("Animal / Insect Infestation", "Animal / Insect Infestation"),
            (
                "Civil Or Political Unrest / Rioting",
                "Civil Or Political Unrest / Rioting",
            ),
            ("Disease / Epidemic", "Disease / Epidemic"),
            ("Earthquake", "Earthquake"),
            ("Extreme Temperatures", "Extreme Temperatures"),
            ("Fire", "Fire"),
            ("Hail Storm", "Hail Storm"),
            ("Heavy Rains / Flooding", "Heavy Rains / Flooding"),
            (
                "Hurricanes / Tropical Storms / Cyclones / Typhoons",
                "Hurricanes / Tropical Storms / Cyclones / Typhoons",
            ),
            ("Industrial Accident", "Industrial Accident"),
            ("Landslide", "Landslide"),
            ("Strong Winds", "Strong Winds"),
            ("Tornado", "Tornado"),
            ("Transport Accident", "Transport Accident"),
            ("Tsunami", "Tsunami"),
            ("Volcanic Activity", "Volcanic Activity"),
            ("Water Contamination Crisis", "Water Contamination Crisis"),
        ]
    )
    estimated_basic_supplies_needed = fields.Char()
    estimated_homes_destroyed = fields.Char()
    estimated_loss_of_life = fields.Char()
    estimated_loss_of_livelihood = fields.Char()
    estimated_not_attending_project = fields.Char()
    estimated_rehabilitation_funds_usd = fields.Float()
    estimated_relief_funds_usd = fields.Float()
    estimated_serious_injuries = fields.Char()

    field_office_id = fields.Many2one(
        "compassion.field.office",
        string="National Offices",
        ondelete="cascade",
        readonly=False,
    )
    field_office_damage = fields.Char()
    field_office_impact_description = fields.Char()

    impact_description = fields.Char()
    impact_on_fcp_infrastructure_damaged = fields.Integer()
    impact_on_fcp_infrastructure_destroyed = fields.Integer()
    impact_on_fcp_program_temporarily_closed = fields.Integer()
    impact_to_field_office_operations = fields.Char()

    is_additional_funds_requested = fields.Boolean()
    is_communication_sensitive = fields.Boolean()
    is_estimated_damage_over_one_million_usd = fields.Boolean()

    reported_loss_of_life_beneficiaries = fields.Integer()
    reported_loss_of_life_caregivers = fields.Integer()
    reported_loss_of_life_siblings = fields.Integer()
    reported_number_beneficiaries_impacted = fields.Integer()
    reported_number_of_fcps_impacted = fields.Integer()
    reported_serious_injuries_beneficiaries = fields.Integer()
    reported_serious_injuries_caregivers = fields.Integer()
    reported_serious_injuries_siblings = fields.Integer()
    response_description = fields.Char()

    severity_level = fields.Char()
    source_kit_name = fields.Char()

    fcp_disaster_impact_ids = fields.One2many(
        "fcp.disaster.impact", "disaster_id", "FCP Disaster Impact", readonly=False
    )
    fo_disaster_update_ids = fields.One2many(
        "fo.disaster.update", "disaster_id", "National Office Update", readonly=False
    )
    child_disaster_impact_ids = fields.One2many(
        "child.disaster.impact", "disaster_id", "Child Disaster Impact", readonly=False
    )
    number_impacted_children = fields.Integer(
        compute="_compute_impacted_children", store=True
    )

    _sql_constraints = [
        (
            "disaster_id",
            "unique(disaster_id)",
            "The disaster alert already exists in database.",
        ),
    ]

    @api.depends("child_disaster_impact_ids")
    def _compute_impacted_children(self):
        for disaster in self:
            disaster.number_impacted_children = len(
                disaster.child_disaster_impact_ids.mapped("child_id")
            )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """Update if disaster already exists."""
        disaster_id = vals.get("disaster_id")
        disaster = self.search([("disaster_id", "=", disaster_id)])
        # Notify users
        notify_ids = (
            self.env["res.config.settings"].sudo().get_param("disaster_notify_ids")
        )
        if disaster:
            disaster.write(vals)
            if notify_ids:
                disaster.message_post(
                    body=_("The Disaster Alert was just updated."),
                    subject=_("Disaster Alert Update"),
                    partner_ids=notify_ids,
                    subtype_xmlid="mail.mt_comment",
                )
        else:
            disaster = super().create(vals)
            if notify_ids:
                disaster.message_post(
                    body=_("The disaster alert has just been received."),
                    subject=_("New Disaster Alert"),
                    partner_ids=notify_ids,
                    subtype_xmlid="mail.mt_comment",
                )
        return disaster

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def view_children(self):
        return {
            "name": _("Impacted children"),
            "domain": [
                ("id", "in", self.child_disaster_impact_ids.filtered("child_id").ids)
            ],
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "child.disaster.impact",
            "target": "current",
        }

    def view_icp(self):
        return {
            "name": _("Impacted projects"),
            "domain": [
                ("id", "in", self.fcp_disaster_impact_ids.mapped("project_id").ids)
            ],
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "compassion.project",
            "target": "current",
        }

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def simulate_details(self, commkit_data):
        """This can be used for simulating the reception of Disaster Alert
        with all details already present in the message. You should change the
        field `incoming_method` of the gmc.action `Disaster Alert` to use this
        method."""
        fo_ids = list()
        for single_data in commkit_data.get("DisasterResponseList", [commkit_data]):
            vals = self.json_to_data(single_data, mapping_name="Disaster Alert")
            fo_disaster = self.create(vals)
            fo_ids.append(fo_disaster.id)
        return fo_ids

    @api.model
    def process_commkit(self, commkit_data):
        message_obj = self.env["gmc.message"]
        action_id = self.env.ref("child_compassion.field_office_disaster_detail").id
        fo_ids = list()
        for single_data in commkit_data.get("DisasterResponseList", [commkit_data]):
            vals = self.json_to_data(
                single_data, mapping_name="Disaster Alert Notification"
            )
            fo_disaster = self.create(vals)
            message_vals = {
                "action_id": action_id,
                "object_id": fo_disaster.id,
            }
            message_obj.with_context(async_mode=False).create(message_vals)
            fo_ids.append(fo_disaster.id)

        return fo_ids
