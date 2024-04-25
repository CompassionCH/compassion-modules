##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>, Philippe Heer
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import _, api, fields, models


class ProjectLifecycle(models.Model):
    _name = "compassion.project.ile"
    _inherit = ["translatable.model", "compassion.mapped.model"]
    _description = "Project lifecycle event"
    _order = "date desc, id desc"

    project_id = fields.Many2one(
        "compassion.project", required=True, ondelete="cascade", readonly=True
    )
    date = fields.Date(readonly=True, default=fields.Date.today)
    type = fields.Selection(
        [
            ("Suspension", "Suspension"),
            ("Reactivation", "Reactivation"),
            ("Transition", "Transition"),
        ],
        readonly=True,
    )
    action_plan = fields.Text(readonly=True)

    # Reactivation
    ##############
    fcp_improvement_desc = fields.Text(readonly=True)

    # Suspension
    ############
    suspension_end_date = fields.Date(readonly=True)
    suspension_detail = fields.Char(readonly=True)
    suspension_reason_ids = fields.Many2many(
        "fcp.lifecycle.reason", string="Suspension reason", readonly=True
    )
    # Adding a computed field to calculate days since suspension
    days_since_suspension = fields.Integer(
        string="Days Since Suspension",
        compute="_compute_days_since_suspension",
        store=True,
    )

    hold_cdsp_funds = fields.Boolean(readonly=True)
    hold_csp_funds = fields.Boolean(readonly=True)
    hold_gifts = fields.Boolean(readonly=True)
    hold_s2b_letters = fields.Boolean(readonly=True)
    hold_b2s_letters = fields.Boolean(readonly=True)
    hold_child_updates = fields.Boolean(readonly=True)
    is_beneficiary_information_updates_withheld = fields.Boolean(readonly=True)

    extension_1 = fields.Boolean(
        help="Suspension is extended by 30 days", readonly=True
    )
    extension_1_reason_ids = fields.Many2many(
        "fcp.suspension.extension.reason",
        relation="compassion_project_ile_sus_extension1_rel",
        readonly=True,
    )
    extension_2 = fields.Boolean(
        help="Suspension is extended by additional 30 days (60 in total)",
        readonly=True,
    )
    extension_2_reason_ids = fields.Many2many(
        "fcp.suspension.extension.reason", readonly=True
    )

    # Transition
    ############
    transition_complete = fields.Boolean(readonly=True)
    details = fields.Text(readonly=True)
    transition_reason_ids = fields.Many2many(
        "fcp.lifecycle.reason",
        string="Transition reason",
        readonly=True,
        relation="compassion_project_ile_transition_reason_rel",
    )
    projected_transition_date = fields.Date(readonly=True)
    future_involvement_ids = fields.Many2many(
        "fcp.involvement", string="Future involvement", readonly=True
    )

    name = fields.Char(readonly=True, index=True, required=True)
    project_status = fields.Selection("_get_project_status")

    gender = fields.Char(size=1, default="M")

    _sql_constraints = [
        ("unique_name", "unique(name)", "Lifecycle event already exists")
    ]

    @api.model
    def _get_project_status(self):
        return [
            ("Active", _("Active")),
            ("Phase Out", _("Phase Out")),
            ("Suspended", _("Suspended")),
            ("Transitioned", _("Transitioned")),
        ]

    @api.model
    def create(self, vals):
        """Call suspension and reactivation process on projects."""
        project = self.env["compassion.project"].browse(vals.get("project_id"))
        fund_suspended = project.suspension == "fund-suspended"
        hold_gifts = project.hold_gifts
        hold_letters = project.hold_s2b_letters
        lifecycle = self.search([("name", "=", vals["name"])])
        if lifecycle:
            lifecycle.write(vals)
        else:
            lifecycle = super().create(vals)
        if lifecycle.type == "Suspension":
            if lifecycle.hold_cdsp_funds and not fund_suspended:
                project.with_delay().suspend_funds()
            if lifecycle.hold_gifts and not hold_gifts:
                project.hold_gifts_action()
            if lifecycle.hold_s2b_letters and not hold_letters:
                project.with_delay().hold_letters_action()
        if lifecycle.type == "Reactivation":
            if fund_suspended:
                project.with_delay().reactivate_project()
            if hold_gifts and not lifecycle.hold_gifts:
                project.with_delay().reactivate_gifts()
            if hold_letters and not lifecycle.hold_s2b_letters:
                project.with_delay().reactivate_letters()
        return lifecycle

    @api.model
    def process_commkit(self, commkit_data):
        lifecycle_ids = list()
        for single_data in commkit_data.get("ICPLifecycleEventList", [commkit_data]):
            project = self.env["compassion.project"].search(
                [("fcp_id", "=", single_data["ICP_ID"])]
            )
            if not project:
                project.create({"fcp_id": single_data["ICP_ID"]})
            vals = self.json_to_data(single_data)
            lifecycle = self.create(vals)
            lifecycle_ids.append(lifecycle.id)
            lifecycle.project_id.last_update_date = fields.Date.today()
        return lifecycle_ids

    def data_to_json(self, mapped_name=None):
        odoo_data = super().data_to_json(mapped_name)
        status = odoo_data.get("project_status")
        if status:
            status_mapping = {
                "Active": "A",
                "Phase Out": "P",
                "Suspended": "S",
                "Transitioned": "T",
            }
            odoo_data["project_status"] = status_mapping[status]
        return odoo_data

    @api.depends('suspension_end_date', 'type')
    def _compute_days_since_suspension(self):
        for record in self:
            if record.type == 'Suspension' and record.suspension_end_date:
                record.days_since_suspension = (record.date - record.suspension_end_date).days
            else:
                record.days_since_suspension = 0
